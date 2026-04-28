import os
import json
import logging
import time
import hashlib
import requests

logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 700
REQUEST_TIMEOUT = 15

# ── Response caching để giảm API calls ───────────────────────────────────
_RESPONSE_CACHE: dict[str, tuple[str, float]] = {}
_CACHE_TTL_SEC = 5 * 60  # 5 phút cache


class ClaudeService:
    """Gọi Claude API (claude-3-haiku) với kiểm soát chi phí."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY chưa được cấu hình trong .env")

    def _get_cache_key(self, user_message: str, system_prompt: str) -> str:
        """Tạo cache key từ message và prompt."""
        key_str = f"{system_prompt[:200]}|{user_message}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> str | None:
        """Lấy response từ cache nếu còn hạn."""
        if cache_key in _RESPONSE_CACHE:
            response, timestamp = _RESPONSE_CACHE[cache_key]
            if time.time() - timestamp < _CACHE_TTL_SEC:
                return response
            else:
                del _RESPONSE_CACHE[cache_key]
        return None

    def _set_cached_response(self, cache_key: str, response: str) -> None:
        """Lưu response vào cache."""
        _RESPONSE_CACHE[cache_key] = (response, time.time())
        # Giới hạn cache size
        if len(_RESPONSE_CACHE) > 500:
            oldest_keys = sorted(_RESPONSE_CACHE.items(), key=lambda x: x[1][1])[:100]
            for k in oldest_keys:
                del _RESPONSE_CACHE[k[0]]

    def _call_once(self, payload: dict, headers: dict) -> dict | None:
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
            return resp.json()
        except requests.exceptions.Timeout:
            logger.error("Claude API timeout sau %ss", REQUEST_TIMEOUT)
            return None
        except Exception as exc:
            logger.error("Claude API exception: %s", exc)
            return None

    @staticmethod
    def _extract_text_blocks(data: dict) -> str:
        content_blocks = data.get("content", []) or []
        texts = [blk.get("text", "") for blk in content_blocks if isinstance(blk, dict) and blk.get("type") == "text"]
        return "\n".join(t.strip() for t in texts if t and t.strip()).strip()

    def call(self, system_prompt: str, user_message: str, max_tokens: int = DEFAULT_MAX_TOKENS):
        if not self.api_key:
            logger.error("Thiếu ANTHROPIC_API_KEY")
            return None

        # Kiểm tra cache trước
        cache_key = self._get_cache_key(user_message, system_prompt)
        cached = self._get_cached_response(cache_key)
        if cached:
            logger.debug("Cache hit for: %s", user_message[:50])
            return cached

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        messages = [{"role": "user", "content": user_message}]
        answer_parts: list[str] = []

        # Cho phép nối nhiều nhịp để tránh câu trả lời bị cắt giữa chừng vì max_tokens.
        for _ in range(4):
            payload = {
                "model": CLAUDE_MODEL,
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": messages,
            }

            data = self._call_once(payload, headers)
            if not data:
                break

            chunk = self._extract_text_blocks(data)
            if chunk:
                answer_parts.append(chunk)

            stop_reason = data.get("stop_reason")
            if stop_reason != "max_tokens":
                break

            messages.append({"role": "assistant", "content": chunk or ""})
            messages.append({
                "role": "user",
                "content": "Tiếp tục đúng phần còn dang dở của câu trả lời trước đó, không lặp lại ý đã nói.",
            })

        final_answer = "\n".join(part for part in answer_parts if part).strip()

        # Lưu vào cache
        if final_answer:
            self._set_cached_response(cache_key, final_answer)

        return final_answer or None
