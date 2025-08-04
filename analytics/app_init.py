from fastapi import FastAPI

app = FastAPI(
    title="Arkistokanta - Analytics API",
    redoc_url=None,
    docs_url="/docs",  # settings.API_DOCS
    version="0.1.0",
)
