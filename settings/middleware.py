import logging

logger = logging.getLogger("debug_requests")

class DebugRequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.debug("%s %s", request.method, request.get_full_path())
        return self.get_response(request)