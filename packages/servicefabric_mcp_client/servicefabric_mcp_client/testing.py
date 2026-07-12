class FakeMcpTransport:
 def __init__(self,tools,responses):self.tools=tools;self.responses=responses;self.calls=[]
 def describe(self,name):return self.tools[name]
 def call(self,name,arguments):self.calls.append((name,arguments));return self.responses[name]
