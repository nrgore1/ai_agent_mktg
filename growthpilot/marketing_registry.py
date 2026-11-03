"""Authenticated tenant context. Public Host headers cannot create tenant brands."""
import base64,hashlib,hmac,json,os,re,time
from .core import Invalid
from .marketing_consent import BRANDS,brand_for_host

class BrandRegistry:
    def __init__(self,store,secret=None):
        self.s=store;self.secret=secret if secret is not None else os.environ.get('GROWTHPILOT_TENANT_SECRET','')
    def all(self,db=None):
        if db is None:
            with self.s.db()as connection:return self.all(connection)
        brands={k:dict(v,operator='Atmakosh LLC',enabled=True)for k,v in BRANDS.items()}
        brands.update({r['id']:r for r in self.s.rows(db,'marketing_brands')})
        return brands
    def resolve(self,host,headers,method,path,body=b''):
        host=host.lower().split(':')[0]
        raw=headers.get('X-Marketing-Context','')
        if not raw:
            brand=brand_for_host(host)
            if brand=='jodiusa' and self.secret:raise Invalid('Verified tenant context required')
            return brand,self.all()[brand]
        if len(self.secret)<32 or len(raw)>12000:raise Invalid('Invalid tenant context')
        try:
            stamp=headers['X-Marketing-Time'];issued=float(stamp)
            if abs(time.time()-issued)>60:raise ValueError()
            expected=hmac.new(self.secret.encode(),('\n'.join([stamp,method,path,host,hashlib.sha256(body).hexdigest(),raw])).encode(),hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected,headers.get('X-Marketing-Signature','')):raise ValueError()
            data=json.loads(base64.urlsafe_b64decode(raw))
            required={'id','product_id','tenant_id','tenant_slug','name','host','aliases','operator','reply_to','privacy','topics','enabled','accepted_at','acceptance_version'}
            if set(data)!=required or data['product_id']!=6 or type(data['enabled'])is not bool:raise ValueError()
            if not re.fullmatch(r'[1-9][0-9]*',str(data['tenant_id'])):raise ValueError()
            if data['id']!='tenant-'+str(data['tenant_id']) and data['id']!='jodiusa':raise ValueError()
            if data['id']=='jodiusa' and data['tenant_slug']!='jodiusa':raise ValueError()
            hosts=[data['host']]+data['aliases']
            if not isinstance(data['aliases'],list) or len(hosts)>12 or host not in hosts:raise ValueError()
            for h in hosts:
                if not isinstance(h,str)or not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?',h)or '.'not in h:raise ValueError()
                if h in {'agentvire.com','weddingos.pro','www.weddingos.pro','memoirbookstudio.com','www.memoirbookstudio.com','jodibana.com','www.jodibana.com'}:raise ValueError()
                if data['id']!='jodiusa' and h in {'jodiusa.com','www.jodiusa.com'}:raise ValueError()
            for key,limit in [('name',120),('operator',160),('topics',300),('tenant_slug',80)]:
                if not isinstance(data[key],str)or not 1<=len(data[key])<=limit or any(ord(c)<32 for c in data[key]):raise ValueError()
            if not re.fullmatch(r'[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+',data['reply_to']):raise ValueError()
            if data['privacy']!='/privacy/':raise ValueError()
            if data['enabled'] and(not data['accepted_at']or data['acceptance_version']!='2026-10-30-v1'):raise ValueError()
        except (KeyError,ValueError,TypeError,UnicodeError):raise Invalid('Invalid tenant context')
        with self.s.db()as db:
            all_brands=self.all(db)
            for slug,b in all_brands.items():
                if slug!=data['id'] and set(hosts)&set([b['host']]+b.get('aliases',[])):raise Invalid('Domain belongs to another consent scope')
            old=all_brands.get(data['id'],{})
            if issued<old.get('context_time',0):
                return data['id'],old
            if any(old.get(k)!=v for k,v in data.items()):
                data['context_time']=issued
                self.s.save(db,'marketing_brands',data)
                self.s.audit(db,'tenant_marketing_configuration',data['id'],{'enabled':data['enabled'],'acceptance_version':data['acceptance_version']},'authenticated_jodibana_proxy')
            else:data=old
        return data['id'],data
