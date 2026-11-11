class ZoeError(Exception):
    """Base exception for all Zoe Intelligence Engine errors."""
    pass


class ConfigError(ZoeError):
    """Raised when configuration or secrets validation fails."""
    pass


class TelegramError(ZoeError):
    """Base exception for Telegram adapter and ingestion errors."""
    pass


class ChatMigrationAlert(TelegramError):
    """Raised when Telegram reports migrate_to_chat_id."""
    pass


class BotRemovedAlert(TelegramError):
    """Raised when the bot is removed from a group or receives 403 Forbidden."""
    pass


class PollingGapAlert(TelegramError):
    """Raised when a gap in update IDs is detected."""
    pass


class InvalidTransitionError(ZoeError):
    """Raised when an illegal state transition is attempted on inbox or outbox."""
    pass


class ProviderNotApprovedError(ZoeError):
    """Raised when routing sensitive data to an unapproved LLM provider."""
    pass

