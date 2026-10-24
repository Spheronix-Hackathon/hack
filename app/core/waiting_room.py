import asyncio
import hashlib
import hmac
import math
import time
from collections import deque
from typing import Dict, Optional, Tuple

from config.settings import get_settings

settings = get_settings()


class FIFOWaitingRoom:
    """
    High-Concurrency Virtual Waiting Room for Flash Registrations (10,000+ simultaneous students).
    Guarantees:
      1. First-In, First-Out (FIFO) queue order.
      2. Rate-limited admission (default 100 students per second).
      3. Active session TTL (30 minutes) to complete registration.
      4. Zero database load during traffic spikes (in-memory async FIFO state).
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._queue = deque()  # FIFO deque of ticket_ids
        self._tickets: Dict[str, dict] = {}  # ticket_id -> metadata
        self._admitted: Dict[str, float] = {}  # ticket_id -> expiry_timestamp
        self._ticker_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start(self):
        """Start the background admission ticker."""
        if self._is_running:
            return
        self._is_running = True
        self._ticker_task = asyncio.create_task(self._admission_loop())

    async def stop(self):
        """Stop background ticker."""
        self._is_running = False
        if self._ticker_task:
            self._ticker_task.cancel()
            try:
                await self._ticker_task
            except asyncio.CancelledError:
                pass

    def _sign_token(self, ticket_id: str, expiry: int) -> str:
        """Create HMAC-SHA256 signed queue pass token."""
        payload = f"{ticket_id}:{expiry}"
        sig = hmac.new(
            settings.secret_key.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()[:24]
        return f"{payload}:{sig}"

    def verify_token(self, token: Optional[str]) -> bool:
        """Verify token signature and expiration."""
        if not token or not settings.queue_enabled:
            return True if not settings.queue_enabled else False
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False
            ticket_id, expiry_str, sig = parts
            expiry = int(expiry_str)
            if time.time() > expiry:
                return False  # Expired
            expected_payload = f"{ticket_id}:{expiry}"
            expected_sig = hmac.new(
                settings.secret_key.encode("utf-8"),
                expected_payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()[:24]
            return hmac.compare_digest(sig, expected_sig)
        except Exception:
            return False

    async def request_entry(self, existing_ticket: Optional[str] = None) -> dict:
        """
        Request entry into the registration portal.
        Returns:
          - admitted: True, token: <signed_token>
          - admitted: False, ticket_id: <str>, position: <int>, wait_seconds: <int>
        """
        if not settings.queue_enabled:
            now = int(time.time())
            dummy_token = self._sign_token("bypass", now + settings.queue_pass_ttl)
            return {"status": "admitted", "admitted": True, "token": dummy_token}

        async with self._lock:
            now = time.time()
            self._cleanup_expired(now)

            # Check if existing ticket is already admitted
            if existing_ticket and existing_ticket in self._admitted:
                expiry = int(self._admitted[existing_ticket])
                token = self._sign_token(existing_ticket, expiry)
                return {
                    "status": "admitted",
                    "admitted": True,
                    "token": token,
                    "ticket_id": existing_ticket,
                }

            # If existing ticket is in queue, return current position
            if existing_ticket and existing_ticket in self._tickets:
                try:
                    pos = self._queue.index(existing_ticket) + 1
                    admit_rate = max(1, settings.queue_admit_rate)
                    wait_sec = math.ceil(pos / admit_rate)
                    return {
                        "status": "waiting",
                        "admitted": False,
                        "ticket_id": existing_ticket,
                        "position": pos,
                        "wait_seconds": wait_sec,
                        "total_in_line": len(self._queue),
                    }
                except ValueError:
                    # Not in queue anymore, might have been cleared
                    pass

            # If no queue and active users are under limit, admit immediately
            active_count = len(self._admitted)
            if len(self._queue) == 0 and active_count < settings.queue_max_active:
                ticket_id = self._generate_ticket_id()
                expiry = int(now + settings.queue_pass_ttl)
                self._admitted[ticket_id] = expiry
                token = self._sign_token(ticket_id, expiry)
                return {
                    "status": "admitted",
                    "admitted": True,
                    "token": token,
                    "ticket_id": ticket_id,
                }

            # Otherwise, join the FIFO queue
            ticket_id = existing_ticket or self._generate_ticket_id()
            if ticket_id not in self._tickets:
                self._tickets[ticket_id] = {"joined_at": now}
                self._queue.append(ticket_id)

            pos = len(self._queue)
            admit_rate = max(1, settings.queue_admit_rate)
            wait_sec = math.ceil(pos / admit_rate)
            return {
                "status": "waiting",
                "admitted": False,
                "ticket_id": ticket_id,
                "position": pos,
                "wait_seconds": wait_sec,
                "total_in_line": pos,
            }

    async def get_ticket_status(self, ticket_id: str) -> dict:
        """Check status of a queued ticket."""
        if not settings.queue_enabled:
            now = int(time.time())
            return {
                "status": "admitted",
                "admitted": True,
                "token": self._sign_token("bypass", now + 1800),
            }

        async with self._lock:
            now = time.time()
            self._cleanup_expired(now)

            # Admitted?
            if ticket_id in self._admitted:
                expiry = int(self._admitted[ticket_id])
                token = self._sign_token(ticket_id, expiry)
                return {
                    "status": "admitted",
                    "admitted": True,
                    "token": token,
                    "ticket_id": ticket_id,
                }

            # Still in queue?
            if ticket_id in self._tickets and ticket_id in self._queue:
                pos = self._queue.index(ticket_id) + 1
                admit_rate = max(1, settings.queue_admit_rate)
                wait_sec = math.ceil(pos / admit_rate)
                return {
                    "status": "waiting",
                    "admitted": False,
                    "ticket_id": ticket_id,
                    "position": pos,
                    "wait_seconds": wait_sec,
                    "total_in_line": len(self._queue),
                }

            # Not found -> generate new entry
            return await self.request_entry(None)

    def _cleanup_expired(self, now: float):
        """Remove expired admission passes."""
        expired = [tid for tid, exp in self._admitted.items() if exp < now]
        for tid in expired:
            self._admitted.pop(tid, None)

    def _generate_ticket_id(self) -> str:
        """Create random 16-char hex ticket."""
        import secrets
        return secrets.token_hex(8)

    async def _admission_loop(self):
        """
        Background worker executing every 1 second:
        Admits up to `queue_admit_rate` (default 100) members per second from front of FIFO queue.
        """
        while self._is_running:
            try:
                await asyncio.sleep(1.0)
                if not settings.queue_enabled or len(self._queue) == 0:
                    continue

                async with self._lock:
                    now = time.time()
                    self._cleanup_expired(now)

                    batch_size = min(settings.queue_admit_rate, len(self._queue))
                    expiry = int(now + settings.queue_pass_ttl)

                    for _ in range(batch_size):
                        if not self._queue:
                            break
                        admitted_id = self._queue.popleft()
                        self._tickets.pop(admitted_id, None)
                        self._admitted[admitted_id] = expiry

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)


# Global singleton instance
waiting_room = FIFOWaitingRoom()
