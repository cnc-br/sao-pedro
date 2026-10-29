import logging


logger = logging.getLogger(__name__)


class HealthRequestSourceLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info in ("/health", "/health/"):
            logger.warning(
                "health_request_source ip=%s user_agent=%r referer=%r",
                request.META.get("REMOTE_ADDR", "unknown"),
                request.META.get("HTTP_USER_AGENT", ""),
                request.META.get("HTTP_REFERER", ""),
            )

        return self.get_response(request)
