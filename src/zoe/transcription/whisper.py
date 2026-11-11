"""Audio transcription service using Groq Whisper API (whisper-large-v3)."""

import asyncio
import os
from pathlib import Path
from typing import Any, Optional

from zoe.utils.logging import get_logger

logger = get_logger("zoe.transcription.whisper")


def transcribe_audio_file(
    file_path: Path,
    api_key: Optional[str] = None,
    client: Optional[Any] = None,
    model: str = "whisper-large-v3",
) -> str:
    """Transcribe an audio file using Groq's whisper-large-v3 model.

    Args:
        file_path: Path to the audio file on disk (.ogg, .mp3, etc.)
        api_key: Optional Groq API key (defaults to GROQ_API_KEY env var)
        client: Optional custom/mock Groq client
        model: Model identifier (default: whisper-large-v3)

    Returns:
        Transcribed text string.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Check for provided custom or mock client
    if client is not None:
        if hasattr(client, "audio") and hasattr(client.audio, "transcriptions"):
            with open(path, "rb") as f:
                res = client.audio.transcriptions.create(
                    file=(path.name, f.read()),
                    model=model,
                    response_format="text",
                )
            if hasattr(res, "text"):
                return str(res.text).strip()
            return str(res).strip()
        elif callable(client):
            return str(client(path)).strip()

    groq_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY must be set for Groq Whisper transcription.")

    from groq import Groq

    groq_client = Groq(api_key=groq_api_key)
    with open(path, "rb") as f:
        res = groq_client.audio.transcriptions.create(
            file=(path.name, f.read()),
            model=model,
            response_format="text",
        )
    if hasattr(res, "text"):
        return str(res.text).strip()
    return str(res).strip()


async def transcribe_audio_file_async(
    file_path: Path,
    api_key: Optional[str] = None,
    client: Optional[Any] = None,
    model: str = "whisper-large-v3",
) -> str:
    """Async wrapper to transcribe an audio file in a thread pool."""
    return await asyncio.to_thread(transcribe_audio_file, file_path, api_key, client, model)

