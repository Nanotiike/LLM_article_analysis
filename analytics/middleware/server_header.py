from starlette.middleware.base import BaseHTTPMiddleware


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware to customize the 'Server' header in HTTP responses.

    This middleware intercepts each request and sets the 'Server' header in the
    response to the provided custom server name.

    Args:
        app: The ASGI application.
        server_name (str): The custom name to set in the 'Server' header.
    """

    def __init__(self, app, server_name: str, **kwargs):
        super().__init__(app)
        self.server_name = server_name

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["server"] = self.server_name
        return response
