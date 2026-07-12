#!/usr/bin/env python3
"""Translate one explicit legacy manifest and always emit a safe report."""
import argparse,json,os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"packages/servicefabric_contracts/src"))
from servicefabric_contracts.legacy_translation import translate_legacy_manifest
from servicefabric_contracts.translation_context import TranslationContext
def write_atomic(path:Path,data:str):
 if path.exists() and path.is_symlink(): raise ValueError("output cannot be a symlink")
 fd,name=tempfile.mkstemp(dir=path.parent,prefix=".translation-")
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as handle: handle.write(data)
  os.replace(name,path)
 finally:
  if os.path.exists(name): os.unlink(name)
def main():
 p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--context",required=True); p.add_argument("--output",required=True); p.add_argument("--report",required=True); p.add_argument("--strict",action="store_true"); a=p.parse_args()
 source,context,output,report=map(Path,(a.input,a.context,a.output,a.report))
 if output.resolve()==source.resolve() or report.resolve()==source.resolve(): return 3
 try:
  result=translate_legacy_manifest(source.read_bytes(),TranslationContext.model_validate_json(context.read_text()),source.as_posix())
  payload=json.dumps(result.model_dump(mode="json",by_alias=True),indent=2,sort_keys=True)+"\n"; write_atomic(report,payload)
  if result.canonical_resource:
   write_atomic(output,json.dumps(result.canonical_resource.model_dump(mode="json",by_alias=True),indent=2,sort_keys=True)+"\n"); print("Legacy manifest translated; human review remains required."); return 0
  print(f"Legacy manifest assessment: {result.status}"); return 2 if result.status in {"requires_context","requires_split"} else 3
 except Exception: print("Legacy manifest translation failed safely.",file=sys.stderr); return 4
if __name__=="__main__": raise SystemExit(main())
