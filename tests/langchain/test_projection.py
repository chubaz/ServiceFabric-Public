import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/"packages/servicefabric_langchain"))
from servicefabric_langchain import ServiceFabricToolset
class Result:status="success";data={"value":4};warnings=();evidence=();effect_receipts=()
class Client:
 def invoke(self,request):self.request=request;return Result()
class ProjectionTests(unittest.TestCase):
 def test_projection_routes_through_client(self):
  client=Client();tools=ServiceFabricToolset(client,"research-demo",["math.calculate"],lambda tool,args:(tool,args)).load_tools();self.assertEqual(tools[0].invoke({"expression":"2+2"})["data"],[{"value":4}][0]);self.assertEqual(client.request[0],"math.calculate")
