import unittest
from servicefabric_mcp_projection import InProcessTransport,TransportError
class TransportTests(unittest.TestCase):
 def test_in_process_exchange_is_bounded_and_deterministic(self):
  transport=InProcessTransport(lambda message:{"echo":message},maximum_message_bytes=32,maximum_response_bytes=64);self.assertEqual(transport.exchange({"a":1}),{"echo":{"a":1}})
  with self.assertRaises(TransportError):transport.exchange({"large":"x"*100})
 def test_close_and_response_limit(self):
  transport=InProcessTransport(lambda message:{"large":"x"*100},maximum_response_bytes=8)
  with self.assertRaises(TransportError):transport.exchange({})
  transport=InProcessTransport(lambda message:{}) ;transport.close()
  with self.assertRaises(TransportError):transport.exchange({})
if __name__=="__main__":unittest.main()
