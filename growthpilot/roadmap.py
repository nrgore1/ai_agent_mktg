"""Founder-managed planning milestones, separate from verified commercial outcomes."""
from .core import Invalid,now

PHASES=[
 {'id':'foundation','name':'Build the Foundation','days':'1–30','activities':[
 ('readiness','1–5','Audit all 17 products','Review stability, onboarding, pricing, checkout, privacy, security, support and demos.'),
 ('ownership','1–5','Assign product owners and priorities','Focus launch effort on LiqMint Individual, LiqMint Institutional, OraToPlus and WeddingOS.'),
 ('customers','6–10','Define ideal customers','Document customer needs, buyer roles and audience segments for each product.'),
 ('positioning','6–10','Prepare positioning and offers','Write product briefs, competitive alternatives, value propositions and proposed commercial offers.'),
 ('claims','6–10','Review claims and evidence','List supported claims, required evidence and approval requirements.'),
 ('landing','11–15','Prepare landing pages and demonstrations','Prepare product-specific landing pages, screenshots, demo videos and conversion calls to action.'),
 ('tracking','11–15','Set up analytics and CRM','Define activation events, trial/subscription funnels, UTM conventions and lead pipelines.'),
 ('packages','16–20','Prepare launch packages','Draft product profiles, directory submissions, launch copy, FAQs and founder introductions.'),
 ('communities','16–20','Plan community participation','Identify relevant communities and review each channel’s current rules before submitting.'),
 ('investors','21–25','Prepare investor materials','Prepare LiqMint and Atmasphere pitch materials, traction framework and data-room checklist.'),
 ('partners','21–25','Build investor and partner shortlists','Identify investor fit, strategic partners, referral opportunities and potential champions.'),
 ('interviews','26–30','Conduct initial customer discovery','Capture customer interview notes, needs, objections and willingness-to-pay signals.'),
 ('beta','26–30','Run controlled beta preparation','Organize early product evaluations, onboarding feedback and demonstration follow-ups.'),
 ('baseline','26–30','Review baseline and launch plan','Review initial learning, set launch experiments and agree on the Days 31–60 priorities.') ]},
 {'id':'launch_learn','name':'Launch & Learn','days':'31–60','activities':[
 ('launch','31–35','Review and launch priority campaigns','Prepare exact channel-specific actions and submit only after founder approval.'),
 ('trials','31–45','Acquire and activate trial users','Guide qualified users to the first meaningful product experience.'),
 ('demos','31–50','Run institutional demonstrations','Qualify prospects and prepare scoped demo and pilot proposals.'),
 ('feedback','36–55','Collect customer feedback','Interview users, improve onboarding and track objections.'),
 ('channels','40–60','Measure channel performance','Compare qualified leads, activation, paid conversion and acquisition cost by source.'),
 ('iterate','51–60','Iterate on launch experiments','Review measured results weekly and adjust offers and campaigns with approval.') ]},
 {'id':'optimize','name':'Focus & Compound','days':'61–90','activities':[
 ('retention','61–75','Improve retention and conversion','Use actual customer behavior to prioritize product and funnel improvements.'),
 ('champions','61–80','Develop champions and referrals','Request genuine testimonials, referrals and reviews from actual users.'),
 ('pilots','66–85','Convert pilots and partnerships','Advance qualified institutional pilots and partner conversations.'),
 ('scale','76–90','Scale effective channels','Allocate effort using verified conversion, revenue and cost evidence.'),
 ('fundraising','76–90','Review investor readiness','Prepare traction-backed updates and individually approved investor communications.') ]}
]

def get_roadmap(store):
 with store.db() as db:
  rows=store.rows(db,'roadmaps')
  if rows:return rows[0]
  row={'id':'portfolio-90-days','current_phase':'foundation','phases':[{**phase,'activities':[{'id':phase['id']+'-'+key,'days':days,'title':title,'description':description,'completed':False,'completed_at':None,'completed_by':None,'completion_note':None} for key,days,title,description in phase['activities']]} for phase in PHASES],'updated_at':now()}
  store.save(db,'roadmaps',row);return row

def update_roadmap(store,data,actor):
 if set(data)-{'current_phase','activities','note'}:raise Invalid('Unknown roadmap field')
 get_roadmap(store)
 with store.db() as db:
  row=store.get(db,'roadmaps','portfolio-90-days')
  if 'current_phase' in data:
   if data['current_phase'] not in [p['id'] for p in row['phases']]:raise Invalid('Invalid phase')
   row['current_phase']=data['current_phase']
  updates=data.get('activities',{})
  if not isinstance(updates,dict):raise Invalid('Activities must map IDs to completion booleans')
  known={a['id']:a for p in row['phases'] for a in p['activities']}
  if set(updates)-set(known):raise Invalid('Unknown activity')
  if any(type(value) is not bool for value in updates.values()):raise Invalid('Activity completion must be boolean')
  for key,value in updates.items():
   a=known[key]
   if a['completed']!=value:
    a.update(completed=value,completed_at=now() if value else None,completed_by=actor if value else None,completion_note=str(data.get('note','Marked complete by founder'))[:1000] if value else None)
  row['updated_at']=now();store.save(db,'roadmaps',row);store.audit(db,'roadmap_updated',row['id'],{'current_phase':row['current_phase'],'activities':updates,'note':data.get('note','')},actor)
  return row
