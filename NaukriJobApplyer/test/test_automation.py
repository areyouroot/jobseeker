"""
=============================================================
  Test: LLM Client & Automated Job Applier Logic
=============================================================
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.llm_client import LLMClient
from src.automation.job_applier import JobApplier


class TestLLMClientParsing(unittest.TestCase):
    """Verify that LLMClient parses keywords from various LLM response formats."""

    def setUp(self):
        self.client = LLMClient(llm_url="http://localhost:5678/webhook/chat", log_fn=MagicMock())

    def test_parse_clean_json_array(self):
        raw = '["C# Developer", ".NET Software Engineer"]'
        keywords = self.client._parse_keywords(raw)
        self.assertEqual(keywords, ["C# Developer", ".NET Software Engineer"])

    def test_parse_json_dict_response(self):
        raw = '{"response": ["C#", ".NET"]}'
        keywords = self.client._parse_keywords(raw)
        self.assertEqual(keywords, ["C#", ".NET"])

    def test_parse_json_dict_text(self):
        raw = '{"text": "[\\"C# Developer\\", \\".NET Developer\\"]"}'
        keywords = self.client._parse_keywords(raw)
        self.assertEqual(keywords, ["C# Developer", ".NET Developer"])

    def test_parse_markdown_wrapped_array(self):
        raw = 'Here is the list:\n```json\n["C#", "ASP.NET"]\n```\nHope it helps!'
        keywords = self.client._parse_keywords(raw)
        self.assertEqual(keywords, ["C#", "ASP.NET"])

    def test_parse_plain_text_numbered_list(self):
        raw = "1. C# Developer\n2. .NET Engineer\n3. SQL Database Administrator"
        keywords = self.client._parse_keywords(raw)
        self.assertEqual(keywords, ["C# Developer", ".NET Engineer", "SQL Database Administrator"])

    def test_parse_plain_text_bullet_list(self):
        raw = "- ASP.NET Core MVC\n* Azure Developer"
        keywords = self.client._parse_keywords(raw)
        self.assertEqual(keywords, ["ASP.NET Core MVC", "Azure Developer"])


class TestJobApplierLogic(unittest.TestCase):
    """Test job search limits, delays, and flow control on mock pages."""

    @patch("src.automation.job_applier.time.sleep")
    def test_apply_limits_and_delays(self, mock_sleep):
        mock_page = MagicMock()
        mock_bot = MagicMock()
        mock_bot.is_configured = True

        # Mock page locator count to simulate finding 5 jobs
        mock_locator = MagicMock()
        mock_locator.count.return_value = 5
        mock_locator.nth.return_value.get_attribute.side_effect = [
            "/job-description/1",
            "/job-description/2",
            "/job-description/3",
            "/job-description/4",
            "/job-description/5"
        ]
        mock_page.locator.return_value = mock_locator

        applier = JobApplier(
            page=mock_page,
            telegram_bot=mock_bot,
            apply_delay=30,
            timeout=1000,
            log_fn=MagicMock()
        )

        # Mock apply single job method to simulate successes
        applier._apply_single_job = MagicMock()

        applier.apply_for_jobs(["C#"])

        # Should limit successes to exactly 3 for the keyword
        self.assertEqual(applier._apply_single_job.call_count, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
