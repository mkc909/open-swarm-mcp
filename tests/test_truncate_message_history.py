import os
import unittest
import tiktoken
from src.swarm.core import truncate_message_history

class TestTruncateMessageHistory(unittest.TestCase):
    def setUp(self):
        # Set a small maximum token limit for testing
        os.environ["MAX_OUTPUT"] = "30"

    def test_truncate_history(self):
        model = "gpt-3.5-turbo"
        try:
            encoding = tiktoken.encoding_for_model(model)
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")
        # Create a message with content that will exceed the max tokens.
        # "a " repeated 100 times
        long_message = {"content": "a " * 100}
        short_message = {"content": "short"}
        messages = [long_message, short_message]
        
        # Call truncate_message_history on a copy of messages
        truncated = truncate_message_history(messages.copy(), model)
        total_tokens = sum(len(encoding.encode(msg.get("content", ""))) for msg in truncated)
        # Assert that total token count is within the limit
        self.assertLessEqual(total_tokens, 30)

    def test_no_truncation_needed(self):
        model = "gpt-3.5-turbo"
        messages = [{"content": "hello"}, {"content": "world"}]
        truncated = truncate_message_history(messages.copy(), model)
        # When messages already within token limit, the history should remain unchanged.
        self.assertEqual(truncated, messages)

if __name__ == "__main__":
    unittest.main()