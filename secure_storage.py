from pathlib import Path
from io import BytesIO
import os
import uuid

import numpy as np
import keyring
from cryptography.fernet import Fernet, InvalidToken

# Keep biometric data inside the project folder
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = DATA_DIR / "enrollment.enc"

# Encryption key is kept in Windows Credential Manager
SERVICE_NAME = "SecureID-Local-Biometrics"
ACCOUNT_NAME = "single-user-prototype"


def save_enrollment(samples):
    """Encrypt and save an enrolled face locally."""

    if not samples:
        raise ValueError("No face samples to save.")

    DATA_DIR.mkdir(exist_ok=True)

    # Assign a random identifier, not a real name
    user_id = uuid.uuid4().hex

    # Serialize facial samples in memory
    buffer = BytesIO()
    np.savez_compressed(
        buffer,
        faces=np.stack(samples),
        user_id=np.array(user_id)
    )

    # Generate a fresh encryption key
    encryption_key = Fernet.generate_key()

    # Encrypt before writing anything to disk
    encrypted_data = Fernet(encryption_key).encrypt(
        buffer.getvalue()
    )

    # Store key separately in Windows Credential Manager
    keyring.set_password(
        SERVICE_NAME,
        ACCOUNT_NAME,
        encryption_key.decode("ascii")
    )

    # Write only encrypted bytes to disk
    temporary_file = DATA_DIR / "enrollment.tmp"

    try:
        with open(temporary_file, "wb") as file:
            file.write(encrypted_data)

        os.replace(temporary_file, DATA_FILE)
    finally:
        temporary_file.unlink(missing_ok=True)

    return user_id


def load_enrollment():
    """Decrypt enrollment in memory."""

    if not DATA_FILE.exists():
        return None

    stored_key = keyring.get_password(
        SERVICE_NAME,
        ACCOUNT_NAME
    )

    if stored_key is None:
        raise RuntimeError(
            "Enrollment exists, but its encryption key "
            "is unavailable."
        )

    try:
        encrypted_data = DATA_FILE.read_bytes()

        decrypted_data = Fernet(
            stored_key.encode("ascii")
        ).decrypt(encrypted_data)

        with np.load(
            BytesIO(decrypted_data),
            allow_pickle=False
        ) as archive:
            faces = archive["faces"].copy()
            user_id = str(archive["user_id"].item())

        return faces, user_id

    except InvalidToken as error:
        raise RuntimeError(
            "Enrollment decryption failed."
        ) from error


def delete_enrollment():
    """Remove the saved enrollment and encryption key."""

    # Revoke access to the encrypted file first
    keyring.delete_password(
        SERVICE_NAME,
        ACCOUNT_NAME
    ) if keyring.get_password(
        SERVICE_NAME,
        ACCOUNT_NAME
    ) is not None else None

    DATA_FILE.unlink(missing_ok=True)
