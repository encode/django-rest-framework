class BaseMiddleware:
    """
    All middleware classes should extend BaseMiddleware.
    """

    def process_request(self, request):
        pass

    def process_response(self, response):
        pass


class FooMiddleware(BaseMiddleware):
    def process_request(self, request):
        request._foo = "foo"

    def process_response(self, response):
        pass


class BarMiddleware(BaseMiddleware):
    def process_request(self, request):
        pass

    def process_response(self, response):
        response._bar = "bar"
