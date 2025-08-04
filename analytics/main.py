import os
import sys

# Hold the functions hand to the right folder so that imports work consistantly
project_root = os.path.abspath(os.path.join(__file__, "../.."))
sys.path.append(str(project_root))

from asgi_correlation_id import CorrelationIdMiddleware

# === imports for middleware ===
# Built-in middleware imports from FastAPI/Starlette:
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# from pydantic import TypeAdapter
from analytics.api.analysis_router import analysis_router
from analytics.app_init import app

# === imports from service, analytics, and api ===
from analytics.config import settings
from analytics.custom_logging import logger, setup_logging
from analytics.middleware.cache_control import NoCacheMiddleware

# Import custom middleware from our middleware package:

# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.responses import Response

setup_logging(json_logs=settings.LOG_JSON_FORMAT, log_level="INFO")

app.include_router(analysis_router)

# === Middleware starts ===
# The order of the middleware is important. The first middleware in the list is the outermost middleware, and the last middleware is the innermost middleware.

# Do we need to accept GZip requests?
# app.add_middleware(GZipDecompressMiddleware)

# # Logging middleware, if the LOG_FILE is not devined
# app.add_middleware(
#     SimpleLoggingMiddleware, server_short_name="DAIN-Logger", log_file=settings.LOG_FILE
# )

# API Key Authentication middleware
# if settings.API_KEY is not None:
#     app.add_middleware(APIKeyAuthMiddleware, expected_api_key=settings.API_KEY)

# # Custom Server Header middleware
# app.add_middleware(CustomHeaderMiddleware, server_name=settings.SERVER_NAME)

# No-Cache middleware for dynamic responses
app.add_middleware(NoCacheMiddleware)

# Security Headers middleware, currently prevents Swagger UI from working
# app.add_middleware(SecurityHeadersMiddleware)


origins = [
    f"https://{settings.PREFIX}-ca-frontend-{settings.ENVIRONMENT}.{settings.ACI_DOMAIN}",
    f"https://{settings.PREFIX}-ca-backend-analytics-{settings.ENVIRONMENT}.{settings.ACI_DOMAIN}",
]

# allow local connections to dev environment
if settings.ENVIRONMENT == "dev":
    origins.extend(["http://localhost", "http://localhost:3000"])

# allow all origins if it is deplyoed to local
if settings.ENVIRONMENT == "local":
    origins = ["*"]

# CORS: Adjust allowed_origins as needed for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID: Middleware to add a unique ID to each request for tracking.
app.add_middleware(CorrelationIdMiddleware)

# GZip: Compress responses larger than 1KB.
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted Hosts: Specify allowed hosts (use proper domain names in production).
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Origins: {origins}")


# # === Middleware ends ===

# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(
#         "analytics.main:app",
#         host="127.0.0.1",
#         port=8000,
#         reload=False,
#         server_header=False,
#     )  # we want to use our own server header
