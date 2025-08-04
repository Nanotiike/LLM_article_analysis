from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add common security headers to HTTP responses.

    This middleware sets headers to help protect your API against common web vulnerabilities.
    The following headers are added:
      - X-Content-Type-Options: nosniff
      - X-Frame-Options: DENY
      - Strict-Transport-Security: max-age=31536000; includeSubDomains (optional)
      - Content-Security-Policy: default-src 'self'

    Args:
        app: The ASGI application.
        hsts (bool): Whether to include the HSTS header. Defaults to True.
        csp (str): Content Security Policy string. Defaults to "default-src 'self'".
    """

    def __init__(self, app, hsts: bool = True, csp: str = "default-src 'self'"):
        super().__init__(app)
        self.hsts = hsts
        self.csp = csp

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if self.hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        response.headers["Content-Security-Policy"] = self.csp
        return response
