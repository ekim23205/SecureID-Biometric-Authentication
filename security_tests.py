from pathlib import Path
import ast
import json
import importlib.util

# SecureID - Final Privacy & Security Checks

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

REQUIRED_FILES = [
    "face_detector.py",
    "face_authentication.py",
    "secure_storage.py",
    "security_monitor.py",
    "privacy_controls.py",
    "pin_auth.py",
    "liveness_demo.py",
    "dashboard.py",
    "authentication_testing.py",
]

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

passed = 0
failed = 0


def check(name, condition):
    global passed, failed

    if condition:
        passed += 1
        print(f"[PASS] {name}")
    else:
        failed += 1
        print(f"[FAIL] {name}")


print("\nSecureID - Final Security Tests")
print("=" * 40)

# Test 1: Check required project files
for filename in REQUIRED_FILES:
    check(
        f"Required file: {filename}",
        (PROJECT_DIR / filename).is_file()
    )

# Test 2: Validate Python syntax
for filename in REQUIRED_FILES:
    file_path = PROJECT_DIR / filename

    if not file_path.exists():
        continue

    try:
        ast.parse(
            file_path.read_text(encoding="utf-8")
        )
        check(f"Python syntax: {filename}", True)

    except (SyntaxError, UnicodeError):
        check(f"Python syntax: {filename}", False)

# Test 3: Verify private storage location
check(
    "Private data directory exists",
    DATA_DIR.is_dir()
)

# Test 4: Verify GitHub exclusions
gitignore = PROJECT_DIR / ".gitignore"

if gitignore.exists():
    content = gitignore.read_text(
        encoding="utf-8"
    ).splitlines()

    rules = {
        line.strip()
        for line in content
        if line.strip() and not line.startswith("#")
    }

    check(
        "Biometric data excluded from Git",
        "data/" in rules
    )

    check(
        "Virtual environment excluded from Git",
        ".venv/" in rules
    )

    check(
        "Secrets excluded from Git",
        ".env" in rules
    )
else:
    check(".gitignore exists", False)

# Test 5: Check encrypted enrollment format
enrollment = DATA_DIR / "enrollment.enc"

if enrollment.exists():
    content = enrollment.read_bytes()

    check(
        "Enrollment uses Fernet token format",
        content.startswith(b"gAAAA")
    )
else:
    print("[INFO] No saved biometric enrollment found.")

# Test 6: Check security event structure
log_file = DATA_DIR / "security_events.jsonl"

if log_file.exists():
    valid = True
    event_count = 0

    with log_file.open(
        "r", encoding="utf-8"
    ) as file:
        for line in file:
            if not line.strip():
                continue

            try:
                record = json.loads(line)

                if (
                    not isinstance(record, dict)
                    or set(record) != {"timestamp", "event"}
                    or record["event"] not in ALLOWED_EVENTS
                    or not isinstance(record["timestamp"], str)
                ):
                    valid = False
                    break

                event_count += 1

            except json.JSONDecodeError:
                valid = False
                break

    check("Security event structure", valid)
    print(f"[INFO] Events inspected: {event_count}")

else:
    print("[INFO] No security event log found.")

# Test 7: Verify encryption dependencies
for package in ["cryptography", "keyring", "cv2"]:
    check(
        f"Dependency installed: {package}",
        importlib.util.find_spec(package) is not None
    )

print("\n" + "=" * 40)
print("Tests passed:", passed)
print("Tests failed:", failed)

if failed == 0:
    print("All automated checks passed.")
else:
    print("Review failed checks before publishing.")

print(
    "\nNote: Passing does not prove that "
    "authentication or encryption is secure."
)

raise SystemExit(1 if failed else 0)
