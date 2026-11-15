"""Model loader for official knowledge embeddings with singleton enforcement."""

import asyncio
import os
import threading
from typing import Any, Optional

from zoe.utils.logging import get_logger

logger = get_logger("zoe.knowledge.model")

_MODEL: Optional[Any] = None
_LOCK = threading.Lock()


def is_model_ready() -> bool:
    """Check if the shared singleton embedding model is loaded in memory."""
    global _MODEL
    return _MODEL is not None


def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> Any:
    """Load and return the sentence transformer embedding model (cached singleton).
    
    Guarantees only a single copy (~500MB RAM) is loaded across all projects,
    preventing Out-Of-Memory (OOM) crashes on resource-constrained systems.
    Thread-safe: if background pre-warming is in progress, blocks until loading completes.
    """
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    with _LOCK:
        if _MODEL is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Initializing shared singleton embedding model '%s'...", model_name)
            try:
                _MODEL = SentenceTransformer(model_name, local_files_only=True)
            except Exception:
                _MODEL = SentenceTransformer(model_name)
            logger.info("Shared singleton embedding model ready.")
    return _MODEL


async def get_embedding_model_async(model_name: str = "all-MiniLM-L6-v2") -> Any:
    """Asynchronously wait for the embedding model to load without blocking the event loop."""
    return await asyncio.to_thread(get_embedding_model, model_name)


def prewarm_model(model_name: str = "all-MiniLM-L6-v2") -> Any:
    """Pre-warm the shared embedding model singleton at application boot."""
    return get_embedding_model(model_name)

