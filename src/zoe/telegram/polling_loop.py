import sqlite3
from typing import Optional

from zoe.inbox.inbox_service import (
    PersistResult,
    init_polling_state,
    persist_batch,
)
from zoe.telegram.adapter import TelegramAdapter
from zoe.telegram.normalizer import normalize_update, normalize_update_async
from zoe.utils.errors import PollingGapAlert
from zoe.utils.logging import get_logger

logger = get_logger("zoe.telegram.polling")


class PollingLoop:
    """Application-managed Telegram polling loop per Spec §6.3.

    Fetches updates using TelegramAdapter, normalizes, and advances polling_state
    strictly after durable persistence. Never uses PTB updater.
    """

    def __init__(
        self,
        project_id: str,
        adapter: TelegramAdapter,
        db_conn: sqlite3.Connection,
        configured_group_id: str,
        hmac_key: str,
        poll_timeout: int = 30,
        limit: int = 100,
        allow_gap_recovery: bool = False,
    ) -> None:
        self.project_id = project_id
        self.adapter = adapter
        self.db_conn = db_conn
        self.configured_group_id = str(configured_group_id)
        self.hmac_key = hmac_key
        self.poll_timeout = poll_timeout
        self.limit = limit
        self.allow_gap_recovery = allow_gap_recovery
        self._is_running = False

    def init_state(self) -> None:
        """Initialize polling state in DB if not already present."""
        init_polling_state(self.db_conn, self.project_id)

    def get_polling_state(self) -> tuple[int, int]:
        """Return (last_persisted_update_id, next_offset)."""
        cur = self.db_conn.cursor()
        cur.execute(
            "SELECT last_persisted_update_id, next_offset FROM polling_state WHERE project_id = ?",
            (self.project_id,),
        )
        row = cur.fetchone()
        if row is None:
            self.init_state()
            return (0, 1)
        return (row[0], row[1])

    async def step(self) -> PersistResult:
        """Execute a single polling cycle: fetch, gap check, normalize, persist."""
        last_persisted_id, next_offset = self.get_polling_state()

        try:
            updates = await self.adapter.get_updates(
                offset=next_offset,
                timeout=self.poll_timeout,
                limit=self.limit,
            )
        except Exception as e:
            if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                return PersistResult(0, 0, next_offset)
            raise

        if not updates:
            return PersistResult(
                inserted_count=0,
                skipped_duplicate_count=0,
                final_offset=next_offset,
            )

        # Gap detection: if the first update_id exceeds next_offset
        first_update_id = updates[0].get("update_id", 0)
        if last_persisted_id > 0 and first_update_id > next_offset:
            gap = first_update_id - next_offset
            logger.warning(
                f"Polling gap detected for {self.project_id}: expected {next_offset}, got {first_update_id} (gap: {gap})"
            )
            if not self.allow_gap_recovery:
                raise PollingGapAlert(
                    f"Gap detected: expected update_id {next_offset}, received {first_update_id} (missing {gap} updates)"
                )
            logger.info("Auto-recovering from polling gap and continuing ingestion...")

        # Normalize batch (handles both typed text and voice notes)
        normalized_messages = []
        for u in updates:
            msg = await normalize_update_async(
                project_id=self.project_id,
                update=u,
                configured_group_id=self.configured_group_id,
                hmac_key=self.hmac_key,
                adapter=self.adapter,
            )
            if msg is not None:
                normalized_messages.append(msg)

        last_update_id_in_batch = max(u.get("update_id", 0) for u in updates)

        # Atomic persistence of messages, receipts, and polling state
        return persist_batch(
            conn=self.db_conn,
            project_id=self.project_id,
            normalized_messages=normalized_messages,
            last_update_id_in_batch=last_update_id_in_batch,
        )

    async def start(self, max_iterations: Optional[int] = None) -> None:
        """Run the polling loop for a given number of iterations or indefinitely."""
        self.init_state()
        self._is_running = True
        iterations = 0

        while self._is_running:
            iterations += 1
            await self.step()
            if max_iterations is not None and iterations >= max_iterations:
                break

    def stop(self) -> None:
        """Stop the polling loop."""
        self._is_running = False

