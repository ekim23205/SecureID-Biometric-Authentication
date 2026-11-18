import cv2
import numpy as np
import time

from liveness_demo import MovementChallenge

from pin_auth import (
    PINAttemptLimiter,
    pin_is_configured,
    prompt_pin,
    verify_pin
)

from secure_storage import (
    save_enrollment,
    load_enrollment,
    delete_enrollment
)

from security_monitor import SecurityMonitor

# SecureID - Privacy-First Facial Authentication
# All processing happens locally.

SAMPLES_NEEDED = 20
MATCH_THRESHOLD = 60  # Experimental, not security-calibrated

# Load OpenCV face detector
detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

if detector.empty():
    raise RuntimeError("Face detector could not be loaded.")

# Create facial recognition model
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Open webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise RuntimeError("Could not access webcam.")

samples = []
enrolled = False
collecting = False
last_sample_time = 0

status = "Press E to enroll your face"

# Initialize authentication security monitoring
security_monitor = SecurityMonitor()
pin_limiter = PINAttemptLimiter()

# Movement challenge state
movement_challenge = None

def prepare_face(gray, face):
    x, y, w, h = face
    cropped = gray[y:y+h, x:x+w]
    resized = cv2.resize(cropped, (100, 100))
    return cv2.equalizeHist(resized)

def complete_pin_verification():
    """Complete the PIN step after a movement challenge."""

    if not pin_is_configured():
        print("Run: python pin_auth.py setup")
        return "SET UP PIN FIRST"

    if pin_limiter.is_locked():
        remaining = pin_limiter.remaining_seconds()
        return f"PIN LOCKED - {remaining}s"

    print("Movement challenge passed. PIN required.")

    entered_pin = prompt_pin()

    if entered_pin is None:
        return "PIN verification cancelled"

    verified = verify_pin(entered_pin)
    del entered_pin

    if verified:
        pin_limiter.record_success()

        security_monitor.log_event(
            "TWO_STEP_DEMO_MATCH"
        )

        print("Two-step verification successful.")
        return "TWO-STEP DEMO VERIFIED"

    locked = pin_limiter.record_failure()

    security_monitor.log_event("PIN_FAILED")

    if locked:
        security_monitor.log_event("PIN_LOCKOUT")
        return "PIN TEMPORARILY LOCKED"

    return "INCORRECT PIN"



# Restore an encrypted enrollment
try:
    saved = load_enrollment()

    if saved is not None:
        saved_faces, user_id = saved

        labels = np.zeros(
            len(saved_faces), dtype=np.int32
        )

        recognizer.train(saved_faces, labels)
        enrolled = True

        del saved_faces
        status = "Saved enrollment loaded - Press V"

        print("Encrypted enrollment restored.")

except Exception as error:
    print("Unable to restore enrollment:", error)
    status = "Press E to enroll your face"


print("SecureID Facial Authentication Started")
print("E = Enroll Face")
print("V = Verify Face")
print("D = Delete Enrollment")
print("Q = Quit")

try:
    while True:
        success, frame = camera.read()

        if not success:
            print("Failed to read webcam.")
            break

        # Convert frame to grayscale
        gray = cv2.cvtColor(
            frame, cv2.COLOR_BGR2GRAY
        )

        # Detect faces
        faces = detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=8,
            minSize=(100, 100)
        )
         # Process an active movement challenge
        if movement_challenge is not None:

            result, message = movement_challenge.update(
                faces
            )

            status = message

            if result == "PASSED":
                movement_challenge = None

                security_monitor.log_event(
                    "CHALLENGE_PASSED"
                )

                status = complete_pin_verification()

            elif result == "FAILED":
                movement_challenge = None

                security_monitor.log_event(
                    "CHALLENGE_FAILED"
                )

                status = "MOVEMENT CHALLENGE FAILED"


        # Collect facial samples
        if collecting:
            if len(faces) == 1:
                now = time.monotonic()

                if now - last_sample_time >= 0.2:
                    sample = prepare_face(gray, faces[0])
                    samples.append(sample)
                    last_sample_time = now

                status = (
                    f"Enrolling: {len(samples)}/"
                    f"{SAMPLES_NEEDED}"
                )

                if len(samples) >= SAMPLES_NEEDED:
                    labels = np.zeros(
                        len(samples), dtype=np.int32
                    )

                    try:
                        # Train facial recognition model
                        recognizer.train(samples, labels)

                        # Encrypt enrollment before saving
                        user_id = save_enrollment(samples)

                        print("Enrollment encrypted successfully.")
                        print("Anonymous user ID:", user_id)

                        samples.clear()
                        enrolled = True
                        collecting = False

                        status = "Encrypted Enrollment Complete!"

                    except Exception as error:
                        print("Enrollment storage failed:", error)

                        samples.clear()

                        recognizer = (
                            cv2.face.LBPHFaceRecognizer_create()
                        )

                        enrolled = False
                        collecting = False

                        status = "Enrollment failed - Press E"

            else:
                status = "Please show exactly one face"

        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                (0, 255, 0),
                3
            )

        # Display status
        cv2.putText(
            frame,
            status,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )

        # Display webcam
        cv2.imshow(
            "SecureID - Facial Authentication",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        # Enroll face
        if key == ord("e"):
            try:
                # Remove existing saved enrollment
                delete_enrollment()

                recognizer = (
                    cv2.face.LBPHFaceRecognizer_create()
                )

                samples.clear()
                enrolled = False
                collecting = True
                last_sample_time = 0

                status = "Starting Enrollment..."

            except Exception as error:
                print("Enrollment reset failed:", error)
                status = "Reset failed - Check terminal"

           # Verify face and start movement challenge
        elif key == ord("v"):

            if movement_challenge is not None:
                status = "Finish movement challenge first"

            elif security_monitor.is_locked():
                remaining = security_monitor.remaining_seconds()
                status = f"LOCKED - Retry in {remaining}s"

            elif collecting:
                status = "Finish enrollment first"

            elif not enrolled:
                status = "Please enroll first"

            elif len(faces) != 1:
                status = "Show exactly one face"

            else:
                face_image = prepare_face(
                    gray, faces[0]
                )

                label, distance = recognizer.predict(
                    face_image
                )

                print(
                    f"Verification distance: {distance:.2f}"
                )

                if (
                    label == 0
                    and distance < MATCH_THRESHOLD
                ):
                    security_monitor.record_success()

                    movement_challenge = MovementChallenge(
                        faces[0]
                    )

                    status = (
                        "CHALLENGE: Move "
                        + movement_challenge.direction
                    )

                    print(status)

                else:
                    status = "NO MATCH"

                    locked = security_monitor.record_failure()

                    if locked:
                        status = (
                            "SECURITY ALERT - TEMPORARY LOCKOUT"
                        )

        # Delete enrollment
        elif key == ord("d"):
            try:
                delete_enrollment()

                recognizer = (
                    cv2.face.LBPHFaceRecognizer_create()
                )

                samples.clear()
                movement_challenge = None
                enrolled = False
                collecting = False
                movement_challenge = None

                status = "Enrollment Deleted"
                print("Saved enrollment and key removed.")

            except Exception as error:
                print("Deletion error:", error)
                status = "Deletion failed - Check terminal"

        # Quit application
        elif key == ord("q") or key == 27:
            print("Closing SecureID...")
            break

finally:
    samples.clear()
    recognizer = None
    camera.release()
    cv2.destroyAllWindows()

    print("SecureID closed.")
    print("No unencrypted biometric files created.")