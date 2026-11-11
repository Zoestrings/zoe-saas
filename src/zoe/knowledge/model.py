"""Model loader for official knowledge embeddings with singleton enforcement."""

import os
import threading
from typing import Any, Optional

from zoe.utils.logging import get_logger

logger = get_logger("zoe.knowledge.model")

_MODEL: Optional[Any] = None
_LOCK = threading.Lock()


def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> Any:
    """Load and return the sentence transformer embedding model (cached singleton).
    
    Guarantees only a single copy (~500MB RAM) is loaded across all projects,
    preventing Out-Of-Memory (OOM) crashes on resource-constrained systems.
    """
    global _MODEL
    if _MODEL is None:
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


def prewarm_model(model_name: str = "all-MiniLM-L6-v2") -> Any:
    """Pre-warm the shared embedding model singleton at application boot."""
    return get_embedding_model(model_name)
