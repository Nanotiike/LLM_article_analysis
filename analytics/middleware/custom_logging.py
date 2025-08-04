import logging
import os
import time

from starlette.middleware.base import BaseHTTPMiddleware


class SimpleLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Logs the request method, URL, response status code, and processing time.
    By default, logs are sent to stdout. If a log_file is provided or if a LOG_FILE
    environment variable is defined, logs will be written to that file.

    Parameters:
        server_short_name (str): A short name for the server, used as the logger name.
        log_file (str, optional): File path to write logs to. If not provided,
            the middleware checks for the LOG_FILE environment variable.
            If neither is provided, logs will be output to stdout.
    """

    def __init__(self, app, server_short_name: str, log_file: str = None, **kwargs):
        super().__init__(app)
        # If no log_file provided, check the environment variable.
        if log_file is None:
            log_file = os.getenv("LOG_FILE")

        # Create a logger with the provided server short name.
        self.logger = logging.getLogger(server_short_name)
        self.logger.setLevel(logging.INFO)

        # Clear any existing handlers to avoid duplicate logs.
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Define the log format.
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Use a FileHandler if a log file is defined, otherwise use a StreamHandler (stdout).
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        self.logger.info(
            "%s %s - %s in %.2fs",
            request.method,
            request.url,
            response.status_code,
            duration,
        )
        return response
