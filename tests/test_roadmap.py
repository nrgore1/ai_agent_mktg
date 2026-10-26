import tempfile,unittest
from growthpilot.platform import Platform
from growthpilot.core import Invalid
class RoadmapTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.s=Platform(self.tmp.name+'/r.db')
 def tearDown(self):self.tmp.cleanup()
 def test_defaults_pending(self):
  r=self.s.roadmap();self.assertEqual(r['current_phase'],'foundation');self.assertEqual(len(r['phases'][0]['activities']),14);self.assertFalse(any(a['completed'] for p in r['phases'] for a in p['activities']))
 def test_founder_completion_does_not_change_actuals(self):
  old=self.s.snapshot();tasks={a['id']:True for a in old['roadmap']['phases'][0]['activities']};r=self.s.update_roadmap({'current_phase':'launch_learn','activities':tasks,'note':'Completed for now at founder request'},'founder');new=self.s.snapshot()
  self.assertTrue(all(a['completed'] for a in r['phases'][0]['activities']));self.assertEqual(new['metrics'],old['metrics']);self.assertEqual(new['products'],old['products']);self.assertEqual(new['events'],[]);self.assertEqual(Platform(self.s.path).roadmap()['current_phase'],'launch_learn')
 def test_invalid_updates_are_atomic(self):
  with self.assertRaises(Invalid):self.s.update_roadmap({'current_phase':'launch_learn','activities':{'missing':True}},'founder')
  self.assertEqual(self.s.roadmap()['current_phase'],'foundation')
 def test_reopen_preserves_other_tasks(self):
  task=self.s.roadmap()['phases'][0]['activities'][0]['id'];self.s.update_roadmap({'activities':{task:True}},'founder');r=self.s.update_roadmap({'activities':{task:False}},'founder');a=r['phases'][0]['activities'][0];self.assertFalse(a['completed']);self.assertIsNone(a['completed_at'])
if __name__=='__main__':unittest.main()
