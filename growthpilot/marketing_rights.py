"""Fresh email ownership verification for scoped consent export and erasure."""
import datetime as dt,hashlib,hmac,json,os,re,secrets
from pathlib import Path
from .core import Invalid,now

class MarketingRights:
    def __init__(self,service):self.m=service;self.s=service.s
    def request(self,brand,data,remote='unknown'):
        if set(data)!={'email'}:raise Invalid('Enter your email address')
        email=str(data.get('email','')).strip().lower()
        if len(email)>254 or not re.fullmatch(r'[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+',email):raise Invalid('Enter a valid email address')
        ident=self.m.identifier(brand,email)
        generic={'accepted':True,'message':'If a marketing record matches, a private export and deletion link will arrive by email. The link expires in 30 minutes.'}
        with self.s.db()as db:
            if self.m.limited(db,'rights-global',100,3600)or self.m.limited(db,'rights-ip:'+remote,20,3600)or self.m.limited(db,'rights-address:'+brand+':'+email,1,60):return generic
            record=next((r for r in self.s.rows(db,'marketing_subscriptions')if r['id']==ident and r.get('email')==email),None)
            if not record:return generic
            token=secrets.token_urlsafe(32);stamp=self.m.clock()
            self.s.save(db,'marketing_rights_tokens',{'id':ident,'brand':brand,'product_id':record['product_id'],'token_hash':hashlib.sha256(token.encode()).hexdigest(),'expires_at':(stamp+dt.timedelta(minutes=30)).isoformat()})
            self.s.audit(db,'marketing_rights_link_requested',ident,{'brand':brand},'subscriber')
        try:self.m.mailer(record,token,'rights');status='accepted'
        except Exception:status='not_confirmed'
        with self.s.db()as db:self.s.audit(db,'marketing_rights_delivery',ident,{'brand':brand,'status':status},'subscription_service')
        return generic
    def checked(self,db,brand,token):
        if not isinstance(token,str)or not 32<=len(token)<=100:raise Invalid('This private link is invalid or expired')
        hashed=hashlib.sha256(token.encode()).hexdigest()
        row=next((r for r in self.s.rows(db,'marketing_rights_tokens')if r['brand']==brand and hmac.compare_digest(r['token_hash'],hashed)),None)
        if not row or dt.datetime.fromisoformat(row['expires_at'])<=self.m.clock():raise Invalid('This private link is invalid or expired')
        record=self.s.get(db,'marketing_subscriptions',row['id'])
        if record.get('status')=='erased':raise Invalid('This marketing record was already erased')
        return record
    def export(self,brand,token):
        with self.s.db()as db:
            record=self.checked(db,brand,token)
            fields=['email','brand','status','source','notice_text','notice_version','requested_at','confirmed_at','withdrawn_at']
            events=[{k:r.get(k)for k in ('action','at','notice_version')}for r in self.s.rows(db,'marketing_consent_events')if r['consent_id']==record['id']]
            self.s.audit(db,'marketing_consent_exported',record['id'],{'brand':brand},'verified_subscriber')
            return {'export':{'generated_at':self.m.clock().isoformat(),'scope':'Marketing consent for this product only; account, purchase, provider and backup records are separate.','subscription':{k:record.get(k)for k in fields},'events':events,'retention':'Deletion removes the active email/contact. A keyed suppression marker and minimal audit are retained; existing backups and email-provider records have separate retention.'}}
    def marker_dir(self):
        return Path(self.s.path).parent/'marketing-erasure-markers'
    def write_marker(self,record):
        folder=self.marker_dir();folder.mkdir(mode=0o700,exist_ok=True)
        marker={'id':record['id'],'brand':record['brand'],'product_id':record['product_id'],'erased_at':self.m.clock().isoformat()}
        marker['signature']=self.m.sign('erasure:'+json.dumps(marker,sort_keys=True))
        target=folder/(record['id']+'.json');temporary=folder/(record['id']+'.tmp')
        with temporary.open('w')as stream:
            os.chmod(temporary,0o600);json.dump(marker,stream);stream.flush();os.fsync(stream.fileno())
        temporary.replace(target)
        if hasattr(os,'O_DIRECTORY'):
            descriptor=os.open(folder,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(descriptor)
            finally:os.close(descriptor)
        return marker
    def scrub(self,db,marker):
        ident=marker['id']
        record=next((r for r in self.s.rows(db,'marketing_subscriptions')if r['id']==ident),None)
        # A fresh explicit, email-confirmed subscription after erasure is a new choice.
        if record and record.get('requested_at','')>marker['erased_at']:return
        if record and record.get('status')=='erased':return
        self.s.save(db,'marketing_subscriptions',{'id':ident,'brand':marker['brand'],'product_id':marker['product_id'],'status':'erased','erased_at':marker['erased_at']})
        self.s.save(db,'marketing_erasure_suppressions',{'id':ident,'brand':marker['brand'],'product_id':marker['product_id'],'erased_at':marker['erased_at']})
        lead_ids=[]
        for lead in self.s.rows(db,'leads'):
            if lead.get('marketing_consent_id')==ident:
                lead_ids.append(lead['id'])
                self.s.save(db,'leads',{'id':lead['id'],'product_id':marker['product_id'],'marketing_brand':marker['brand'],'marketing_consent_id':ident,'consent':'opt_out','suppressed':True,'name':'Erased marketing contact','stage':'erased','erased_at':marker['erased_at']})
        actions=[]
        for action in self.s.rows(db,'actions'):
            if action.get('payload',{}).get('lead_id')in lead_ids:
                actions.append(action['id'])
                action.update(payload={'product_id':action['product_id'],'campaign_id':action['campaign_id'],'kind':'privacy_erased','lead_id':action['payload']['lead_id']},history=[],approval=None,receipt=None,status='privacy_erased',erased_at=marker['erased_at'])
                self.s.save(db,'actions',action)
        if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deliveries'").fetchone():
            for aid in actions:db.execute("UPDATE deliveries SET status='privacy_erased',result=NULL WHERE action_id=?",(aid,))
        db.execute("DELETE FROM records WHERE kind='marketing_rights_tokens' AND id=?",(ident,))
        self.s.audit(db,'marketing_contact_erased',ident,{'brand':marker['brand'],'retained':'keyed suppression and minimal audit','actions_redacted':len(actions)},'verified_subscriber')
    def erase(self,brand,token,confirmed):
        if confirmed is not True:raise Invalid('Explicitly confirm deletion of this product marketing record')
        with self.s.db()as db:
            record=self.checked(db,brand,token)
            marker=self.write_marker(record)
            self.scrub(db,marker)
        return {'erased':True,'message':'Your email and active marketing contact were removed for this product. A keyed suppression marker and minimal audit remain. This does not delete your account, provider records or existing backups, or recall email already in flight.'}
    def reconcile_erasure(self):
        folder=self.marker_dir()
        if not folder.exists():return
        with self.s.db()as db:
            for path in folder.glob('*.json'):
                marker=json.loads(path.read_text());signature=marker.pop('signature')
                if not hmac.compare_digest(signature,self.m.sign('erasure:'+json.dumps(marker,sort_keys=True))):raise Invalid('Erasure journal verification failed')
                self.scrub(db,marker)
