import pytest
from swarm.extensions.llm.mock_llm import MockLLMProvider

@pytest.fixture
def mock_llm():
    """Fixture to provide an instance of MockLLMProvider."""
    return MockLLMProvider(model="mock_model")

def test_mock_llm_chat_completion(mock_llm):
    """Test chat completion response of the MockLLMProvider."""
    messages = [{"role": "user", "content": "Hello"}]
    response = mock_llm.chat_completion(messages)
    assert response["model"] == "mock_model", "Model name mismatch"
    assert response["choices"][0]["message"]["content"] == "This is a mocked response.", "Response content mismatch"
