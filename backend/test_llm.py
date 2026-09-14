import json
import unittest
from unittest.mock import AsyncMock, patch

from app.services.llm_service import choose_weather_tool


class LLMRoutingTests(unittest.IsolatedAsyncioTestCase):

    @patch("app.services.llm_service.ask_llm", new_callable=AsyncMock)
    async def test_weather_tool_routing(self, mock_ask_llm):
        mock_ask_llm.return_value = json.dumps({
            "tool": "forecast"
        })

        result = await choose_weather_tool(
            "Will it rain tomorrow in Mumbai?"
        )

        self.assertEqual(result["tool"], "forecast")
        mock_ask_llm.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()