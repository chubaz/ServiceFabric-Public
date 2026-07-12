import ast,operator
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}
def calculate(arguments):
 expression=arguments.get("expression")
 if not isinstance(expression,str) or len(expression)>128: raise ValueError("invalid expression")
 def visit(node):
  if isinstance(node,ast.Expression):return visit(node.body)
  if isinstance(node,ast.Constant) and type(node.value) in (int,float):return node.value
  if isinstance(node,ast.BinOp) and type(node.op) in OPS:return OPS[type(node.op)](visit(node.left),visit(node.right))
  raise ValueError("unsupported expression")
 return {"value":visit(ast.parse(expression,mode="eval"))}
