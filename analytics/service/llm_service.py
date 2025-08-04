from anthropic import AsyncAnthropic
from openai import (
    AsyncAzureOpenAI,
    AsyncOpenAI,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from analytics.config import settings

# Currently supported models
models = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        "gpt-4.5-preview",
        "gpt-4.1",
        "o4-mini",
        "o3",
    ],
    "azure": [
        f"{settings.AZURE_RESOURCE_PREFIX}-gpt-4o",
        f"{settings.AZURE_RESOURCE_PREFIX}-gpt-4o-mini",
    ],
    "leviathan": ["llama3.3:70b", "gemma3:27b", "deepseek-r1:32b", "qwq:latest"],
    "anthropic": [
        "claude-3-7-sonnet-20250219",
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
    ],
    "google": [
        "gemini-2.0-flash",
    ],
}


# API call to the LLMs
@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(RateLimitError),
)
async def basic_chat(
    message, temperature, model=f"{settings.AZURE_RESOURCE_PREFIX}-gpt-4o"
):
    for key, value in models.items():
        if model in value:
            if key == "anthropic":
                client = AsyncAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY,
                )

                message = await client.messages.create(
                    model=model,
                    max_tokens=4000,
                    temperature=temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": message,
                        }
                    ],
                )

                return message.content[0].text

            else:
                if key == "openai":
                    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                elif key == "leviathan":
                    client = AsyncOpenAI(
                        base_url=settings.LEVIATHAN_ENDPOINT,
                        api_key="ollama",
                    )
                elif key == "google":
                    client = AsyncOpenAI(
                        base_url=settings.GOOGLE_ENDPOINT,
                        api_key=settings.GOOGLE_API_KEY,
                    )
                else:
                    client = AsyncAzureOpenAI(
                        azure_endpoint=settings.AZURE_OPENAI_CHAT_ENDPOINT,
                        api_key=settings.AZURE_OPENAI_API_KEY,
                        api_version="2024-02-15-preview",
                    )

                if model == "o4-mini" or model == "o3":
                    temperature = 1

                completion = await client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=[{"role": "user", "content": message}],
                )

                return completion.choices[0].message.content
