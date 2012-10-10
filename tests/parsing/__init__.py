import unittest

from test_parsing import JsonRpcTest
suite = unittest.TestLoader().loadTestsFromTestCase(JsonRpcTest)
unittest.TextTestRunner(verbosity=2).run(suite)