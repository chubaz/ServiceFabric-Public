"""Bounded machine-readable governance CLI projection."""
import argparse,json
def parser():
 root=argparse.ArgumentParser(prog="servicefabric-governance");actions=root.add_subparsers(dest="action",required=True)
 for name in ("get","events","receipts"):
  command=actions.add_parser(name);command.add_argument("operation_ref")
 cancel=actions.add_parser("cancel");cancel.add_argument("operation_ref");cancel.add_argument("--expected-version",type=int,required=True);cancel.add_argument("--reason",required=True)
 return root
def _value(value):
 if hasattr(value,"model_dump"):return value.model_dump(mode="json",by_alias=True)
 if hasattr(value,"__dict__"):return {key:_value(item) for key,item in value.__dict__.items()}
 if isinstance(value,(tuple,list)):return [_value(item) for item in value]
 return value
def execute(client,argv,*,now=None):
 args=parser().parse_args(argv)
 if args.action=="get":operation,version=client.get_operation(args.operation_ref);value={"operation":_value(operation),"version":version}
 elif args.action=="events":value={"events":_value(client.list_operation_events(args.operation_ref))}
 elif args.action=="receipts":value={"effect_receipts":_value(client.effect_receipts(args.operation_ref))}
 else:
  if now is None:raise ValueError("cancel command requires an injected trusted clock")
  value=_value(client.request_cancellation(args.operation_ref,expected_version=args.expected_version,now=now,reason=args.reason))
 return json.dumps(value,sort_keys=True,separators=(",",":"))
