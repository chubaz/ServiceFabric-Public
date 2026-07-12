import argparse,json
def parser():
 p=argparse.ArgumentParser();p.add_argument("tool_id",choices=["math.calculate"]);p.add_argument("--expression",required=True);return p
def arguments(argv=None):
 value=parser().parse_args(argv);return {"tool_id":value.tool_id,"arguments":{"expression":value.expression}}
if __name__=="__main__":print(json.dumps(arguments(),sort_keys=True))
