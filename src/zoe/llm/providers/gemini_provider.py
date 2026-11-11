"""Gemini LLM Provider implementation using HTTPX."""

from typing import Any, Dict, List, Optional
import httpx

from zoe.utils.logging import get_logger

logger = get_logger("zoe.llm.providers.gemini")


class GeminiProvider:
    """Fallback LLM provider calling Google Gemini REST API."""

    name: str = "gemini"
    DEFAULT_MODEL: str = "gemini-1.5-flash"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        timeout_seconds: float = 30.0,
        client: Optional[httpx.Client] = None,
    ):
        if not api_key:
            raise ValueError("Gemini API key cannot be empty")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = client

    def _get_client(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        return httpx.Client(timeout=self.timeout_seconds)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """Call Gemini generateContent endpoint."""
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        headers = {"Content-Type": "application/json"}
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": system_prompt}],
            }

        client = self._get_client()
        try:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 401 or resp.status_code == 403:
                raise RuntimeError("Gemini API authentication failed.")
            if resp.status_code == 429:
                raise RuntimeError("Gemini API rate limit exceeded.")
            resp.raise_for_status()

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini returned no candidates.")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return ""
            return parts[0].get("text", "").strip()

        except httpx.TimeoutException as e:
            logger.error("Gemini request timed out after %.1fs: %s", self.timeout_seconds, str(e))
            raise TimeoutError(f"Gemini API call timed out: {e}") from e
        except Exception as e:
            logger.error("Gemini provider error: %s", str(e))
            raise

    def classify(self, text: str, categories: List[str], **kwargs: Any) -> str:
        """Classify message text into one of the designated categories."""
        cats_str = ", ".join(f"'{c}'" for c in categories)
        sys_prompt = (
            f"Classify the text into exactly one of: [{cats_str}]. "
            f"Output ONLY the category name."
        )
        resp = self.generate(sys_prompt, text, temperature=0.0, max_tokens=16)
        cleaned = resp.strip().lower().strip("'\"")
        for cat in categories:
            if cat.lower() == cleaned or cat.lower() in cleaned:
                return cat
        return categories[0] if categories else "casual"

