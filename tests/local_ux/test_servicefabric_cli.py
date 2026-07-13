import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
COMMAND=[os.environ.get("SERVICEFABRIC_COMMAND", "servicefabric")]
class LocalDeveloperUxTests(unittest.TestCase):
 def command(self,*args,home):return subprocess.run([*COMMAND,*args],cwd=ROOT,env={**os.environ,"SERVICEFABRIC_HOME":str(home)},capture_output=True,text=True)
 def test_initialize_list_and_invoke(self):
  with tempfile.TemporaryDirectory() as temporary:
   home=Path(temporary)/"workspace";self.assertEqual(self.command("init",home=home).returncode,0);self.assertEqual(self.command("init",home=home).returncode,0);self.assertEqual(self.command("tools","list",home=home).returncode,0);result=self.command("invoke","math.calculate","--arguments",'{"expression":"1+2*3"}',home=home);self.assertEqual(result.returncode,0);self.assertIn('"value": 7',result.stdout)
 def test_uninitialized_and_invalid_json_fail_safely(self):
  with tempfile.TemporaryDirectory() as temporary:
   home=Path(temporary)/"workspace";self.assertNotEqual(self.command("status",home=home).returncode,0);self.command("init",home=home);result=self.command("invoke","math.calculate","--arguments","{",home=home);self.assertNotEqual(result.returncode,0);self.assertNotIn("Traceback",result.stderr)
