import os
import unittest
from pydantic import ValidationError
from main import AssistantChatRequest
from test_rate_limiter import test_multi_ip_rate_limiting
from test_tenant_isolation import test_tenant_isolation
import asyncio

class TestBackendOfflineSuite(unittest.TestCase):
    def test_pydantic_chat_query_bounds(self):
        """Verifies 1 to 500 character bounds on AssistantChatRequest."""
        # Empty query
        with self.assertRaises(ValidationError):
            AssistantChatRequest(query="")
        # Query exceeding 500 characters
        with self.assertRaises(ValidationError):
            AssistantChatRequest(query="a" * 501)
        # Valid query
        valid = AssistantChatRequest(query="What is the forecast for baguettes?")
        self.assertEqual(valid.query, "What is the forecast for baguettes?")
        print("[OK] Pydantic query length constraints validated.")

    def test_rate_limiter_isolated_counters(self):
        """Verifies independent counters for different client IPs behind proxies."""
        asyncio.run(test_multi_ip_rate_limiting())

    def test_multi_tenant_isolation_suite(self):
        """Verifies zero data leakage between tenants."""
        test_tenant_isolation()

    def test_gemini_or_skip_marker(self):
        """Runs Gemini test if key present, else prints explicit skip marker."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or "AIzaSy" not in api_key and not api_key.startswith("AQ."):
            print("[CI SKIP] GEMINI_API_KEY not configured or placeholder. Skipping live GenAI network test.")
        else:
            from verify_llm import test_llm_integration
            test_llm_integration()

if __name__ == "__main__":
    unittest.main()
