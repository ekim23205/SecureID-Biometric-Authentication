import json
import time
from datetime import datetime, timezone
from pathlib import Path

# SecureID - Local Security Monitoring

MAX_FAILED_ATTEMPTS = 3
LOCKOUT_SECONDS = 30

LOG_DIR = Path(__file__).resolve().parent / "data"
LOG_FILE = LOG_DIR / "security_events.jsonl"

# Only these events may appear in the audit log.
ALLOWED_EVENTS = {
    "DEMO_MATCH",
    "NO_MATCH",
    "TEMPORARY_LOCKOUT",
    "LOCKOUT_ENDED",
    "PIN_FAILED",
    "PIN_LOCKOUT",
    "TWO_STEP_DEMO_MATCH",
    "CHALLENGE_PASSED",
    "CHALLENGE_FAILED",
}


class SecurityMonitor:
    def __init__(self):
        self.failed_attempts = 0
        self.locked_until = 0.0
        LOG_DIR.mkdir(exist_ok=True)

    def log_event(self, event):
        """Record a minimal, privacy-focused event."""

        if event not in ALLOWED_EVENTS:
            raise ValueError("Unsupported security event")

        record = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "event": event
        }

        with LOG_FILE.open(
            "a", encoding="utf-8"
        ) as file:
            file.write(json.dumps(record) + "\n")

        print("[SECURITY EVENT]", event)

    def is_locked(self):
        """Check whether verification is locked."""

        if self.locked_until == 0:
            return False

        if time.monotonic() < self.locked_until:
            return True

        self.locked_until = 0
        self.failed_attempts = 0

        self.log_event("LOCKOUT_ENDED")
        return False

    def remaining_seconds(self):
        return max(
            0,
            int(self.locked_until - time.monotonic()) + 1
        )

    def record_success(self):
        self.failed_attempts = 0
        self.log_event("DEMO_MATCH")

    def record_failure(self):
        self.failed_attempts += 1
        self.log_event("NO_MATCH")

        print(
            "Failed attempts:",
            self.failed_attempts
        )

        if self.failed_attempts >= MAX_FAILED_ATTEMPTS:
            self.locked_until = (
                time.monotonic() + LOCKOUT_SECONDS
            )

            self.log_event("TEMPORARY_LOCKOUT")

            print(
                "[SECURITY ALERT] Too many failed "
                "verification attempts!"
            )

            return True

        return False