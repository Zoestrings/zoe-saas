"""Twitter (X) adapter for Zoe autonomous agent platform.

Enables mention polling, auto-replies, and community intelligence on X
while routing all queries through the unified Zoe intelligence engine.
"""

import asyncio
from datetime import datetime, timezone
import re
from typing import Any, Callable, Dict, List, Optional, Set, Union
import tweepy

from zoe.telegram.normalizer import NormalizedMessage, compute_pseudonym
from zoe.utils.logging import get_logger

logger = get_logger("zoe.twitter.adapter")


class TwitterSentMessage:
    """Represents a successfully published tweet reply."""

    def __init__(self, message_id: int):
        self.message_id = message_id


class TwitterAdapter:
    """Adapter for polling mentions and replying to tweets on X (Twitter)."""

    def __init__(
        self,
        project_id: str,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str,
        bearer_token: Optional[str] = None,
        poll_interval_seconds: int = 120,
        hmac_key: str = "default_hmac_key_32_characters_minimum",
        on_message_callback: Optional[Callable[[NormalizedMessage], Any]] = None,
    ) -> None:
        self.project_id = project_id
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.access_token = access_token.strip()
        self.access_secret = access_secret.strip()
        self.bearer_token = bearer_token.strip() if bearer_token else None
        self.poll_interval = max(30, int(poll_interval_seconds))
        self.hmac_key = hmac_key
        self.on_message_callback = on_message_callback

        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_secret,
            wait_on_rate_limit=True,
        )

        self._bot_id: Optional[int] = None
        self._bot_username: Optional[str] = None
        self._last_seen_id: Optional[int] = None
        self._seen_ids: Set[int] = set()
        self._bg_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._incoming_queue: asyncio.Queue[NormalizedMessage] = asyncio.Queue()

    def _init_identity(self) -> None:
        """Fetch bot's own user identity from Twitter API."""
        try:
            me = self.client.get_me()
            if me and me.data:
                self._bot_id = me.data.id
                self._bot_username = me.data.username
                logger.info(
                    "Twitter bot authenticated as @%s (ID: %s) for project %s",
                    self._bot_username,
                    self._bot_id,
                    self.project_id,
                )
        except Exception as exc:
            logger.warning("Could not fetch Twitter bot identity: %s", exc)

    async def _poll_loop(self) -> None:
        """Periodic background poller fetching new @mentions."""
        while self._is_running:
            try:
                await self.poll_mentions()
            except Exception as poll_err:
                logger.error("Error during Twitter mention polling: %s", poll_err)

            await asyncio.sleep(self.poll_interval)

    async def poll_mentions(self) -> List[NormalizedMessage]:
        """Fetch latest @mentions since last poll, normalize and queue them."""
        if not self._bot_id:
            await asyncio.to_thread(self._init_identity)
            if not self._bot_id:
                return []

        def _fetch():
            kwargs: Dict[str, Any] = {
                "id": self._bot_id,
                "tweet_fields": ["created_at", "author_id", "conversation_id"],
                "expansions": ["author_id"],
                "user_fields": ["username"],
                "max_results": 20,
            }
            if self._last_seen_id:
                kwargs["since_id"] = self._last_seen_id
            return self.client.get_users_mentions(**kwargs)

        try:
            resp = await asyncio.to_thread(_fetch)
        except Exception as api_err:
            logger.warning("Twitter API get_users_mentions error: %s", api_err)
            return []

        if not resp or not resp.data:
            return []

        # Build user lookup dict from expansions
        users_by_id = {}
        if resp.includes and "users" in resp.includes:
            for u in resp.includes["users"]:
                users_by_id[u.id] = u.username

        new_messages = []
        for tweet in sorted(resp.data, key=lambda t: t.id):
            if tweet.id in self._seen_ids:
                continue
            self._seen_ids.add(tweet.id)
            self._last_seen_id = max(self._last_seen_id or 0, tweet.id)

            # Ignore own tweets
            if tweet.author_id == self._bot_id:
                continue

            username = users_by_id.get(tweet.author_id, f"user_{tweet.author_id}")
            raw_text = tweet.text or ""
            # Strip bot mention from beginning
            if self._bot_username:
                clean_text = re.sub(rf"(?i)@{re.escape(self._bot_username)}\b", "", raw_text).strip()
            else:
                clean_text = raw_text.strip()

            pseudo_id = compute_pseudonym(tweet.author_id, self.hmac_key)
            created_str = (
                tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if tweet.created_at
                else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            )

            normalized = NormalizedMessage(
                project_id=self.project_id,
                telegram_update_id=tweet.id,
                group_id=str(tweet.id),
                telegram_message_id=tweet.id,
                pseudonymous_user_id=pseudo_id,
                text=clean_text or raw_text,
                reply_to_message_id=tweet.id,
                is_forward=False,
                timestamp=created_str,
                is_voice=False,
                raw_user_id=tweet.author_id,
                username=username,
                platform="twitter",
            )

            await self._incoming_queue.put(normalized)
            new_messages.append(normalized)

            if self.on_message_callback:
                try:
                    res = self.on_message_callback(normalized)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as cb_err:
                    logger.error("Error in Twitter on_message_callback: %s", cb_err)

        if new_messages:
            logger.info("Fetched %d new mention(s) on Twitter for %s", len(new_messages), self.project_id)

        return new_messages

    async def start(self) -> None:
        """Start mention poller in background."""
        if self._is_running:
            return
        self._is_running = True
        await asyncio.to_thread(self._init_identity)
        self._bg_task = asyncio.create_task(self._poll_loop())
        logger.info("TwitterAdapter mention poller started for %s (interval: %ds)", self.project_id, self.poll_interval)

    async def stop(self) -> None:
        """Stop Twitter mention poller."""
        self._is_running = False
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()
            try:
                await self._bg_task
            except asyncio.CancelledError:
                pass
        logger.info("TwitterAdapter stopped for project %s", self.project_id)

    async def get_next_message(self, timeout: float = 1.0) -> Optional[NormalizedMessage]:
        """Fetch next incoming mention from the buffer queue."""
        try:
            return await asyncio.wait_for(self._incoming_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def send_message(
        self,
        chat_id: Union[str, int],
        text: str,
        reply_to_message_id: Optional[Union[str, int]] = None,
        inline_keyboard: Optional[Any] = None,
    ) -> TwitterSentMessage:
        """Publish a tweet reply (up to 280 characters)."""
        target_id = int(reply_to_message_id or chat_id)
        # Ensure tweet text fits within 280 character limit
        tweet_text = text.strip()
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

        def _post():
            return self.client.create_tweet(
                text=tweet_text,
                in_reply_to_tweet_id=target_id,
            )

        resp = await asyncio.to_thread(_post)
        tweet_id = resp.data["id"] if resp and resp.data else target_id
        return TwitterSentMessage(message_id=int(tweet_id))

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
