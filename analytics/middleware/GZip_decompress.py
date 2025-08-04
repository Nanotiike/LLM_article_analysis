import gzip

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class GZipDecompressMiddleware(BaseHTTPMiddleware):
    """
    Middleware to decompress incoming gzipped request bodies.

    If the incoming request has a 'Content-Encoding' header with the value 'gzip',
    this middleware will read the request body, decompress it using gzip, and then
    replace the request's receive method so that the rest of the application sees
    the decompressed data. It also removes the 'Content-Encoding' header from the scope.

    Returns a 400 response if the decompression fails.
    """

    async def dispatch(self, request: Request, call_next):
        if request.headers.get("Content-Encoding", "").lower() == "gzip":
            # Read and decompress the request body.
            body = await request.body()
            try:
                decompressed_body = gzip.decompress(body)
            except Exception:
                return Response("Invalid gzip compressed data", status_code=400)

            # Replace the request's receive function to return the decompressed body.
            async def receive():
                return {
                    "type": "http.request",
                    "body": decompressed_body,
                    "more_body": False,
                }

            request._receive = receive  # Overwrite the internal receive function.

            # Remove the Content-Encoding header from the scope.
            new_headers = [
                (k, v)
                for k, v in request.scope["headers"]
                if k.lower() != b"content-encoding"
            ]
            request.scope["headers"] = new_headers

        response = await call_next(request)
        return response
