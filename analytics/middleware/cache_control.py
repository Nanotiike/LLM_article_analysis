from starlette.middleware.base import BaseHTTPMiddleware


class NoCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to disable caching for dynamic API responses.

    This middleware sets HTTP headers to ensure that responses are not cached
    by clients or proxies.

    The following headers are set:
      - Cache-Control: no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0
      - Pragma: no-cache
      - Expires: 0
    """

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
