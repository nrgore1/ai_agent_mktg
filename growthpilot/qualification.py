"""Import operator-verified entitlement test evidence; never approve commercial actions."""
import argparse
import copy
import datetime as dt
import json
import re
from pathlib import Path
from .core import Invalid, digest, now
from .execution import Execution, VERSION

CASES = ('free_tier','paid_tier','usage_limits','cross_tier_denial','sandbox_checkout','webhooks','cancellation','refunds')
STATUSES = {'passed','partial','failed','blocked','not_applicable'}


class Qualification:
    def __init__(self, store):
        self.s = store

    def summary(self):
        with self.s.db() as db:
            runs = sorted(self.s.rows(db, 'qualification_runs'), key=lambda r:r['recorded_at'], reverse=True)
        return runs[0] if runs else None

    def record(self, report, actor='authorized_test_runner'):
        if set(report) != {'run_id','recorded_at','strategy_revision','products','source'}:
            raise Invalid('Invalid qualification report envelope')
        if not re.fullmatch(r'[A-Za-z0-9_-]{8,100}', str(report['run_id'])):
            raise Invalid('Invalid run identifier')
        try:
            stamp = dt.datetime.fromisoformat(report['recorded_at'])
            age = dt.datetime.now(dt.timezone.utc)-stamp
        except (TypeError,ValueError):
            raise Invalid('Test evidence requires a timezone-aware timestamp')
        if age < -dt.timedelta(minutes=5) or age > dt.timedelta(days=7):
            raise Invalid('Test evidence is stale or future-dated')
        if not isinstance(report['source'],str) or not 10 <= len(report['source']) <= 1000:
            raise Invalid('A durable evidence source is required')
        rows = report['products']
        if not isinstance(rows,list) or len(rows)!=17 or not all(isinstance(r,dict)for r in rows) or {r.get('product_id')for r in rows} != set(range(1,18)):
            raise Invalid('Exactly one report for each of the 17 products is required')
        for row in rows:
            if set(row) != {'product_id','wave','source_version','environment','cases','note'}:
                raise Invalid('Invalid product report')
            pid = row['product_id'];expected_wave=1 if pid<=4 else 2 if pid in (5,6,9) else 3
            if type(pid)is not int or row['wave']!=expected_wave or row['environment'] not in ('isolated_deployed_image','isolated_source','not_available','internal_only','shared_product'):
                raise Invalid('Product wave or environment mismatch')
            if not isinstance(row['source_version'],str) or len(row['source_version'])>250 or not isinstance(row['note'],str) or len(row['note'])>3000:
                raise Invalid('Invalid source version or product note')
            if not isinstance(row['cases'],list) or len(row['cases'])!=len(CASES) or not all(isinstance(c,dict)for c in row['cases']) or {c.get('key')for c in row['cases']}!=set(CASES):
                raise Invalid('Every acceptance category must be accounted for')
            for case in row['cases']:
                if set(case)!={'key','status','level','checks_passed','checks_failed','evidence'} or case['status']not in STATUSES:
                    raise Invalid('Invalid test case')
                if case['level']not in ('sandbox_e2e','offline_product_tests','source_verified','not_run'):
                    raise Invalid('Unknown evidence level')
                if any(type(case[k])is not int or case[k]<0 for k in ('checks_passed','checks_failed')):
                    raise Invalid('Invalid measured check count')
                if not isinstance(case['evidence'],str) or not 20<=len(case['evidence'])<=3000:
                    raise Invalid('Detailed case evidence is required')
                if case['status']=='passed' and (case['checks_passed']==0 or case['checks_failed'] or case['level']!='sandbox_e2e' or not row['source_version']):
                    raise Invalid('Full pass requires measured sandbox end-to-end evidence and source version')
                if case['status']=='not_applicable' and (case['level']!='source_verified' or not row['source_version']):
                    raise Invalid('Inapplicability needs a verified scoped rationale')
                if case['status']=='partial' and (not case['checks_passed'] or case['checks_failed']):
                    raise Invalid('Partial requires passing component checks without known failures')
                if case['checks_failed'] and case['status']!='failed':
                    raise Invalid('Failed checks cannot be relabelled as passes')
        engine=Execution(self.s);snapshot=engine.summary()
        if snapshot['source_changed'] or not snapshot['program'] or report['strategy_revision']!=snapshot['program']['revision']:
            raise Invalid('Test report must match the current strategy revision')
        report_hash=digest(report)
        with self.s.db() as db:
            existing=next((r for r in self.s.rows(db,'qualification_runs')if r['id']==report['run_id']),None)
            if existing:
                if existing['report_hash']!=report_hash:raise Invalid('Run ID already belongs to different evidence')
                return existing
            if self.s.paused(db):raise Invalid('System paused')
            prior=self.s.rows(db,'qualification_runs')
            if any(dt.datetime.fromisoformat(r['recorded_at'])>=stamp for r in prior):
                raise Invalid('Older evidence cannot supersede the latest test run')
            current_engine,current_plan=engine.source()
            current_revision=digest({'version':VERSION,'plan':current_plan,'dossiers':current_engine.strategies})
            programs=self.s.rows(db,'execution_program')
            if not programs or current_revision!=report['strategy_revision'] or programs[0]['revision']!=current_revision:
                raise Invalid('Strategy changed while recording evidence')
            tasks={t['product_id']:t for t in self.s.rows(db,'execution_tasks')if t['key']=='entitlements'}
            all_tasks={t['id']:t for t in self.s.rows(db,'execution_tasks')}
            decisions=[]
            for row in rows:
                task=tasks[row['product_id']]
                if task['commercial_gate']:raise Invalid('Commercial approval is excluded')
                checks_complete=all(c['status']in ('passed','not_applicable')for c in row['cases'])
                dependencies=[d for d in task['dependencies']if all_tasks.get(d,{}).get('status')!='completed']
                approved=checks_complete and not dependencies
                decision='technical_approved' if approved else 'blocked_prerequisites' if checks_complete else 'blocked_test_coverage'
                # Evidence acceptance does not attest legal identity, finance or pricing.
                task.setdefault('history',[]).append({'status':task['status'],'updated_at':task['updated_at'],'evidence':copy.deepcopy(task.get('evidence',[]))})
                task['status']='completed'if approved else'blocked'
                task['updated_at']=now()
                task['evidence'].append({'source':report['source'],'note':row['note']+' Automatic decision: '+decision+'. Case-level evidence is in the wave test report. Commercial and prerequisite approvals are unchanged.','type':'automated_test_evidence','actor':actor,'recorded_at':now(),'run_id':report['run_id'],'report_hash':report_hash})
                self.s.save(db,'execution_tasks',task)
                decisions.append(dict(row,decision=decision,blocking_prerequisites=dependencies,task_id=task['id']))
            result={'id':report['run_id'],'report_hash':report_hash,'recorded_at':report['recorded_at'],'strategy_revision':report['strategy_revision'],'source':report['source'],'products':decisions,'technical_approvals':sum(r['decision']=='technical_approved'for r in decisions),'commercial_approvals':0,'external_actions':0}
            self.s.save(db,'qualification_runs',result)
            self.s.audit(db,'wave_tests_recorded',result['id'],{'report_hash':report_hash,'technical_approvals':result['technical_approvals'],'commercial_approvals':0},actor)
        return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--db',required=True);parser.add_argument('--report',required=True);args=parser.parse_args()
    path=Path(args.report)
    if path.stat().st_size>262144:raise Invalid('Report too large')
    from .platform import Platform
    result=Qualification(Platform(args.db)).record(json.loads(path.read_text()))
    print(json.dumps({'run_id':result['id'],'products':len(result['products']),'technical_approvals':result['technical_approvals'],'commercial_approvals':0}))

if __name__=='__main__':main()
