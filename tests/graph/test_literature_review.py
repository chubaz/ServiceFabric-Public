import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/"services/graph_runner"))
from literature_review import FakeReviewModel,LiteratureReviewGraph
class Result:status="success";data={"papers":[{"title":"A"}]}
class Client:
 def invoke(self,request):self.calls=[request];return Result()
class GraphTests(unittest.TestCase):
 def test_nested_call_uses_client(self):
  client=Client();value=LiteratureReviewGraph(client,lambda tool,args:(tool,args),FakeReviewModel()).invoke({"question":" agents "});self.assertEqual(client.calls[0][0],"research.search_papers");self.assertEqual(value["summary"],"Review of agents: 1 papers.")
