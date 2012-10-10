# This file is part of simple-rpc-json.
#
# jsonrpc is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this software; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""JSON RPC 2 Mixin Implementation Library
(http://www.jsonrpc.org/specification)

Provides a Mixin-style implementation to work with the JSON-RPC v2 protocol.

Notice: Batch RPCs are yet not supported.

"""
__author__ = 'dla.mora@gmail.com (David Mora)'

import simplejson as json
import sys

#corresponding spec version
RPC_VERSION = "2.0"

class BaseJSONRPCException(Exception):
    """ Base Exception for all RPC related exceptions"""
    pass

class ResourceResponseJSONEncoder(json.JSONEncoder):
    """ Encoder for JSON RPC Messages going out of the server.

    Just a Object oriented style to handle the correct format according to the
    JSON-RPC spec.

    The result of a method being invoked in a alternate library will result
    on a ResourceResponse object that can be encoded using this logic.

    Provides also an alternate way to block attributes that should not be
    transferred through the protocol.
    """
    def default(self, obj):
        if isinstance(obj, BaseResourceResponse):
            response = {"jsonrpc" : RPC_VERSION}
            for field in dir(obj):
                if not field.startswith('_') and not field in obj._exclude:
                    value = getattr(obj, field)
                    response[field] = value
            return response
        return json.JSONEncoder.default(self, obj)

class BaseResourceResponse(object):
    """Base Class for all Responses from the RPC implementation.

    The idea here is to handle responses as "views". Since we have the
    ResourceResponseJSONEncoder in place, we can just simple assign attributes
    to this class or any extending class that are going to be transferred trough
    the protocol.

    Extending the Protocol itself is as simple as extending this object.
    """
    def __init__(self, request_id):
        self.id = request_id
        # Members to exclude when encoding
        self._exclude = []

    def __str__(self, *args, **kwargs):
        return json.dumps(self, cls=ResourceResponseJSONEncoder)

class InternalError(BaseResourceResponse):
    """The error response for a Internal RPC provider Error"""
    def __init__(self, request_id = None):
        BaseResourceResponse.__init__(self, request_id)
        self.error = {"code": -32603, "message": "Internal error."}

class NonExistentMethodError(BaseResourceResponse):
    """The error response for a Non Existent Method"""
    def __init__(self, request_id = None):
        BaseResourceResponse.__init__(self, request_id)
        self.error = {"code": -32601, "message": "Method not found."}

class InvalidJSONError(BaseResourceResponse):
    """The error response for a Invalid JSON (parse error)"""
    def __init__(self, request_id = None):
        BaseResourceResponse.__init__(self, request_id)
        self.error = {"code": -32700, "message": "Parse error."}

class invalidRequestObjecError(BaseResourceResponse):
    """The error response for a invalid Request Object"""
    def __init__(self, request_id = None):
        BaseResourceResponse.__init__(self, request_id)
        self.error = {"code": -32600, "message": "Invalid Request."}

class CustomException(BaseResourceResponse):
    """The error response for a custom exception

    Use this when using a Exception (code and message) style of API implementation
    for error handling and by extending the BaseJSONRPCException
    """
    def __init__(self, e, request_id = None):
        BaseResourceResponse.__init__(self, request_id)
        self.error = {"code": e.code , "message": e.message}

class SuccessResponse(BaseResourceResponse):
    """Identifies a sucessful response

    Extend this class and return it on your service methods, this way the library
    will make use of the new Sucess Response.
    """
    def __init__(self, result, request_id = None):
        BaseResourceResponse.__init__(self, request_id)
        self.result = result

class RequestHandlerMixin(object):
    """The Request Handler Mixin

    The idea here is to provide other solutions/framework with a mixin to support
    RPC calls.

    By passing the raw body string of the request to the handle_request should
    be enough. This method will return the corresponding JSON which needs to be
    carried on through the procol.

    On those Internal server errors, logging is available by just having
    the extending class assign a attribute _logger with the logger instance
    """
    def _get_protected_handler(self):
        """Should return a object which methods need to be protected from
        being called through the protocol.

        Overload/extend to return the object type that needs to be protected.
        """
        return None

    def handle_request(self, data):
        """Handles the request.

        Data corresponds to the request raw body. This method will call a simple
        validation that at the end will unpack the json params of the method
        and call that method in the class that is extending this mixin class.
        """
        # first try to validate the json
        try:
            request = json.loads(data)
        except:
            return InvalidJSONError()

        return self._validate_request(request)

    def _validate_request(self, request_object):
        """Performs a Simple validation

        Validates the request object (list) and calls the proper
        extending class method being invoked.
        """
        if len(request_object) < 1: # we should have a list here
            return InvalidJSONError()

        json_version = request_object.get('jsonrpc')
        if json_version != RPC_VERSION:
            return invalidRequestObjecError()

        method = request_object.get("method")
        params = request_object.get("params")
        request_id = request_object.get("id")

        protected_handler = self._get_protected_handler()
        protected_methods = dir(RequestHandlerMixin) + dir(protected_handler)
        if method in dir(self) and method not in protected_methods:
            method_invoked = getattr(self, method)
            try:
                invoked_result = method_invoked(*params, **request_object)
                if isinstance(invoked_result, SuccessResponse):
                    return invoked_result
                return SuccessResponse(invoked_result, request_id)
            except TypeError:
                return invalidRequestObjecError(request_id)
            except BaseJSONRPCException, e:
                return CustomException(e, request_id)
            except: # something went really wrong
                if (hasattr(self, '_logger')):
                    self._logger.exception(sys.exc_info()[0])
                return InternalError(request_id)
        else:
            return NonExistentMethodError(request_id)