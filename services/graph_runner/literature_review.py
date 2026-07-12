class LiteratureReviewGraph:
 def __init__(self,client,request_factory,model):self.client=client;self.request_factory=request_factory;self.model=model
 def invoke(self,arguments):
  question=arguments["question"].strip();result=self.client.invoke(self.request_factory("research.search_papers",{"query":question,"maximum_results":arguments.get("maximum_results",5)}))
  if result.status=="error":raise RuntimeError(result.error.message)
  papers=(result.data or {}).get("papers",[])
  return {"question":question,"summary":self.model.summarize(question,papers),"papers":papers}
class FakeReviewModel:
 def summarize(self,question,papers):return f"Review of {question}: {len(papers)} papers."
