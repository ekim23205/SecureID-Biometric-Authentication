import secrets
import time


class MovementChallenge:
    """
    Basic facial movement challenge.
    Demonstration only - not secure liveness detection.
    """

    def __init__(self, face):
        x, y, w, h = face

        self.start_x = x + w / 2
        self.face_width = max(float(w), 1.0)

        self.direction = secrets.choice(["LEFT", "RIGHT"])
        self.stage = "MOVE"

        self.started = time.monotonic()
        self.timeout = 15

    def update(self, faces):

        # Require exactly one detected face
        if len(faces) != 1:
            return (
                "PENDING",
                "Keep one face visible"
            )

        # Check timeout
        if time.monotonic() - self.started > self.timeout:
            return (
                "FAILED",
                "Movement challenge timed out"
            )

        x, y, w, h = faces[0]
        center_x = x + w / 2

        movement = (
            center_x - self.start_x
        ) / self.face_width

        # Step 1: Move sideways
        if self.stage == "MOVE":

            if self.direction == "LEFT":
                reached = movement < -0.15
            else:
                reached = movement > 0.15

            if reached:
                self.stage = "RETURN"

                return (
                    "PENDING",
                    "RETURN TO STARTING POSITION"
                )

            return (
                "PENDING",
                f"MOVE {self.direction}"
            )

        # Step 2: Return to original position
        if self.stage == "RETURN":

            if abs(movement) < 0.10:
                return (
                    "PASSED",
                    "Movement challenge complete"
                )

            return (
                "PENDING",
                "RETURN TO STARTING POSITION"
            )

        return "FAILED", "Invalid challenge state"