import pytest
from swarm.extensions.llm.base_llm_provider import BaseLLMProvider

class MockLLM(BaseLLMProvider):
    """Mock implementation of BaseLLMProvider for testing."""
    def get_model_info(self):
        return {"name": "Mock Model", "version": "1.0"}

    def generate_response(self, prompt: str):
        return f"Mock response to: {prompt}"

    async def generate_response_async(self, prompt: str):
        return f"Mock async response to: {prompt}"

def test_base_llm_provider_abstract_methods():
    """Ensure unimplemented methods raise NotImplementedError."""
    with pytest.raises(TypeError):
        BaseLLMProvider()

def test_mock_llm_get_model_info():
    """Test the implementation of get_model_info."""
    mock_llm = MockLLM()
    info = mock_llm.get_model_info()
    assert info == {"name": "Mock Model", "version": "1.0"}, "Model info mismatch"

def test_mock_llm_generate_response():
    """Test the synchronous generate_response implementation."""
    mock_llm = MockLLM()
    prompt = "Test prompt"
    response = mock_llm.generate_response(prompt)
    assert response == "Mock response to: Test prompt", "Synchronous response mismatch"

@pytest.mark.asyncio
async def test_mock_llm_generate_response_async():
    """Test the asynchronous generate_response_async implementation."""
    mock_llm = MockLLM()
    prompt = "Test async prompt"
    response = await mock_llm.generate_response_async(prompt)
    assert response == "Mock async response to: Test async prompt", "Asynchronous response mismatch"
