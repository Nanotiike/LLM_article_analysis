import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from openai import RateLimitError

# Hold the functions hand to the right folder so that imports work consistantly
project_root = os.path.abspath(os.path.join(__file__, "../.."))
sys.path.append(str(project_root))

from backend_analytics.analytics.service.llm_service import basic_chat


# Test the basic_chat function
@pytest.mark.asyncio(loop_scope="session")
async def test_basic_chat():
    result = await basic_chat(
        "What is 2+12? Give only the final result of the equation", 0
    )
    assert result == "14"


models = ["gemini-2.0-flash", "gpt-4.1"]


# Test the basic_chat function with all the models
@pytest.mark.asyncio(loop_scope="session")
async def test_basic_chat_models():
    for model in models:
        print(model)
        result = await basic_chat(
            "What is 2+12? Give only the final result of the equation", 1, model=model
        )
        print(result)
        assert result != ""


# Test the retry functionality of basic_chat
@pytest.mark.asyncio(loop_scope="session")
async def test_basic_chat_retry():
    # Create a mock for the AsyncAzureOpenAI client
    mock_client = MagicMock()

    # Create a mock for the chat.completions.create method
    mock_create = MagicMock()
    mock_client.chat.completions.create = mock_create

    # Set up the side effects: first 3 calls raise RateLimitError, then succeed
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "14"

    # Define a side effect function that raises RateLimitError 3 times then succeeds
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 3:
            # Create a proper RateLimitError with all required parameters
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 429
            mock_response_obj.headers = {"retry-after": "2"}

            error_body = {
                "error": {
                    "message": "Rate limit exceeded",
                    "type": "rate_limit_error",
                    "param": None,
                    "code": "rate_limit",
                }
            }

            raise RateLimitError(
                message="Rate limit exceeded",
                response=mock_response_obj,
                body=error_body,
            )
        return mock_response

    mock_create.side_effect = side_effect

    # Patch the AsyncAzureOpenAI class to return our mock client
    with patch(
        "backend_analytics.analytics.service.llm_service.AsyncAzureOpenAI",
        return_value=mock_client,
    ):
        # Call the function that should retry
        result = await basic_chat(
            "What is 2+12? Give only the final result of the equation", 0
        )

        # Assert the result is correct
        assert result == "14"

        # Assert that the create method was called 4 times (3 failures + 1 success)
        assert call_count == 4
