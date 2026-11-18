# SecureID: Privacy Preserving Facial Biometric Authentication System

SecureID is a Python based facial biometric authentication prototype
designed to explore privacy conscious identity verification.

> **Disclaimer:** SecureID is an educational cybersecurity prototype.

## Features

- Real-time webcam facial detection using OpenCV
- Encrypted biometric enrollment storage
- PIN verification with salted PBKDF2 hashing
- Randomized head movement challenge
- Authentication logging and failed attempt monitoring
- Temporary lockouts after repeated verification failures
- Streamlit dashboard for monitoring security events
- User controlled biometric enrollment deletion
- Manual 30 day security-log retention and deletion
- Automated security and privacy validation checks

## Technologies

- Python
- OpenCV and LBPH facial recognition
- NumPy
- Cryptography (Fernet)
- Windows Credential Manager (Keyring)
- Streamlit
- Pandas
- Git and GitHub

## Authentication Workflow

1. User enrolls their face with consent.
2. Facial enrollment data is encrypted and stored locally.
3. User initiates facial verification.
4. SecureID compares the live face with the enrolled profile.
5. A randomized movement challenge is presented.
6. The user enters their PIN.
7. SecureID records the demonstration outcome in a local audit log.

## Privacy and Security

SecureID implements:

- Local biometric processing without cloud uploads
- Encrypted biometric enrollment data
- Separation of encrypted files and encryption keys
- Pseudonymous identifiers instead of legal names
- No permanent storage of full webcam frames
- User controlled enrollment deletion
- Privacy minimized security logs
- Manual 30 day security-log retention policy

Biometric enrollment samples remain sensitive even when encrypted.

## Installation

Clone the repository:

```bash
git clone https://github.com/ekim23205/SecureID-Biometric-Authentication.git
cd SecureID-Biometric-Authentication
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Configure a demonstration PIN:

```bash
python pin_auth.py setup
```

## Running SecureID

Start the facial authentication application:

```bash
python face_authentication.py
```

Controls:

| Key | Action |
|---|---|
| E | Enroll face |
| V | Verify face |
| D | Delete biometric enrollment |
| Q | Quit |

Run the local security dashboard:

```bash
python -m streamlit run dashboard.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

## Security Testing

Run the automated checks:

```bash
python security_tests.py
```

The project includes tests for expected file structure, Python syntax, enrollment file format, security log structure, dependencies, and Git exclusions.

## Known Limitations

- LBPH facial matching uses an experimental, unvalidated threshold.
- The head movement challenge is not reliable presentation attack detection.
- Verification may be susceptible to photographs, videos, or manipulated camera inputs.
- PIN and facial checks run on the same device and do not constitute production grade MFA.
- Authentication lockout counters reset when the application restarts.
- Local users with sufficient privileges may access or modify application data.
- Log cleanup is manual.
- Deleted biometric data may remain in memory, backups, or recoverable disk blocks.
- Automated structural tests do not establish production security.

## Ethical Use

Enroll only consenting users. Do not use SecureID for covert surveillance, identifying bystanders, or protecting real accounts.

## Project Status

Functional educational prototype. Security hardening and further accuracy testing are ongoing.