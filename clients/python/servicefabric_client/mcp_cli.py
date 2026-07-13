import argparse,json
from servicefabric_mcp_projection import McpCallRequest,McpCancellationRequest
def parser():
 root=argparse.ArgumentParser(prog="servicefabric-mcp");commands=root.add_subparsers(dest="command",required=True);listing=commands.add_parser("list");listing.add_argument("session_id");call=commands.add_parser("call");call.add_argument("session_id");call.add_argument("tool_name");call.add_argument("--arguments",default="{}");task=commands.add_parser("task");task.add_argument("session_id");task.add_argument("operation_ref");cancel=commands.add_parser("cancel");cancel.add_argument("session_id");cancel.add_argument("operation_ref");cancel.add_argument("expected_version",type=int);cancel.add_argument("reason");return root
def execute(client,argv,*,now):
 args=parser().parse_args(argv)
 if args.command=="list":value=client.list_tools(session_id=args.session_id,now=now).model_dump(mode="json")
 elif args.command=="call":value=client.call(session_id=args.session_id,now=now,call=McpCallRequest(request_id="mcp-call-1",tool_name=args.tool_name,correlation_id="mcp-correlation-1",arguments=json.loads(args.arguments))).model_dump(mode="json")
 elif args.command=="task":value=client.task(session_id=args.session_id,operation_ref=args.operation_ref,now=now).model_dump(mode="json")
 else:value=client.cancel(session_id=args.session_id,request=McpCancellationRequest(request_id="mcp-cancel-1",operation_ref=args.operation_ref,reason=args.reason),expected_version=args.expected_version,now=now).model_dump(mode="json")
 return json.dumps(value,sort_keys=True,separators=(",",":"))
