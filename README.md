A Python Mixin approach for JSON-RPC v2.0 protocol
======================

A Python Mixin approach for JSON-RPC v2.0

Why?
-------
When building a solution, a framework is selected (django, tornado, web.py, etc).
The main idea of having a Mixin approach is to leverage eveything that has to
deal with the spec itself (decoding messages, encoding messages of invoked method
result) without providing another WSGI handler that needs to run part of the stack.

How?
-------
Basing the approach of a MVC, you have a controller handling the requests, or
another type of request handler.

A good example of this is the websocket implementation by tornado. For instance:

    class MyWebSocketHandler(tornado.websocket.WebSocketHandler, RequestHandlerMixin):
    pass

Your handler is already providing the transport by extending the tornado websocket
and is capable of RPC by mixin' in the RequestHandlerMixin form this library.

Basic Usage
-------
    from jsonrpc2.mixin import BaseJSONRPCException, RequestHandlerMixin

    class MyException(BaseJSONRPCException):
        """
        Just a simple exception to test the extending capabilities or error handling.
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

And in the context of your handler (according to the framework)

    handler = SimpleController()
    response = str(handler.handle_request(data))

At this point, you need to pass the response back via the transport handler and
you are set!

Testing
-------

To run the tests:
    $ python -m unittest -v tests.parsing
