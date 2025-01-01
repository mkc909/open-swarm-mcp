# src/open_swarm_mcp/llm_providers/mock_llm.py

class MockLLMProvider:
    def __init__(self, model, api_key=None, **kwargs):
        self.model = model
        self.api_key = api_key

    def chat_completion(self, messages, **kwargs):
        """
        Simulates the chat completion response from an LLM provider.
        """
        return {
            'id': 'mock-id',
            'object': 'chat.completion',
            'created': 0,
            'model': self.model,
            'choices': [
                {
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': "This is a mocked response."
                    },
                    'finish_reason': 'stop'
                }
            ],
            'usage': {
                'prompt_tokens': 10,
                'completion_tokens': 20,
                'total_tokens': 30
            }
        }
