import os,sys,unittest,json,uuid,types
from unittest.mock import AsyncMock,MagicMock,patch
os.environ.update(WEDDINGOS_ENVIRONMENT='test',WEDDINGOS_AUTH_REQUIRED='true',WEDDINGOS_AUTO_CREATE_SCHEMA='false')
sys.path.insert(0,'src')
from weddingos_api.routers import free_tools as f
from fastapi import HTTPException
from pydantic import ValidationError

class Checks(unittest.IsolatedAsyncioTestCase):
 def payload(self,**kw):return f.PlanInput(**dict({'id':uuid.uuid4(),'tool':'budget','title':'Synthetic plan','inputs':{},'result':{}},**kw))
 def test_unauthenticated_save_denied(self):
  with self.assertRaises(HTTPException)as e:f.owner(types.SimpleNamespace(user_id=None))
  self.assertEqual(e.exception.status_code,401)
 def test_registered_owner_supported(self):
  uid=uuid.uuid4();self.assertEqual(f.owner(types.SimpleNamespace(user_id=uid)),uid)
 def test_caller_cannot_supply_plan_owner(self):
  with self.assertRaises(ValidationError):self.payload(user_id=str(uuid.uuid4()))
 def test_unknown_tool_rejected(self):
  with self.assertRaises(ValidationError):self.payload(tool='paid-workspace')
 def test_oversized_plan_rejected(self):
  with self.assertRaises(ValidationError):self.payload(inputs={'blob':'x'*50001})
 def test_nonfinite_snapshot_rejected(self):
  with self.assertRaises(ValidationError):self.payload(result={'cost':float('nan')})
 async def test_cross_account_overwrite_denied(self):
  session=AsyncMock();session.get.return_value=types.SimpleNamespace(user_id=uuid.uuid4())
  with self.assertRaises(HTTPException)as e:await f.save_plan(self.payload(),types.SimpleNamespace(user_id=uuid.uuid4()),session)
  self.assertEqual(e.exception.status_code,404);session.commit.assert_not_called()
 async def test_twenty_plan_limit_denied(self):
  session=AsyncMock();session.get.return_value=None;session.scalars.return_value=list(range(20))
  with self.assertRaises(HTTPException)as e:await f.save_plan(self.payload(),types.SimpleNamespace(user_id=uuid.uuid4()),session)
  self.assertEqual(e.exception.status_code,409);session.commit.assert_not_called()
 async def test_last_free_plan_allowed(self):
  session=AsyncMock();session.add=MagicMock();session.get.return_value=None;session.scalars.return_value=list(range(19))
  with patch.object(f,'append_platform_audit',new_callable=AsyncMock):result=await f.save_plan(self.payload(),types.SimpleNamespace(user_id=uuid.uuid4()),session)
  self.assertEqual(result['tool'],'budget');session.commit.assert_awaited_once()
 async def test_retry_does_not_consume_quota(self):
  uid=uuid.uuid4();p=self.payload();session=AsyncMock();session.get.return_value=types.SimpleNamespace(user_id=uid,created_at=None,**p.model_dump())
  result=await f.save_plan(p,types.SimpleNamespace(user_id=uid),session)
  self.assertEqual(result['id'],str(p.id));session.scalars.assert_not_called();session.commit.assert_not_called()
 async def test_missing_or_foreign_delete_denied(self):
  session=AsyncMock();session.scalar.return_value=None
  with self.assertRaises(HTTPException)as e:await f.delete_plan(uuid.uuid4(),types.SimpleNamespace(user_id=uuid.uuid4()),session)
  self.assertEqual(e.exception.status_code,404);session.delete.assert_not_called()

suite=unittest.defaultTestLoader.loadTestsFromTestCase(Checks);result=unittest.TextTestRunner(verbosity=2).run(suite)
print('AGENTVIRE_RESULT '+json.dumps({'tests':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'failed_tests':[str(t)for t,_ in result.failures],'error_tests':[str(t)for t,_ in result.errors]}))
