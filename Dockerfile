FROM python:3.12.9-slim-bookworm

ARG DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1 \
    USERNAME=nonroot \
    USER_UID=1000 \
    USER_GID=1000

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    VIRTUAL_ENV=/app/analytics/.venv 

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && \
    apt-get install -y --no-install-recommends \
    curl=7.88.* \ 
    gnupg=2.2.* \ 
    && \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    gcc=4:12.2.* \
    azure-cli=2.45.* \  
    && \
    apt-get remove curl -y && \
    apt-get autoremove -y && \
    groupadd --gid $USER_GID $USERNAME && \ 
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    rm -rf /var/lib/apt/lists/*

# Copy the project files and the shared library
WORKDIR /app
COPY backend_analytics ./analytics/
COPY backend_shared ./backend_shared/

# Switch to the project directory for correct path resolution
# and install all the dependencies including the shared library
WORKDIR /app/analytics
RUN pip install poetry==2.1.1 --no-cache-dir && \
    poetry install --no-interaction --no-ansi --no-root && \
    chown -R $USER_UID:$USER_GID /app

# Add the virtual environment of the project to the PATH
ENV PATH="/app/analytics/.venv/bin:$PATH"

EXPOSE 8000

USER $USERNAME

CMD ["uvicorn", "analytics.main:app", "--host", "0.0.0.0", "--port", "8000"]
