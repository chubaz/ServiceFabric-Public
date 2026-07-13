import unittest
from datetime import datetime,timedelta,timezone
from servicefabric_contracts.caller import CallerContext
from servicefabric_mcp_projection import McpClientCapabilities,SessionError,SessionManager,TrustedMcpTransportContext
NOW=datetime(2030,1,1,tzinfo=timezone.utc)
def caller():return CallerContext(subject_ref="user-alice",principal_type="human",tenant_ref="tenant-demo",issuer="identity",authentication_strength="multi_factor")
def trusted(caller_context=None,adapter_ref="trusted-mcp-adapter"):return TrustedMcpTransportContext(caller=caller_context or caller(),adapter_ref=adapter_ref)
class SessionTests(unittest.TestCase):
 def test_negotiation_is_trusted_isolated_and_bounded(self):
  manager=SessionManager(maximum_sessions=1,maximum_requests=1,lifetime=timedelta(minutes=1));session,server=manager.initialize(session_id="session-1",trusted_context=trusted(),capabilities=McpClientCapabilities(progress=True),now=NOW);self.assertTrue(server.progress);self.assertEqual(manager.request("session-1",now=NOW).request_count,1)
  with self.assertRaises(SessionError):manager.request("session-1",now=NOW)
  with self.assertRaises(SessionError):manager.initialize(session_id="session-2",trusted_context=trusted(),capabilities=McpClientCapabilities(),now=NOW)
 def test_untrusted_and_expired_sessions_are_rejected(self):
  manager=SessionManager(lifetime=timedelta(seconds=1))
  with self.assertRaises(SessionError):manager.initialize(session_id="session-1",trusted_context=trusted(adapter_ref="caller"),capabilities=McpClientCapabilities(),now=NOW)
  manager.initialize(session_id="session-1",trusted_context=trusted(),capabilities=McpClientCapabilities(),now=NOW)
  with self.assertRaises(SessionError):manager.request("session-1",now=NOW+timedelta(seconds=1))
if __name__=="__main__":unittest.main()
