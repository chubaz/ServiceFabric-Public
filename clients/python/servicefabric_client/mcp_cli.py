import argparse,json
from servicefabric_mcp_projection import McpCallRequest
def parser():
 root=argparse.ArgumentParser(prog="servicefabric-mcp");commands=root.add_subparsers(dest="command",required=True);listing=commands.add_parser("list");listing.add_argument("session_id");call=commands.add_parser("call");call.add_argument("session_id");call.add_argument("tool_name");call.add_argument("--arguments",default="{}");return root
def execute(client,argv,*,now):
 args=parser().parse_args(argv)
 if args.command=="list":value=client.list_tools(session_id=args.session_id,now=now).model_dump(mode="json")
 else:value=client.call(session_id=args.session_id,now=now,call=McpCallRequest(request_id="mcp-call-1",tool_name=args.tool_name,correlation_id="mcp-correlation-1",arguments=json.loads(args.arguments))).model_dump(mode="json")
 return json.dumps(value,sort_keys=True,separators=(",",":"))
