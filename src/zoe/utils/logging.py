import contextvars
import logging
import re
import sys
import traceback
from typing import Any, Optional

# Standard LogRecord attribute names to distinguish custom extra fields
_STANDARD_LOGRECORD_ATTRS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "asctime"
}

_DIGIT_PATTERN = re.compile(r"\d{6,}")
_CURRENT_PROJECT: contextvars.ContextVar[str] = contextvars.ContextVar("_CURRENT_PROJECT", default="")


def set_current_project(project_id: str) -> None:
    """Set the active project_id for multi-tenant contextual logging."""
    _CURRENT_PROJECT.set(project_id)


def get_current_project() -> str:
    """Get the active project_id context."""
    return _CURRENT_PROJECT.get()


def redact_value(val: Any) -> Any:
    """Recursively redact any sequence of 6+ consecutive digits."""
    if isinstance(val, str):
        return _DIGIT_PATTERN.sub("[REDACTED]", val)
    elif isinstance(val, int):
        if len(str(abs(val))) >= 6:
            return "[REDACTED]"
        return val
    elif isinstance(val, dict):
        return {redact_value(k): redact_value(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [redact_value(item) for item in val]
    elif isinstance(val, tuple):
        return tuple(redact_value(item) for item in val)
    elif isinstance(val, set):
        return {redact_value(item) for item in val}
    return val


class SanitizingFormatter(logging.Formatter):
    """Formatter that scrubs sensitive data (6+ digit runs) and prepends [PROJECT_ID]."""

    def format(self, record: logging.LogRecord) -> str:
        # 1. Redact message text
        if isinstance(record.msg, str):
            record.msg = _DIGIT_PATTERN.sub("[REDACTED]", record.msg)

        # 2. Redact record.args
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(redact_value(arg) for arg in record.args)
            elif isinstance(record.args, dict):
                record.args = {k: redact_value(v) for k, v in record.args.items()}
            else:
                record.args = redact_value(record.args)

        # 3. Redact structured extra fields in record.__dict__
        for attr, val in list(record.__dict__.items()):
            if attr not in _STANDARD_LOGRECORD_ATTRS:
                setattr(record, attr, redact_value(val))

        # 4. Handle exc_info and chained exceptions
        if record.exc_info:
            exc_type, exc_val, exc_tb = record.exc_info
            if exc_val is not None:
                formatted_exc = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
                record.exc_text = _DIGIT_PATTERN.sub("[REDACTED]", formatted_exc)

        # 5. Handle preexisting exc_text
        if record.exc_text:
            record.exc_text = _DIGIT_PATTERN.sub("[REDACTED]", record.exc_text)

        # 6. Call standard format
        formatted_message = super().format(record)

        # Final safety scrub on formatted string
        scrubbed = _DIGIT_PATTERN.sub("[REDACTED]", formatted_message)

        # 7. Prepend [PROJECT_ID] for multi-tenant tracing
        project_id = getattr(record, "project_id", None) or _CURRENT_PROJECT.get()
        if project_id:
            return f"[{project_id}] {scrubbed}"
        return scrubbed


def get_logger(name: str = "zoe") -> logging.Logger:
    """Return a logger configured with SanitizingFormatter."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = SanitizingFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
