import unittest
from servicefabric_contracts.caller import CallerContext
from servicefabric_mcp_projection import DiscoveryService,ProjectionCandidate
def caller(scopes):return CallerContext(subject_ref="user-alice",principal_type="human",tenant_ref="tenant-demo",issuer="identity",scopes=scopes,authentication_strength="multi_factor")
class DiscoveryTests(unittest.TestCase):
 def test_discovery_is_caller_specific_ordered_and_paged(self):
  candidates=(ProjectionCandidate("research.search_papers","1.0.0","research-search","Search","Search papers.",{},True,True,("research-search",)),ProjectionCandidate("math.calculate","1.0.0","math-calculate","Calculate","Calculate.",{},True,True,("math-calculate",)),ProjectionCandidate("remote.hidden","1.0.0","remote-hidden","Remote","Remote.",{},True,True,(),federated=True))
  discovery=DiscoveryService(candidates,maximum_page_size=1);first=discovery.list_tools(caller(("math-calculate","research-search")),page_size=1);second=discovery.list_tools(caller(("math-calculate","research-search")),cursor=first.next_cursor,page_size=1)
  self.assertEqual(([x.name for x in first.tools],[x.name for x in second.tools]),(["math-calculate"],["research-search"]))
 def test_disabled_unavailable_and_unauthorized_tools_remain_hidden(self):
  candidates=(ProjectionCandidate("math.calculate","1.0.0","math-calculate","Calculate","Calculate.",{},True,True,("math-calculate",)),ProjectionCandidate("x.hidden","1.0.0","hidden","Hidden","Hidden.",{},False,True,()),ProjectionCandidate("x.down","1.0.0","down","Down","Down.",{},True,False,()))
  self.assertEqual(DiscoveryService(candidates).list_tools(caller(())).tools,())
 def test_invalid_cursor_and_page_limit_rejected(self):
  service=DiscoveryService((),maximum_page_size=2)
  with self.assertRaises(ValueError):service.list_tools(caller(()),page_size=3)
  with self.assertRaises(ValueError):service.list_tools(caller(()),cursor="missing")
 def test_duplicate_projected_names_are_rejected(self):
  candidate=ProjectionCandidate("math.calculate","1.0.0","math-calculate","Calculate","Calculate.",{},True,True)
  with self.assertRaises(ValueError):DiscoveryService((candidate,candidate))
if __name__=="__main__":unittest.main()
