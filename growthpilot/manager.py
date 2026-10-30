"""Portfolio marketing operations. Preparation is automatic; external actions stay gated."""
import datetime as dt,json,uuid
from pathlib import Path
from urllib.parse import urlsplit,urlencode,urlunsplit,parse_qsl
from zoneinfo import ZoneInfo
from .core import Invalid,digest,now
from . import postmark

ACTIVITIES=[('launch','Review and launch priority campaigns','31–35',4),('activate','Acquire and activate trial users','31–45',14),('demo','Run institutional demonstrations','31–50',19),('feedback','Collect customer feedback','36–55',24),('measure','Measure channel performance','40–60',29),('iterate','Iterate on launch experiments','51–60',29)]
def stable(value):return uuid.uuid5(uuid.NAMESPACE_URL,'agentvire:'+value).hex
def tracked(url,source,campaign):
 if not url:return None
 parts=urlsplit(url);query=dict(parse_qsl(parts.query));query.update(utm_source=source,utm_medium='community',utm_campaign=campaign)
 return urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(query),parts.fragment))
def rules(channel):
 if channel=='producthunt.com':return 'Launch description, 3–5 real screenshots, a working demo and a genuine founder comment. Never ask for upvotes. Founder account required.'
 if channel=='reddit.com':return 'Choose a relevant subreddit, read its specific rules and disclose the founder relationship. Ask permission where required. No unsolicited DMs or bulk promotion.'
 if channel=='news.ycombinator.com':return 'Founder must write the final submission personally. Show HN needs a working product people can try; do not submit a waitlist or generated text.'
 if channel=='github.com':return 'Use an owned project README, release or permitted discussion. Do not advertise through unrelated repositories or create promotional issues in others’ projects.'
 if channel in ('g2.com','capterra.com','getapp.com'):return 'Verify product category and listing eligibility. Use genuine customer reviews only, without invented proof or manipulated incentives.'
 return 'Verify current submission rules, product eligibility, account permissions and any fee before submitting. No paid placement without a separate approved spending action.'

class Manager:
 def __init__(self,store):self.s=store;self.profiles=json.loads(Path(__file__).with_name('launch_profiles.json').read_text())
 def prepare(self,actor='founder'):
  today=dt.datetime.now(ZoneInfo('America/New_York')).date()
  with self.s.db() as db:
   if self.s.paused(db):raise Invalid('System paused')
   existing=self.s.rows(db,'programs');program=existing[0] if existing else {'id':'launch-learn','started_at':now(),'launch_day_31':today.isoformat(),'timezone':'America/New_York','enabled':True,'owner':'founder','effort_allocation':{'priority':70,'technical':20,'discovery':10}}
   self.s.save(db,'programs',program);base=dt.date.fromisoformat(program['launch_day_31'])
   products=self.s.rows(db,'products');channels={c['domain']:c for c in self.s.rows(db,'channels')}
   for p in products:
    pid=p['id'];profile=self.profiles[str(pid)];cid=stable('launch-campaign:'+str(pid));sender='naren@vireoka.com' if pid in (1,2) else 'naren@atmakosh.com'
    existing_campaign=db.execute("SELECT 1 FROM records WHERE kind='campaigns' AND id=?",(cid,)).fetchone()
    if not existing_campaign:
     campaign={'id':cid,'product_id':pid,'name':p['name']+' · Launch & Learn','program_id':program['id'],'status':'prepared','created_at':now(),'owner':'founder','budget_cents':0,'targets':p['targets'],'hypothesis':profile['angle'],'audience':profile['segment'],'offer':profile['offer'],'sender':sender,'utm':{'utm_source':p['channels'][0],'utm_medium':'community','utm_campaign':cid},'confidence':'requires_product_and_channel_review'};self.s.save(db,'campaigns',campaign)
    planid=stable('growthplan:'+str(pid))
    if not db.execute("SELECT 1 FROM records WHERE kind='growthplans' AND id=?",(planid,)).fetchone():
     plan={'id':planid,'product_id':pid,'campaign_id':cid,'priority':p['priority'],'audience':profile['segment'],'positioning_hypothesis':profile['angle'],'offer':profile['offer'],'sender':sender,'activation':{'event':profile['activation'],'steps':profile['steps'],'followup_sequence':[{'timing':'After explicit opt-in','purpose':'Welcome, confirm goal and provide one next action'},{'timing':'After first meaningful use','purpose':'Ask what helped and what blocked progress'},{'timing':'After feedback or inactivity','purpose':'Offer an optional founder walkthrough; no automatic pressure or invented urgency'}]},'qualification_questions':['What job are you trying to complete?','How do you solve it today?','Who will use and approve a change?','What outcome would make an evaluation worthwhile?'],'demo':{'agenda':profile['demo'],'required_inputs':['Named interested participant','Consent or requested meeting','Confirmed product walkthrough','Synthetic or authorized demo data'],'pilot_proposal':['Customer problem and scope','Explicit evaluation success criteria','Owners, dates and support boundaries','Data handling and approval responsibilities','Commercial terms proposed separately for approval']},'feedback_questions':[profile['question'],'What was the first moment you understood the value?','Where did you get stuck or stop?','What alternative would you use?','Would you use this again, and why?'],'measurement':{'events':['landing_view','signup','trial',profile['activation'],'demo','pilot_proposal','paid','feedback'],'attribution':['product_id','campaign_id','utm_source','utm_medium','utm_campaign'],'reporting':'Actual records only; targets are planning hypotheses'},'review_rules':['Check instrumentation before judging channel performance','Do not scale from small samples','After 100 attributable landing views with zero activations, investigate message/onboarding fit before more distribution','Only propose a spend or offer change; founder approval is required'],'created_at':now()};self.s.save(db,'growthplans',plan)
    count=3 if p['priority']==1 else 2
    for channel in p['channels'][:count]:
     aid=stable('launch-action:'+str(pid)+':'+channel)
     if db.execute("SELECT 1 FROM records WHERE kind='actions' AND id=?",(aid,)).fetchone():continue
     cta=tracked(p.get('landing_page') or p.get('website'),channel,cid)
     topic=profile['angle'];body=f"{p['name']} — {topic}\n\nFor {profile['segment'].lower()}.\n\nWe’re looking to understand your current workflow and whether a focused evaluation would be useful. {profile['offer']}.\n\nWhat we’d like to learn: {profile['question']}\n\n"+(('Review the product and request an evaluation: '+cta) if cta else 'A product destination must be verified before this draft can be submitted.')
     if channel=='reddit.com':body=f"Founder disclosure: I’m working on {p['name']}.\n\n{profile['question']}\n\nI’d value examples of your current workflow, including tools and workarounds. If this community permits product feedback requests, I can share a focused evaluation for interested people. No unsolicited messages.\n\n"+(cta or 'Product link pending verification.')
     if channel=='news.ycombinator.com':body='FOUNDER BRIEF — DO NOT SUBMIT GENERATED TEXT\n\n'+body+'\n\nThe founder must personally write the final Show HN or discussion submission after verifying a working try-it-yourself experience.'
     payload={'product_id':pid,'campaign_id':cid,'kind':'manual_launch','connector':'manual','channel':channel,'destination':channels[channel]['url'],'sender':sender,'account':'founder account — confirm before submission','recipient':None,'title':p['name']+' · '+topic,'content':body,'claims':[],'evidence':[{'source':'user-supplied portfolio strategy','note':'Positioning is a hypothesis pending founder verification'}],'cost_cents':0,'cta':cta,'requirements':rules(channel),'attestations':{'product_facts':False,'channel_rules':False,'destination':False,'founder_written':False}}
     action={'id':aid,'product_id':pid,'campaign_id':cid,'payload':payload,'payload_hash':digest(payload),'version':1,'status':'pending','approval':None,'receipt':None,'created_at':now(),'program_id':program['id']};self.s.save(db,'actions',action)
    for key,title,days,offset in ACTIVITIES:
     tid=stable('workitem:'+str(pid)+':'+key)
     if db.execute("SELECT 1 FROM records WHERE kind='workitems' AND id=?",(tid,)).fetchone():continue
     item={'id':tid,'product_id':pid,'campaign_id':cid,'activity':key,'title':title,'days':days,'due_date':(base+dt.timedelta(days=offset)).isoformat(),'owner':'marketing_manager','status':'prepared' if key in ('launch','activate','demo','feedback') else 'awaiting_data','created_at':now()};self.s.save(db,'workitems',item)
    expid=stable('experiment:'+str(pid))
    if not db.execute("SELECT 1 FROM records WHERE kind='experiments' AND id=?",(expid,)).fetchone():self.s.save(db,'experiments',{'id':expid,'product_id':pid,'campaign_id':cid,'name':p['name']+' · first-value experiment','hypothesis':profile['angle'],'metric':profile['activation'],'target':5 if p['priority']==1 else 2,'budget_cents':0,'status':'planned','decision':'pending','created_at':now(),'program_id':program['id']})
   self.s.audit(db,'launch_program_prepared',program['id'],{'products':len(products),'external_actions':0},actor)
  self.review(actor)
  return self.summary()
 def blockers(self,db,a):
  p=self.s.get(db,'products',a['product_id']);payload=a['payload'];out=[]
  if not (p.get('landing_page') or p.get('website')):out.append('Verify product destination')
  if p.get('readiness')!='verified':out.append('Confirm product launch readiness')
  if not payload.get('attestations',{}).get('product_facts'):out.append('Review product facts and copy')
  if not payload.get('attestations',{}).get('channel_rules'):out.append('Review exact platform/community rules')
  if not payload.get('attestations',{}).get('destination'):out.append('Confirm destination and founder account')
  if payload.get('connector')=='manual' and 'confirm before submission' in payload.get('account','').lower():out.append('Enter the actual publishing account')
  if payload.get('channel')=='news.ycombinator.com' and not payload.get('attestations',{}).get('founder_written'):out.append('Founder must personally write final HN text')
  if payload.get('connector')=='postmark':
   account=postmark.configured(p['id'])
   if account.get('status')!='configured':out.append('Configure Postmark credential and broadcast stream')
  return out
 def summary(self,product=None):
  with self.s.db() as db:
   result={k:self.s.rows(db,k,product) for k in ('growthplans','workitems','feedback','demos','reviews','campaigns')};program=self.s.rows(db,'programs');result['program']=program[0] if program else None
   actions=[a for a in self.s.rows(db,'actions',product) if a.get('program_id')=='launch-learn'];result['actions']=[dict(a,blockers=self.blockers(db,a)) for a in actions]
   result['growthplans'].sort(key=lambda p:(p['priority'],p['product_id']))
   priorities={p['id']:p['priority'] for p in self.s.rows(db,'products')}
   result['actions'].sort(key=lambda a:(priorities[a['product_id']],a['product_id'],a['payload']['channel']))
   result['postmark']=postmark.public_accounts()
  return result
 def review(self,actor='marketing_manager'):
  current=dt.datetime.now(ZoneInfo('America/New_York'));today=current.date().isoformat();reviewid='review-'+today
  with self.s.db() as db:
   if self.s.paused(db):raise Invalid('System paused')
   products=self.s.rows(db,'products');actions=self.s.rows(db,'actions');workitems=self.s.rows(db,'workitems');experiments=self.s.rows(db,'experiments');events=[e for e in self.s.rows(db,'events') if e.get('source')=='actual'];feedback=self.s.rows(db,'feedback');demos=self.s.rows(db,'demos');results=[]
   for p in products:
    pe=[e for e in events if e['product_id']==p['id']];funnel={}
    for e in pe:funnel[e['type']]=funnel.get(e['type'],0)+e.get('count',0)
    profile=self.profiles[str(p['id'])];activation=funnel.get(profile['activation'],0);views=funnel.get('landing_view',0)
    decision='Instrument and collect real traffic before judging channel performance' if not pe else 'Investigate the landing message, event tracking and first-value flow' if views>=100 and not activation else 'Continue collecting evidence; compare activated users by source before scaling'
    bysource={}
    for e in pe:
     source=e.get('utm_source','unattributed');bucket=bysource.setdefault(source,{'views':0,'activated':0,'paid':0,'cost_cents':0});bucket['views']+=e.get('count',0) if e['type']=='landing_view' else 0;bucket['activated']+=e.get('count',0) if e['type']==profile['activation'] else 0;bucket['paid']+=e.get('count',0) if e['type']=='paid' else 0;bucket['cost_cents']+=e.get('cost_cents',0)
    published=sum(a['product_id']==p['id'] and a['payload'].get('kind')=='manual_launch' and a['status']=='submitted' for a in actions)
    fcount=sum(f['product_id']==p['id'] for f in feedback);dcount=sum(d['product_id']==p['id'] and d.get('status')=='completed' for d in demos)
    observed={'launch':published,'activate':activation,'demo':dcount,'feedback':fcount,'measure':len(pe),'iterate':sum(e['product_id']==p['id'] and e.get('status')=='completed' and e.get('decision') in ('continue','stop','iterate') and bool(e.get('result')) for e in experiments)}
    goals={'launch':3 if p['priority']==1 else 2,'activate':p.get('targets',{}).get('activated',p.get('targets',{}).get('testers',1)),'demo':p.get('targets',{}).get('demos',1),'feedback':p.get('targets',{}).get('interviews',10),'measure':1,'iterate':1}
    for item in [w for w in workitems if w['product_id']==p['id']]:
     item.update(observed=observed[item['activity']],target=goals[item['activity']],updated_at=now())
     item['status']='completed' if item['observed']>=item['target'] else 'in_progress' if item['observed'] else 'awaiting_approval' if item['activity']=='launch' else 'awaiting_real_participants' if item['activity'] in ('activate','demo','feedback') else 'awaiting_data'
     self.s.save(db,'workitems',item)
    results.append({'product_id':p['id'],'funnel':funnel,'by_source':bysource,'decision':decision,'status':'needs_data' if not pe else 'review_ready','feedback_count':sum(f['product_id']==p['id'] for f in feedback),'completed_demos':sum(d['product_id']==p['id'] and d.get('status')=='completed' for d in demos)})
   row={'id':reviewid,'created_at':now(),'timezone':'America/New_York','review_type':'weekly' if current.weekday()==4 else 'daily','products':results,'external_changes':0,'note':'Recommendations only; campaign changes require founder approval'};self.s.save(db,'reviews',row)
   programs=self.s.rows(db,'programs')
   if programs:
    program=programs[0];program['last_review_date']=today;program['next_review_date']=(current.date()+dt.timedelta(days=1)).isoformat();program['weekly_review_day']='Friday';self.s.save(db,'programs',program)
   self.s.audit(db,'manager_review',reviewid,{'products':len(results)},actor)
  return row
 def tick(self):
  with self.s.db() as db:
   programs=self.s.rows(db,'programs')
   if not programs or not programs[0].get('enabled') or self.s.paused(db):return
   today=dt.datetime.now(ZoneInfo('America/New_York')).date().isoformat()
   if programs[0].get('last_review_date')==today:return
  self.review()
 def activity_record(self,kind,data,actor):
  if kind not in ('feedback','demos'):raise Invalid('Unsupported activity record')
  with self.s.db() as db:
   p=self.s.get(db,'products',data.get('product_id'))
   if kind=='feedback' and (not data.get('notes') or not data.get('source')):raise Invalid('Actual feedback notes and source required')
   if kind=='demos' and data.get('status') not in ('proposed','scheduled','completed','cancelled'):raise Invalid('Demo status required')
   if kind=='demos' and data.get('status')=='completed' and (not data.get('notes') or not data.get('source')):raise Invalid('Completed demos need actual outcome notes and evidence source')
   if data.get('lead_id') and self.s.get(db,'leads',data['lead_id'])['product_id']!=p['id']:raise Invalid('Lead belongs to another product')
   row={k:v for k,v in data.items() if k in ('product_id','lead_id','status','notes','source','objection','next_step','scheduled_at','consent')};row.update(id=uuid.uuid4().hex,created_at=now(),recorded_by=actor);self.s.save(db,kind,row);self.s.audit(db,'record_'+kind,row['id'],{'product_id':p['id']},actor);return row

 def validate_action(self,db,a):
  errors=self.blockers(db,a)
  if errors:raise Invalid('; '.join(errors))
  payload=a['payload'];p=self.s.get(db,'products',a['product_id'])
  if payload.get('product_id')!=a['product_id'] or payload.get('campaign_id')!=a['campaign_id']:raise Invalid('Product/campaign mismatch')
  if self.s.get(db,'campaigns',a['campaign_id'])['product_id']!=a['product_id']:raise Invalid('Campaign belongs to another product')
  if 'A product destination must be verified before this draft can be submitted.' in payload.get('content',''):raise Invalid('Replace the draft destination placeholder with reviewed final copy')
  if payload.get('cost_cents')!=0:raise Invalid('Paid actions need a separate spending workflow')
  if payload.get('sender')!=('naren@vireoka.com' if p['id'] in (1,2) else 'naren@atmakosh.com'):raise Invalid('Sender does not match product')
  if not payload.get('content','').strip() or not payload.get('account','').strip():raise Invalid('Exact content and account required')
  if any(c not in p.get('approved_claims',[]) for c in payload.get('claims',[])):raise Invalid('Unsupported product claim')
  if payload['connector']=='manual':
   host=(urlsplit(payload.get('destination','')).hostname or '').removeprefix('www.')
   if host!=payload.get('channel') or not payload['destination'].startswith('https://'):raise Invalid('Exact destination must belong to selected channel')
   if payload['channel']=='reddit.com' and not urlsplit(payload['destination']).path.startswith('/r/'):raise Invalid('Choose and review an exact subreddit destination')
   if payload['channel']=='news.ycombinator.com' and payload['content'].startswith('FOUNDER BRIEF'):raise Invalid('Replace the generated brief with founder-written text')
  elif payload['connector']=='postmark':
   lead=self.s.get(db,'leads',payload.get('lead_id'))
   if lead['product_id']!=p['id'] or lead.get('email')!=payload.get('recipient') or lead.get('consent')!='opt_in' or not lead.get('source'):raise Invalid('Product-specific opt-in lead, consent source and exact recipient required')
   from .marketing_consent import MarketingConsent
   MarketingConsent(self.s).validate_lead(db,lead,payload)
   if lead.get('suppressed') or any(x['email'].lower()==payload['recipient'].lower() for x in self.s.rows(db,'suppressions')):raise Invalid('Recipient suppressed')
   postmark.envelope(payload,a['id'])
  else:raise Invalid('Unsupported manager connector')
 def transition(self,id,command,data,actor='founder'):
  import copy
  current=dt.datetime.now(dt.timezone.utc)
  if command=='execute':
   with self.s.db() as db:a=self.s.get(db,'actions',id)
   return self.s.enqueue(id) if a['payload']['connector']=='postmark' else self.transition(id,'export',{},actor)
  with self.s.db() as db:
   a=self.s.get(db,'actions',id)
   if command=='revise':
    if a['status'] in ('executed','submitted','queued','executing','unknown'):raise Invalid('Submitted or queued actions cannot be revised')
    allowed={'content','title','account','destination','attestations','claims','evidence'}
    if set(data)-allowed:raise Invalid('Unsupported launch edit')
    if 'attestations' in data and (not isinstance(data['attestations'],dict) or set(data['attestations'])-{'product_facts','channel_rules','destination','founder_written'} or any(type(v) is not bool for v in data['attestations'].values())):raise Invalid('Review attestations must be explicit booleans')
    a.setdefault('history',[]).append({'version':a['version'],'payload':copy.deepcopy(a['payload']),'hash':a['payload_hash']})
    a['payload'].update(data)
    if 'content' in data and 'attestations' not in data:a['payload'].setdefault('attestations',{}).update(product_facts=False,founder_written=False)
    a.update(version=a['version']+1,payload_hash=digest(a['payload']),approval=None,status='pending')
   elif command=='approve':
    if self.s.paused(db):raise Invalid('System paused')
    if a['status']!='pending' or data.get('payload_hash')!=a['payload_hash']:raise Invalid('Only the current pending payload can be approved')
    self.validate_action(db,a);a.update(status='approved',approval={'hash':a['payload_hash'],'version':a['version'],'actor':actor,'expires_at':(current+dt.timedelta(hours=24)).isoformat()})
   elif command=='reject':
    if a['status'] in ('executed','submitted','queued','executing','unknown'):raise Invalid('Cannot reject an in-flight or completed action')
    a.update(status='rejected',approval=None)
   elif command in ('export','record_submission'):
    self.validate_action(db,a)
    approval=a.get('approval')
    if self.s.paused(db) or a['status']!='approved' or not approval or approval['hash']!=digest(a['payload']) or approval['version']!=a['version'] or dt.datetime.fromisoformat(approval['expires_at'])<=current:raise Invalid('Current, unexpired founder approval required')
    if a['payload']['connector']!='manual':raise Invalid('Manual package required')
    if command=='export':return {'package':a['payload'],'payload_hash':a['payload_hash'],'version':a['version'],'delivery':'manual; not submitted by export'}
    url=data.get('receipt_url','');host=(urlsplit(url).hostname or '').removeprefix('www.')
    if not url.startswith('https://') or host!=a['payload']['channel'] or not data.get('note'):raise Invalid('Submission URL on the approved channel and a receipt note required')
    a.update(status='submitted',receipt={'at':now(),'url':url,'note':str(data['note'])[:2000],'payload_hash':a['payload_hash'],'verification':'founder_reported','external_delivery':'reported_by_founder'})
   else:raise Invalid('Unknown launch action command')
   self.s.save(db,'actions',a);self.s.audit(db,'launch_'+command,id,{'hash':a['payload_hash'],'version':a['version']},actor);return a
 def outreach(self,lead_id,actor):
  with self.s.db() as db:
   lead=self.s.get(db,'leads',lead_id);p=self.s.get(db,'products',lead['product_id']);profile=self.profiles[str(p['id'])]
   if not lead.get('email') or lead.get('consent')!='opt_in' or not lead.get('source'):raise Invalid('Add a real opt-in lead with a consent source before drafting email')
   account=postmark.configured(p['id']);cid=stable('launch-campaign:'+str(p['id']));self.s.get(db,'campaigns',cid);sender='naren@vireoka.com' if p['id'] in (1,2) else 'naren@atmakosh.com';aid=uuid.uuid4().hex
   content=f"Hi {lead['name']},\n\nThanks for opting in to information about {p['name']}. {profile['offer']}.\n\nA useful first step: {profile['steps'][0]}.\n\n{profile['question']}\n\nIf you’d like a walkthrough, reply with the workflow you want to evaluate and a suitable time.\n\nNarendra Gore\n{sender}\n\nTo stop these marketing updates: {{{{DOUBLE_PLACEHOLDER}}}}"
   content=content.replace('{{DOUBLE_PLACEHOLDER}}','{{{ pm:unsubscribe }}}')
   payload={'product_id':p['id'],'campaign_id':cid,'connector':'postmark','server_id':account.get('server_id'),'message_stream':account.get('stream'),'kind':'outreach','channel':'postmark','destination':lead['email'],'sender':sender,'account':postmark.account_key(p['id']),'recipient':lead['email'],'lead_id':lead['id'],'title':p['name']+' — your next evaluation step','content':content,'claims':[],'evidence':[{'source':lead['source'],'note':'Lead consent and interest source; product claims still require founder review'}],'cost_cents':0,'usage_note':'Postmark usage is billed under the existing account; no new purchase or ad spend is authorized. Actual costs are reported separately.','attestations':{'product_facts':False,'channel_rules':False,'destination':False,'founder_written':False}}
   if lead.get('marketing_consent_id'):
    from .marketing_consent import MarketingConsent, BRANDS, PREFIX
    service=MarketingConsent(self.s);brand=BRANDS[lead['marketing_brand']]
    payload['marketing_brand']=lead['marketing_brand'];service.validate_lead(db,lead,payload)
    record=self.s.get(db,'marketing_subscriptions',lead['marketing_consent_id'])
    payload['title']=brand['name']+' — updates you requested'
    payload['content']='Thanks for choosing '+brand['name']+' email updates.\n\nFounder draft: add a verified update about '+brand['topics']+'.\n\nVisit https://'+brand['host']+'/\n\nQuestions: '+brand['reply_to']+'\n\nStop these product updates: https://'+brand['host']+PREFIX+'withdraw#'+service.withdrawal_token(record)+'\n\n{{{ pm:unsubscribe }}}'
   a={'id':aid,'product_id':p['id'],'campaign_id':cid,'payload':payload,'payload_hash':digest(payload),'version':1,'status':'pending','approval':None,'receipt':None,'created_at':now(),'program_id':'launch-learn'};self.s.save(db,'actions',a);self.s.audit(db,'outreach_prepared',aid,{'lead_id':lead_id},actor);return a
