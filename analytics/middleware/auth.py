from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    Checks for the 'X-API-Key' header in incoming requests and validates it against
    the provided API key. If the key is missing or invalid, a 403 response is returned.

    Args:
        app: The ASGI application.
        expected_api_key (str): The API key that is expected.
    """

    def __init__(self, app, expected_api_key: str):
        super().__init__(app)
        self.expected_api_key = expected_api_key
        if not self.expected_api_key:
            raise ValueError("API key must be provided for API key authentication.")

    async def dispatch(self, request: Request, call_next):
        request_api_key = request.headers.get("X-API-Key")
        if request_api_key != self.expected_api_key:
            return JSONResponse({"error": "Invalid API Key"}, status_code=403)
        return await call_next(request)
