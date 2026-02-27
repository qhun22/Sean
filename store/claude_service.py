import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-3-haiku-20240307"
DEFAULT_MAX_TOKENS = 400
REQUEST_TIMEOUT = 15


class ClaudeService:
    """Gọi Claude API (claude-3-haiku) với kiểm soát chi phí."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY chưa được cấu hình trong .env")

    def call(self, system_prompt: str, user_message: str, max_tokens: int = DEFAULT_MAX_TOKENS):
        if not self.api_key:
            logger.error("Thiếu ANTHROPIC_API_KEY")
            return None

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": CLAUDE_MODEL,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }

        try:
            resp = requests.post(
                CLAUDE_API_URL,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if resp.status_code != 200:
                logger.error("Claude API lỗi %s: %s", resp.status_code, resp.text[:300])
                return None

            data = resp.json()
            content_blocks = data.get("content", [])
            if content_blocks:
                return content_blocks[0].get("text", "")
            return None

        except requests.exceptions.Timeout:
            logger.error("Claude API timeout sau %ss", REQUEST_TIMEOUT)
            return None
        except Exception as exc:
            logger.error("Claude API exception: %s", exc)
            return None
