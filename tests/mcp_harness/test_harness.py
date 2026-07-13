import unittest
from servicefabric_mcp_harness import GoldenTranscript,McpHarness,TranscriptError
class HarnessTests(unittest.TestCase):
 def test_golden_transcript_is_deterministic_and_replays(self):
  transcript=GoldenTranscript(((({"type":"initialize"},{"ok":True})),(({"type":"tools/list"},{"tools":[]}))))
  self.assertEqual(transcript.canonical(),GoldenTranscript.parse(transcript.canonical()).canonical());McpHarness(lambda message:{"ok":True} if message["type"]=="initialize" else {"tools":[]}).replay(transcript)
 def test_mismatch_and_malformed_transcripts_fail(self):
  with self.assertRaises(TranscriptError):GoldenTranscript.parse("{}")
  with self.assertRaises(TranscriptError):McpHarness(lambda message:{}).replay(GoldenTranscript((({}, {"expected":True}),)))
if __name__=="__main__":unittest.main()
