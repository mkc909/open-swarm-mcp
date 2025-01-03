import pytest
from unittest.mock import patch, Mock
from swarm.extensions.llm.openai_provider import OpenAIProvider

@pytest.fixture
def openai_provider():
    """Fixture to provide a mock-configured OpenAIProvider instance."""
    config = {
        "api_key": "test_api_key",
        "model": "gpt-4",
        "base_url": "https://api.openai.com/v1",
        "temperature": 0.7,
    }
    return OpenAIProvider(config)

@patch("swarm.extensions.llm.openai_provider.requests.post")
def test_generate_success(mock_post, openai_provider):
    """Test the generate method for successful API response."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Mocked response"}}]
    }
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    prompt = "Hello, OpenAI!"
    response = openai_provider.generate(prompt)
    assert response == "Mocked response", "Generated response mismatch"

@patch("swarm.extensions.llm.openai_provider.requests.post")
def test_generate_failure(mock_post, openai_provider):
    """Test the generate method for API failure."""
    mock_post.side_effect = Exception("API request failed")

    prompt = "Hello, OpenAI!"
    with pytest.raises(RuntimeError, match="Failed to generate response:"):
        openai_provider.generate(prompt)
