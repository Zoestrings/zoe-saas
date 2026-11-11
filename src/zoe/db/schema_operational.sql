PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    telegram_group_id TEXT NOT NULL,
    config_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS polling_state (
    project_id TEXT PRIMARY KEY,
    last_persisted_update_id INTEGER NOT NULL DEFAULT 0,
    next_offset INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL,
    CHECK (next_offset = last_persisted_update_id + 1),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE IF NOT EXISTS update_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    telegram_update_id INTEGER NOT NULL,
    received_at TEXT NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'persisted',
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    UNIQUE (project_id, telegram_update_id)
);

CREATE TABLE IF NOT EXISTS inbox_messages (
    id INTEGER PRIMARY KEY,
    project_id TEXT NOT NULL,
    telegram_update_id INTEGER NOT NULL,
    group_id TEXT NOT NULL,
    telegram_message_id INTEGER NOT NULL,
    pseudonymous_user_id TEXT NOT NULL,
    text TEXT NOT NULL,
    reply_to_message_id INTEGER,
    is_forward INTEGER NOT NULL DEFAULT 0,
    message_timestamp TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN (
        'message_persisted','processing','no_response_required','response_pending',
        'response_sent','completed','failed','dead_letter','needs_investigation','escalated')),
    state_changed_at TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 5),
    next_attempt_at TEXT,
    lease_owner TEXT,
    lease_expires_at TEXT,
    classification_category TEXT,
    classification_confidence REAL,
    decision TEXT CHECK (decision IN ('respond','remain_silent','escalate','ignore')),
    decision_reason TEXT,
    failure_reason TEXT,
    investigation_reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    UNIQUE (project_id, telegram_update_id),
    UNIQUE (project_id, group_id, telegram_message_id)
);

CREATE INDEX IF NOT EXISTS idx_inbox_claimable
    ON inbox_messages(project_id, state, next_attempt_at);

CREATE TABLE IF NOT EXISTS participation_log (
    id INTEGER PRIMARY KEY,
    project_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    telegram_message_id INTEGER NOT NULL,
    decision TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY,
    project_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    trigger_message_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    safety_verdict TEXT NOT NULL,
    created_at TEXT NOT NULL,
    retention_delete_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    UNIQUE (project_id, group_id, trigger_message_id)
);

-- Stage 3 Tables
CREATE TABLE IF NOT EXISTS outbox_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    inbox_message_id INTEGER NOT NULL,
    group_id TEXT NOT NULL,
    reply_to_message_id INTEGER,
    text TEXT NOT NULL,
    simulated INTEGER NOT NULL CHECK (simulated IN (0, 1)),
    state TEXT NOT NULL CHECK (state IN ('pending', 'sending', 'sent', 'simulated_delivered', 'failed', 'dead_letter')),
    state_changed_at TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 5),
    lease_owner TEXT,
    lease_expires_at TEXT,
    next_attempt_at TEXT,
    sent_at TEXT,
    telegram_message_id INTEGER,
    error_message TEXT,
    created_at TEXT NOT NULL,
    inline_keyboard_json TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (inbox_message_id) REFERENCES inbox_messages(id),
    UNIQUE (project_id, inbox_message_id)
);

CREATE INDEX IF NOT EXISTS idx_outbox_claimable
    ON outbox_messages(project_id, state, next_attempt_at);

CREATE TABLE IF NOT EXISTS operator_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- Stage 3 Triggers (14 total)
-- 1. Simulated write-once trigger
CREATE TRIGGER IF NOT EXISTS trg_outbox_simulated_write_once
BEFORE UPDATE OF simulated ON outbox_messages
WHEN OLD.simulated != NEW.simulated
BEGIN
    SELECT RAISE(ABORT, 'simulated flag is write-once');
END;

-- 2. Outbox insert sent requires simulated=0
CREATE TRIGGER IF NOT EXISTS trg_outbox_insert_sent_requires_real
BEFORE INSERT ON outbox_messages
WHEN NEW.state = 'sent' AND NEW.simulated = 1
BEGIN
    SELECT RAISE(ABORT, 'state sent requires simulated=0');
END;

-- 3. Outbox update sent requires simulated=0
CREATE TRIGGER IF NOT EXISTS trg_outbox_update_sent_requires_real
BEFORE UPDATE OF state ON outbox_messages
WHEN NEW.state = 'sent' AND NEW.simulated = 1
BEGIN
    SELECT RAISE(ABORT, 'state sent requires simulated=0');
END;

-- 4. Outbox insert simulated_delivered requires simulated=1
CREATE TRIGGER IF NOT EXISTS trg_outbox_insert_simulated_delivered_requires_simulated
BEFORE INSERT ON outbox_messages
WHEN NEW.state = 'simulated_delivered' AND NEW.simulated = 0
BEGIN
    SELECT RAISE(ABORT, 'state simulated_delivered requires simulated=1');
END;

-- 5. Outbox update simulated_delivered requires simulated=1
CREATE TRIGGER IF NOT EXISTS trg_outbox_update_simulated_delivered_requires_simulated
BEFORE UPDATE OF state ON outbox_messages
WHEN NEW.state = 'simulated_delivered' AND NEW.simulated = 0
BEGIN
    SELECT RAISE(ABORT, 'state simulated_delivered requires simulated=1');
END;

-- 6. Terminal state outbox sent
CREATE TRIGGER IF NOT EXISTS trg_outbox_terminal_state_sent
BEFORE UPDATE OF state ON outbox_messages
WHEN OLD.state = 'sent'
BEGIN
    SELECT RAISE(ABORT, 'cannot transition out of terminal state sent');
END;

-- 7. Terminal state outbox simulated_delivered
CREATE TRIGGER IF NOT EXISTS trg_outbox_terminal_state_simulated_delivered
BEFORE UPDATE OF state ON outbox_messages
WHEN OLD.state = 'simulated_delivered'
BEGIN
    SELECT RAISE(ABORT, 'cannot transition out of terminal state simulated_delivered');
END;

-- 8. Terminal state outbox dead_letter
CREATE TRIGGER IF NOT EXISTS trg_outbox_terminal_state_dead_letter
BEFORE UPDATE OF state ON outbox_messages
WHEN OLD.state = 'dead_letter'
BEGIN
    SELECT RAISE(ABORT, 'cannot transition out of terminal state dead_letter');
END;

-- 9. Terminal state inbox completed
CREATE TRIGGER IF NOT EXISTS trg_inbox_terminal_state_completed
BEFORE UPDATE OF state ON inbox_messages
WHEN OLD.state = 'completed'
BEGIN
    SELECT RAISE(ABORT, 'cannot transition out of terminal state completed');
END;

-- 10. Terminal state inbox no_response_required
CREATE TRIGGER IF NOT EXISTS trg_inbox_terminal_state_no_response_required
BEFORE UPDATE OF state ON inbox_messages
WHEN OLD.state = 'no_response_required'
BEGIN
    SELECT RAISE(ABORT, 'cannot transition out of terminal state no_response_required');
END;

-- 11. Terminal state inbox dead_letter
CREATE TRIGGER IF NOT EXISTS trg_inbox_terminal_state_dead_letter
BEFORE UPDATE OF state ON inbox_messages
WHEN OLD.state = 'dead_letter'
BEGIN
    SELECT RAISE(ABORT, 'cannot transition out of terminal state dead_letter');
END;

-- 12. Inbox valid state transitions
CREATE TRIGGER IF NOT EXISTS trg_inbox_valid_transitions
BEFORE UPDATE OF state ON inbox_messages
WHEN NOT (
    (OLD.state = NEW.state) OR
    (OLD.state = 'message_persisted' AND NEW.state = 'processing') OR
    (OLD.state = 'failed' AND NEW.state = 'processing') OR
    (OLD.state = 'processing' AND NEW.state IN ('no_response_required', 'response_pending', 'failed', 'dead_letter', 'needs_investigation', 'escalated')) OR
    (OLD.state = 'response_pending' AND NEW.state IN ('response_sent', 'failed')) OR
    (OLD.state = 'response_sent' AND NEW.state IN ('completed', 'needs_investigation')) OR
    (OLD.state = 'needs_investigation' AND NEW.state = 'completed') OR
    (OLD.state = 'escalated' AND NEW.state IN ('completed', 'needs_investigation'))
)
BEGIN
    SELECT RAISE(ABORT, 'Invalid inbox_messages state transition');
END;

-- 13. Outbox valid state transitions
CREATE TRIGGER IF NOT EXISTS trg_outbox_valid_transitions
BEFORE UPDATE OF state ON outbox_messages
WHEN NOT (
    (OLD.state = 'pending' AND NEW.state = 'sending') OR
    (OLD.state = 'sending' AND NEW.state IN ('sent', 'simulated_delivered', 'failed')) OR
    (OLD.state = 'failed' AND NEW.state IN ('sending', 'dead_letter')) OR
    (OLD.state = 'sending' AND NEW.state = 'dead_letter')
)
BEGIN
    SELECT RAISE(ABORT, 'Invalid outbox_messages state transition');
END;

-- 14. Inbox attempt count cap trigger
CREATE TRIGGER IF NOT EXISTS trg_inbox_attempt_count_cap
BEFORE UPDATE OF attempt_count ON inbox_messages
WHEN NEW.attempt_count > 5
BEGIN
    SELECT RAISE(ABORT, 'attempt_count cannot exceed 5');
END;

-- Stage 7 Tables: Escalations and Moderator Notifications

CREATE TABLE IF NOT EXISTS escalations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    inbox_message_id INTEGER NOT NULL,
    group_id TEXT NOT NULL,
    telegram_message_id INTEGER NOT NULL,
    pseudonymous_user_id TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'normal', 'high', 'critical')),
    reason TEXT NOT NULL,
    notification_status TEXT NOT NULL DEFAULT 'simulated' CHECK (notification_status IN ('pending', 'delivered', 'failed', 'simulated', 'dead_letter')),
    resolution_status TEXT NOT NULL DEFAULT 'unresolved' CHECK (resolution_status IN ('unresolved', 'investigating', 'resolved', 'dismissed')),
    resolved_by TEXT,
    resolved_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (inbox_message_id) REFERENCES inbox_messages(id)
);

CREATE INDEX IF NOT EXISTS idx_escalations_lookup
    ON escalations(project_id, pseudonymous_user_id, created_at);

CREATE TABLE IF NOT EXISTS moderator_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    escalation_id INTEGER NOT NULL,
    channel_id TEXT NOT NULL,
    text TEXT NOT NULL,
    simulated INTEGER NOT NULL CHECK (simulated IN (0, 1)),
    state TEXT NOT NULL CHECK (state IN ('pending', 'sending', 'sent', 'simulated_delivered', 'failed', 'dead_letter')),
    state_changed_at TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 5),
    lease_owner TEXT,
    lease_expires_at TEXT,
    next_attempt_at TEXT,
    sent_at TEXT,
    telegram_message_id INTEGER,
    error_message TEXT,
    created_at TEXT NOT NULL,
    inline_keyboard_json TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (escalation_id) REFERENCES escalations(id),
    UNIQUE (project_id, escalation_id)
);

CREATE INDEX IF NOT EXISTS idx_mod_notif_claimable
    ON moderator_notifications(project_id, state, next_attempt_at);

-- Stage 7 Triggers: Moderator Notifications (7 triggers)

-- 15. Moderator notification simulated write-once trigger
CREATE TRIGGER IF NOT EXISTS trg_mod_notif_simulated_write_once
BEFORE UPDATE OF simulated ON moderator_notifications
WHEN OLD.simulated != NEW.simulated
BEGIN
    SELECT RAISE(ABORT, 'moderator notification simulated flag is write-once');
END;

-- 16. Moderator notification insert sent requires simulated=0
CREATE TRIGGER IF NOT EXISTS trg_mod_notif_insert_sent_requires_real
BEFORE INSERT ON moderator_notifications
WHEN NEW.state = 'sent' AND NEW.simulated = 1
BEGIN
    SELECT RAISE(ABORT, 'moderator notification state sent requires simulated=0');
END;

-- 17. Moderator notification update sent requires simulated=0
CREATE TRIGGER IF NOT EXISTS trg_mod_notif_update_sent_requires_real
BEFORE UPDATE OF state ON moderator_notifications
WHEN NEW.state = 'sent' AND NEW.simulated = 1
BEGIN
    SELECT RAISE(ABORT, 'moderator notification state sent requires simulated=0');
END;

-- 18. Moderator notification insert simulated_delivered requires simulated=1
CREATE TRIGGER IF NOT EXISTS trg_mod_notif_insert_simulated_delivered_requires_simulated
BEFORE INSERT ON moderator_notifications
WHEN NEW.state = 'simulated_delivered' AND NEW.simulated = 0
BEGIN
    SELECT RAISE(ABORT, 'moderator notification state simulated_delivered requires simulated=1');
END;

-- 19. Moderator notification update simulated_delivered requires simulated=1
CREATE TRIGGER IF NOT EXISTS trg_mod_notif_update_simulated_delivered_requires_simulated
BEFORE UPDATE OF state ON moderator_notifications
WHEN NEW.state = 'simulated_delivered' AND NEW.simulated = 0
BEGIN
    SELECT RAISE(ABORT, 'moderator notification state simulated_delivered requires simulated=1');
END;

-- 20. Moderator notification terminal state sent
CREATE TRIGGER IF NOT EXISTS trg_mod_notif_terminal_state_sent
BEFORE UPDATE OF state ON moderator_notifications
WHEN OLD.state = 'sent'
BEGIN
    SELECT RAISE(ABORT, 'cannot transition out of terminal state sent');
END;

-- 21. Moderator notification terminal state simulated_delivered
CREATE TRIGGER IF NOT EXISTS trg_mod_notif_terminal_state_simulated_delivered
BEFORE UPDATE OF state ON moderator_notifications
WHEN OLD.state = 'simulated_delivered'
BEGIN
    SELECT RAISE(ABORT, 'cannot transition out of terminal state simulated_delivered');
END;
