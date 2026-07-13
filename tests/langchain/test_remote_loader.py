import unittest
from servicefabric_langchain import RemoteResearchDemoLoader

class Client:
 def list_tools(self): return ("research.search_papers",)
 def invoke(self, tool_id, arguments):
  class Result: status="success"; data={"tool":tool_id,"query":arguments["query"]}
  return Result()

class RemoteLoaderTests(unittest.TestCase):
 def test_loader_delegates_to_remote_client(self):
  tool=RemoteResearchDemoLoader(Client()).load_tools()[0]
  self.assertEqual(tool.invoke({"query":"retrieval"})["tool"],"research.search_papers")
