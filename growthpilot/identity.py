"""Local identities, expiring sessions, CSRF and bounded authentication attempts."""
import datetime as dt
import hashlib
import hmac
import json
import os
import secrets
from .core import Invalid, now

def password_hash(password,salt):
 return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()

class Identity:
 def __init__(self,store):
  self.store=store
  with store.db() as db:
   db.executescript("""CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,password TEXT,salt TEXT,role TEXT,products TEXT,enabled INTEGER);
   CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY,user_id TEXT,csrf TEXT,expires TEXT);
   CREATE TABLE IF NOT EXISTS auth_limits(key TEXT PRIMARY KEY,attempts INTEGER,until TEXT);""")
 def create(self,username,password,role='operator',products=None):
  if role not in ('founder','admin','operator','viewer'): raise Invalid('Invalid role')
  if len(password)<14 or not username.strip() or len(username)>80: raise Invalid('Username and password of at least 14 characters required')
  products=products or []
  if not isinstance(products,list) or any(type(p) is not int for p in products): raise Invalid('Product IDs must be integers')
  salt=secrets.token_hex(16); value=password_hash(password,salt)
  with self.store.db() as db:
   if db.execute('SELECT 1 FROM users WHERE id=?',(username,)).fetchone(): raise Invalid('User already exists')
   db.execute('INSERT INTO users VALUES(?,?,?,?,?,1)',(username,value,salt,role,json.dumps(products)))
   self.store.audit(db,'user_created',username,{'role':role,'products':products})
  return {'username':username,'role':role,'products':products}
 def bootstrap(self,directory):
  with self.store.db() as db:
   exists=db.execute('SELECT 1 FROM users LIMIT 1').fetchone()
  if not exists:
   password=secrets.token_urlsafe(24)
   # Credentials never go to stdout, audit, or API responses.
   path=directory/'initial-login.txt'
   fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
   with os.fdopen(fd,'w') as f:f.write('Username: founder\nPassword: '+password+'\n')
   self.create('founder',password,'founder')
 def login(self,username,password,ip):
  key=hashlib.sha256(ip.encode()).hexdigest(); current=dt.datetime.now(dt.timezone.utc)
  with self.store.db() as db:
   limit=db.execute('SELECT attempts,until FROM auth_limits WHERE key=?',(key,)).fetchone()
   if limit and limit['attempts']>=8 and dt.datetime.fromisoformat(limit['until'])>current: raise Invalid('Too many login attempts; retry in 15 minutes')
   user=db.execute('SELECT * FROM users WHERE id=?',(username,)).fetchone()
   salt=user['salt'] if user else '00'*16
   valid=hmac.compare_digest(password_hash(password,salt),user['password'] if user else '00'*64)
   if not user or not valid or not user['enabled']:
    attempts=(limit['attempts'] if limit and dt.datetime.fromisoformat(limit['until'])>current else 0)+1
    db.execute('INSERT OR REPLACE INTO auth_limits VALUES(?,?,?)',(key,attempts,(current+dt.timedelta(minutes=15)).isoformat()))
    # Commit the limit even though the API will return a failed login.
    return None
   db.execute('DELETE FROM auth_limits WHERE key=?',(key,))
   raw=secrets.token_urlsafe(40); csrf=secrets.token_urlsafe(24)
   db.execute('DELETE FROM sessions WHERE expires<?',(now(),))
   db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(raw.encode()).hexdigest(),username,csrf,(current+dt.timedelta(hours=8)).isoformat()))
   self.store.audit(db,'login',username,{},username)
   return {'session':raw,'csrf':csrf,'username':username,'role':user['role'],'products':json.loads(user['products'])}
 def session(self,raw):
  with self.store.db() as db:
   row=db.execute('SELECT u.id,u.role,u.products,s.csrf,s.expires FROM sessions s JOIN users u ON s.user_id=u.id WHERE s.hash=? AND u.enabled=1',(hashlib.sha256(raw.encode()).hexdigest(),)).fetchone()
   if not row or dt.datetime.fromisoformat(row['expires'])<=dt.datetime.now(dt.timezone.utc): return None
   return {'username':row['id'],'role':row['role'],'products':json.loads(row['products']),'csrf':row['csrf']}
 def logout(self,raw):
  with self.store.db() as db:db.execute('DELETE FROM sessions WHERE hash=?',(hashlib.sha256(raw.encode()).hexdigest(),))
 def change_password(self,user,old,new):
  if len(new)<14:raise Invalid('Password must contain at least 14 characters')
  with self.store.db() as db:
   row=db.execute('SELECT * FROM users WHERE id=?',(user,)).fetchone()
   if not row or not hmac.compare_digest(password_hash(old,row['salt']),row['password']):raise Invalid('Current password incorrect')
   salt=secrets.token_hex(16)
   db.execute('UPDATE users SET password=?,salt=? WHERE id=?',(password_hash(new,salt),salt,user))
   db.execute('DELETE FROM sessions WHERE user_id=?',(user,));self.store.audit(db,'password_changed',user,{},user)
 def users(self):
  with self.store.db() as db:return [dict(username=r['id'],role=r['role'],products=json.loads(r['products']),enabled=bool(r['enabled'])) for r in db.execute('SELECT * FROM users')]
