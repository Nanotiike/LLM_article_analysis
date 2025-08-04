from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings."""

    # # === Variables for server configuration ===
    # load_dotenv()
    # SERVER_NAME: str = "DAIN Studios, ArticleDB, Article Analyzer v0.1"
    # SERVER_NAME_FOR_LOGGING: str = "ArticleAnalyzer"
    # API_KEY: str | None = os.getenv(
    #     "API_KEY", None
    # )  # curl -i -H "X-API-Key: foo" http://127.0.0.1:8000/ping
    # LOG_FILE: str | None = os.getenv(
    #     "LOG_FILE", None
    # )  # if it does not exist, then stdout is used

    PROJECT_NAME: str = "analytics"
    DEBUG: bool = True
    ENVIRONMENT: str = "local"
    PREFIX: str = "ark"
    ACI_DOMAIN: str = ""
    LOG_JSON_FORMAT: bool = False

    # Azure Resources
    AZURE_RESOURCE_PREFIX: str = "ark"
    AZURE_OPENAI_CHAT_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    KEY_VAULT_ENDPOINT: str = ""

    # Other LLM settings
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LEVIATHAN_ENDPOINT: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_ENDPOINT: str = ""
    EXCEL_PATH: str = ""

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
