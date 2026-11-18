
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# SecureID - Privacy Controls

DATA_DIR = Path(__file__).resolve().parent / "data"
LOG_FILE = DATA_DIR / "security_events.jsonl"

# Keep only the most recent 30 days of logs
RETENTION_DAYS = 30

def read_logs():
    """Read existing security events."""
    if not LOG_FILE.exists():
        return []

    records = []

    with LOG_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return records


def show_status():
    """Display log count without revealing user data."""
    records = read_logs()

    print("SecureID Privacy Report")
    print("-----------------------")
    print("Stored security events:", len(records))
    print("Retention period:", RETENTION_DAYS, "days")


def cleanup_old_logs():
    """Remove records older than retention period."""
    if not LOG_FILE.exists():
        print("No security logs found.")
        return

    cutoff = datetime.now(timezone.utc) - timedelta(
        days=RETENTION_DAYS
    )

    records = read_logs()
    recent = []

    for record in records:
        timestamp = datetime.fromisoformat(
            record["timestamp"].replace("Z", "+00:00")
        )

        if timestamp.astimezone(timezone.utc) >= cutoff:
            recent.append(record)

    removed = len(records) - len(recent)

    # Replace the file without leaving a plaintext backup.
    temp_file = DATA_DIR / "security_events.tmp"

    try:
        with temp_file.open("w", encoding="utf-8") as file:
            for record in recent:
                file.write(json.dumps(record) + "\n")

        os.replace(temp_file, LOG_FILE)
    finally:
        temp_file.unlink(missing_ok=True)

    print("Expired events removed:", removed)
    print("Events retained:", len(recent))


def delete_all_logs():
    """Require confirmation before deleting audit history."""
    confirmation = input(
        "Type DELETE LOGS to erase your audit log: "
    )

    if confirmation != "DELETE LOGS":
        print("Deletion cancelled.")
        return

    LOG_FILE.unlink(missing_ok=True)
    print("Local security log deleted.")
    print("Biometric enrollment was not changed.")


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print("Usage: privacy_controls.py status|cleanup|delete")

        elif sys.argv[1] == "status":
            show_status()

        elif sys.argv[1] == "cleanup":
            cleanup_old_logs()

        elif sys.argv[1] == "delete":
            delete_all_logs()

        else:
            print("Unknown command.")

    except (OSError, ValueError, KeyError) as error:
        print("Privacy operation failed:", error)