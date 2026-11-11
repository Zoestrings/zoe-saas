-- Community Memory Database Schema

CREATE TABLE IF NOT EXISTS community_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    telegram_message_id INTEGER NOT NULL,
    pseudonymous_user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    received_at TEXT NOT NULL,
    summarized_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_community_messages_lookup
    ON community_messages(project_id, group_id, received_at);

CREATE INDEX IF NOT EXISTS idx_community_messages_summarized
    ON community_messages(project_id, group_id, summarized_at);

CREATE TABLE IF NOT EXISTS community_memory_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_community_memory_summaries_period
    ON community_memory_summaries(project_id, group_id, period_start, period_end);

