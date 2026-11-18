import hashlib
import hmac
import secrets
import sys
import time
from getpass import getpass

import keyring

# SecureID - Local PIN Verification

SERVICE = "SecureID-Local-PIN"
ACCOUNT = "single-user-prototype"

ITERATIONS = 600_000
MAX_ATTEMPTS = 3
LOCKOUT_SECONDS = 30


def pin_is_configured():
    return keyring.get_password(SERVICE, ACCOUNT) is not None


def setup_pin():
    """Register a PIN using Windows Credential Manager."""

    if pin_is_configured():
        print("A PIN is already configured.")
        print("Existing PIN was not changed.")
        return

    print("SecureID PIN Setup")
    print("Choose a PIN with at least 8 digits.")

    pin = getpass("Create PIN: ")
    confirm = getpass("Confirm PIN: ")

    if not pin.isascii() or not pin.isdigit() or len(pin) < 8:
        print("PIN must contain at least 8 ASCII digits.")
        return

    if pin != confirm:
        print("PINs do not match.")
        return

    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt,
        ITERATIONS
    )

    # Store a salted verifier, never the plaintext PIN
    stored = salt.hex() + ":" + digest.hex()

    keyring.set_password(
        SERVICE,
        ACCOUNT,
        stored
    )

    print("PIN configured successfully.")
    print("No plaintext PIN was stored.")


def verify_pin(pin):
    """Check PIN without exposing its stored value."""

    stored = keyring.get_password(
        SERVICE,
        ACCOUNT
    )

    if stored is None:
        return False

    try:
        salt_hex, digest_hex = stored.split(":", 1)

        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            ITERATIONS
        )

        return hmac.compare_digest(actual, expected)

    except (ValueError, TypeError):
        return False


def prompt_pin():
    """Show a masked PIN dialog."""

    import tkinter as tk
    from tkinter import simpledialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        return simpledialog.askstring(
            "SecureID Verification",
            "Enter your SecureID PIN:",
            show="*",
            parent=root
        )
    finally:
        root.destroy()


class PINAttemptLimiter:
    def __init__(self):
        self.failures = 0
        self.locked_until = 0.0

    def is_locked(self):
        if time.monotonic() >= self.locked_until:
            if self.locked_until:
                self.failures = 0
                self.locked_until = 0.0
            return False
        return True

    def remaining_seconds(self):
        return max(
            0,
            int(self.locked_until - time.monotonic()) + 1
        )

    def record_failure(self):
        self.failures += 1

        if self.failures >= MAX_ATTEMPTS:
            self.locked_until = (
                time.monotonic() + LOCKOUT_SECONDS
            )
            return True

        return False

    def record_success(self):
        self.failures = 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "setup":
        setup_pin()
    else:
        print("Usage: python pin_auth.py setup")