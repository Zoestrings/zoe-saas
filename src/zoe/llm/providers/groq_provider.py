"""Groq LLM Provider implementation using HTTPX."""

import re
from typing import Any, Dict, List, Optional
import httpx

from zoe.llm.rate_limiter import get_global_rate_limiter
from zoe.utils.logging import get_logger

logger = get_logger("zoe.llm.providers.groq")


class GroqProvider:
    """LLM provider calling Groq Chat Completions API with sub-second latency."""

    name: str = "groq"
    DEFAULT_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    _WORKING_MODEL: Optional[str] = "qwen/qwen3.8-27b"

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-8b-instant",
        api_url: Optional[str] = None,
        timeout_seconds: float = 30.0,
        client: Optional[httpx.Client] = None,
    ):
        if not api_key:
            raise ValueError("Groq API key cannot be empty")
        self.api_key = api_key
        self.model = model
        self.api_url = api_url or self.DEFAULT_API_URL
        self.timeout_seconds = timeout_seconds
        self._client = client

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout_seconds)
        return self._client

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 100,
        **kwargs: Any,
    ) -> str:
        """Call Groq chat completions to generate response text with strict token caps."""
        # Hard limit of 250 tokens prevents overly long responses and Telegram timeouts
        is_technical = bool(
            kwargs.get("is_technical")
            or re.search(
                r"\b(?:code|python|solidity|contract|script|function|bug|traceback|syntax|deploy|debug|compile)\b",
                user_prompt,
                re.IGNORECASE,
            )
        )
        if is_technical:
            effective_max_tokens = min(int(max_tokens) if max_tokens else 250, 250)
        else:
            effective_max_tokens = min(int(max_tokens) if max_tokens else 100, 250)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        target_model = GroqProvider._WORKING_MODEL if GroqProvider._WORKING_MODEL else self.model

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": effective_max_tokens,
        }

        client = self._get_client()
        limiter = get_global_rate_limiter()
        try:
            with limiter:
                resp = client.post(self.api_url, json=payload, headers=headers)
            if resp.status_code == 404 and "model_not_found" in resp.text:
                logger.warning("Model '%s' not found on Groq; automatically falling back to 'qwen/qwen3.8-27b'", payload["model"])
                payload["model"] = "qwen/qwen3.8-27b"
                with limiter:
                    resp = client.post(self.api_url, json=payload, headers=headers)
                if resp.status_code == 404:
                    logger.warning("Model 'qwen/qwen3.8-27b' not found; falling back to 'openai/gpt-oss-120b'")
                    payload["model"] = "openai/gpt-oss-120b"
                    # For reasoning models, allocate extra headroom so completion tokens details doesn't exhaust reasoning
                    payload["max_tokens"] = max(effective_max_tokens, 250)
                    with limiter:
                        resp = client.post(self.api_url, json=payload, headers=headers)

            if resp.status_code == 200:
                # Cache the verified working model across all future calls
                GroqProvider._WORKING_MODEL = payload["model"]
                self.model = payload["model"]

            if resp.status_code == 401:
                raise RuntimeError("Groq API authentication failed: invalid API key.")
            if resp.status_code == 429:
                raise RuntimeError("Groq API rate limit exceeded.")
            resp.raise_for_status()

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("Groq returned empty choices.")

            msg_obj = choices[0].get("message", {})
            content = msg_obj.get("content", "")
            if not content and msg_obj.get("reasoning"):
                # If a reasoning model exhausted tokens in reasoning, extract the concluding sentence
                reasoning = msg_obj.get("reasoning", "")
                content = reasoning.split("\n")[-1] if reasoning else ""

            return content.strip()

        except httpx.TimeoutException as e:
            logger.error("Groq request timed out after %.1fs: %s", self.timeout_seconds, str(e))
            raise TimeoutError(f"Groq API call timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error("Groq HTTP error %d: %s", e.response.status_code, e.response.text)
            raise RuntimeError(f"Groq HTTP {e.response.status_code}: {e.response.text}") from e
        except Exception as e:
            logger.error("Groq provider unexpected failure: %s", str(e))
            raise

    def classify(self, text: str, categories: List[str], **kwargs: Any) -> str:
        """Classify message text into one of the designated categories."""
        cats_str = ", ".join(f"'{c}'" for c in categories)
        sys_prompt = (
            f"You are a text classification assistant. Classify the user text into exactly "
            f"one of the following categories: [{cats_str}]. "
            f"Return ONLY the exact category name and nothing else."
        )
        resp = self.generate(sys_prompt, text, temperature=0.0, max_tokens=16)
        cleaned = resp.strip().lower().strip("'\"")
        for cat in categories:
            if cat.lower() == cleaned or cat.lower() in cleaned:
                return cat
        return categories[0] if categories else "casual"

