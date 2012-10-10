'''
Tests the JSON-RPC 2 Mixin library
'''
import unittest
import simplejson as json
from jsonrpc2.mixin import BaseJSONRPCException, RequestHandlerMixin
# this is used by all cases, due to the way tornado wraps unit test we need an instance

class MyException(BaseJSONRPCException):
    """
    Just a simple exception to test the extending capabilities.
    """
    code = 1
    message = "My Custom Exception"

class SimpleController(RequestHandlerMixin):
    """ A simple echo controller.

    Mimics what frameworks usually provides. E.g: in tornado you can extend
    the websocket handler and add the RPC capabilities by extending the mixin
    """
    def echo(self, message, **kwargs):
        return message

    def custom_exception(self, **kwargs):
        raise MyException()

    def internal_error(self, **kwargs):
        raise Exception()

class JsonRpcTest(unittest.TestCase):
    """"JSON RPC Test Suite
    """
    parse_error = -32700
    invalid_request = -32600
    method_not_found = -32601
    internal_error = -32603


    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_errors(self):
        """
        Tests the different errors in the library
        """
        # test no request
        handler = RequestHandlerMixin()
        response = json.loads(str(handler.handle_request(None)))
        error_code = response.get("error").get("code")
        self.assert_(error_code == self.parse_error)

        # test invalid json structure
        response = json.loads(str(handler.handle_request('{"hi": 1}')))
        error_code = response.get("error").get("code")
        self.assert_(error_code == self.invalid_request)

        # tests invalid method
        data = '{"jsonrpc": "2.0", "method": "update", "params": [1,2,3,4,5]}'
        response = json.loads(str(handler.handle_request(data)))
        error_code = response.get("error").get("code")
        self.assert_(error_code == self.method_not_found)

        # tests a protected method call
        # tests invalid method
        data = '{"jsonrpc": "2.0", "method": "handle_request", "params": "123"}'
        response = json.loads(str(handler.handle_request(data)))
        error_code = response.get("error").get("code")
        self.assert_(error_code == self.method_not_found)

    def test_method_call(self):
        """
        Tests a successfull method call
        """
        data = '{"jsonrpc": "2.0", "method": "echo", "params": ["HI"], "id": 4}'
        handler = SimpleController()
        response = json.loads(str(handler.handle_request(data)))
        error = response.get('error')
        request_id = response.get("id")
        self.assert_(request_id == 4)
        self.assert_(error is None)

    def test_raise_exception(self):
        """
        Tests the internal API raising an exception
        """
        data = '{"jsonrpc": "2.0", "method": "custom_exception", "params": [], "id": 4}'
        handler = SimpleController()
        response = json.loads(str(handler.handle_request(data)))
        error = response.get('error')
        request_id = response.get("id")
        self.assert_(request_id == 4)
        self.assert_(error.get("code") ==1)

    def test_raise_internal_error(self):
        """
        Tests the internal API raising an internal system exception
        """
        data = '{"jsonrpc": "2.0", "method": "internal_error", "params": [], "id": 4}'
        handler = SimpleController()
        response = json.loads(str(handler.handle_request(data)))
        error = response.get('error')
        request_id = response.get("id")
        self.assert_(request_id == 4)
        self.assert_(error.get("code") ==self.internal_error)

