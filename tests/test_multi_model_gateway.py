import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llm_client import LLMProvider
from multi_model_gateway import MultiModelGateway


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"model": "llama-test", "response": "Yerel taslak"}


class FakeCloudClient:
    clients = {LLMProvider.GROQ: object()}

    def __init__(self, result=None):
        self.result = result or {
            "content": "Groq taslağı",
            "provider": "groq",
            "model": "test-model",
            "error": None,
        }
        self.last_provider = None

    def is_configured(self):
        return True

    def get_available_providers(self):
        return ["groq"]

    def generate_content(self, prompt, provider=None):
        self.last_provider = provider
        return self.result


class MultiModelGatewayTests(unittest.TestCase):
    def test_ast_task_stays_local_and_reports_real_structure(self):
        gateway = MultiModelGateway()
        with patch("multi_model_gateway.requests.post", side_effect=AssertionError("network used")):
            result = gateway.akilli_yonlendir("kod_ast_analizi", "class A:\n    pass\n")

        self.assertEqual(result["secilen_saglayici"], "local_ast")
        self.assertTrue(result["icerik"]["syntax_valid"])
        self.assertEqual(result["icerik"]["classes"], ["A"])
        self.assertFalse(result["bulut_izni"])

    def test_local_ollama_is_used_by_default(self):
        gateway = MultiModelGateway()
        with patch("multi_model_gateway.requests.post", return_value=FakeResponse()) as request:
            result = gateway.akilli_yonlendir("genel", "test prompt")

        self.assertEqual(result["secilen_saglayici"], "ollama")
        self.assertEqual(result["icerik"], "Yerel taslak")
        self.assertFalse(result["bulut_izni"])
        self.assertEqual(request.call_args.kwargs["json"]["model"], "llama3.2")

    def test_fast_hook_uses_groq_only_after_cloud_opt_in(self):
        client = FakeCloudClient()
        gateway = MultiModelGateway(llm_client=client)

        result = gateway.akilli_yonlendir("hizli_kanca", "hook prompt", allow_cloud=True)

        self.assertEqual(result["secilen_saglayici"], "groq")
        self.assertEqual(result["icerik"], "Groq taslağı")
        self.assertEqual(client.last_provider, LLMProvider.GROQ)

    def test_unavailable_providers_do_not_fabricate_success(self):
        client = Mock()
        client.is_configured.return_value = False
        client.get_available_providers.return_value = []
        gateway = MultiModelGateway(llm_client=client)
        with patch("multi_model_gateway.requests.post", side_effect=requests.ConnectionError):
            result = gateway.akilli_yonlendir("genel", "prompt")

        self.assertEqual(result["durum"], "unavailable")
        self.assertIsNone(result["icerik"])

    def test_external_ollama_endpoint_is_rejected(self):
        with self.assertRaises(ValueError):
            MultiModelGateway(ollama_url="https://example.com")


if __name__ == "__main__":
    unittest.main()