# File: hardware/ai_modules/face_recognizer.py
"""
Real-time face recognition with anti-spoofing (liveness detection).

Supports multiple camera backends: picamera2, GStreamer, V4L2, and OpenCV default.
"""
import cv2
import datetime
import logging
import math
import os
import random
import sys
import time

import face_recognition
import numpy as np
from os import environ

# Add project path for database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from database_modules.employee_crud import get_all_employees
    from database_modules.attendance_logger import mark_attendance
    from utils.attendance_status import determine_attendance_status
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running from the project root.")
    sys.exit(1)

logger = logging.getLogger(__name__)

# Try to import picamera2 for Pi OS Bookworm
PICAMERA2_AVAILABLE = False
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
    logger.info("picamera2 library found.")
except ImportError:
    logger.info("picamera2 not available, will try OpenCV backends.")


class PiCameraWrapper:
    """Wrapper to make Picamera2 behave like cv2.VideoCapture."""

    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()
        self._is_open = True

    def read(self):
        if not self._is_open:
            return False, None
        frame = self.picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return True, frame_bgr

    def isOpened(self):
        return self._is_open

    def release(self):
        if self._is_open:
            self.picam2.stop()
            self._is_open = False


def get_camera():
    """
    Try to open camera using different backends.
    Priority: picamera2 > GStreamer > V4L2 > Default
    """
    # 1. Try picamera2
    if PICAMERA2_AVAILABLE:
        logger.info("Attempting Picamera2 connection...")
        try:
            cam = PiCameraWrapper()
            ret, _ = cam.read()
            if ret:
                logger.info("Picamera2 backend works!")
                return cam
        except Exception as e:
            logger.warning("Picamera2 failed: %s", e)

    # 2. Try GStreamer
    logger.info("Attempting GStreamer connection...")
    gst_pipeline = (
        "libcamerasrc ! video/x-raw, width=640, height=480, framerate=15/1 ! "
        "videoconvert ! video/x-raw, format=BGR ! appsink drop=1"
    )
    try:
        cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        if cap.isOpened():
            ret, _ = cap.read()  # BUG FIX: was cam.read()
            if ret:
                logger.info("GStreamer backend works!")
                return cap
        cap.release()
    except Exception as e:
        logger.warning("GStreamer failed: %s", e)

    # 3. Try V4L2
    logger.info("Attempting V4L2 connection...")
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                logger.info("V4L2 backend works!")
                return cap
        cap.release()
    except Exception as e:
        logger.warning("V4L2 failed: %s", e)

    # 4. Try Default
    logger.info("Attempting Default connection...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                logger.info("Default backend works!")
                return cap
    except Exception as e:
        logger.warning("Default failed: %s", e)

    return None


# ── Anti-Spoofing Helpers ──────────────────────────────────────


def calculate_ear(eye_points):
    """Calculate Eye Aspect Ratio (EAR) for blink detection."""
    A = math.hypot(eye_points[1][0] - eye_points[5][0], eye_points[1][1] - eye_points[5][1])
    B = math.hypot(eye_points[2][0] - eye_points[4][0], eye_points[2][1] - eye_points[4][1])
    C = math.hypot(eye_points[0][0] - eye_points[3][0], eye_points[0][1] - eye_points[3][1])
    if C == 0:
        return 0
    return (A + B) / (2.0 * C)


def calculate_mar(mouth_points):
    """Calculate Mouth Aspect Ratio (MAR) for smile/open-mouth detection."""
    top_lip = mouth_points["top_lip"]
    bottom_lip = mouth_points["bottom_lip"]

    top_point = top_lip[9]
    bottom_point = bottom_lip[9]
    left_point = top_lip[0]
    right_point = top_lip[6]

    vert_dist = math.hypot(
        top_point[0] - bottom_point[0], top_point[1] - bottom_point[1]
    )
    horiz_dist = math.hypot(
        left_point[0] - right_point[0], left_point[1] - right_point[1]
    )

    if horiz_dist == 0:
        return 0
    return vert_dist / horiz_dist


# ── Main Recognition Loop ─────────────────────────────────────


def start_recognition_camera():
    """Start the face recognition camera with liveness detection."""
    logger.info("STARTING FACE RECOGNITION SYSTEM")

    url = environ.get("SUPABASE_URL", "").strip()
    key = environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        logger.critical("Supabase credentials missing!")
        return

    logger.info("Loading employee data from database...")
    try:
        employees_data = get_all_employees()
    except Exception as e:
        logger.exception("Database Error: %s", e)
        return

    known_face_encodings = [e["encoding"] for e in employees_data]
    known_face_names = [e["name"] for e in employees_data]
    known_face_ids = [e["id"] for e in employees_data]

    logger.info("System Ready: Loaded %d employees.", len(known_face_names))

    video_capture = get_camera()
    if video_capture is None:
        logger.critical("Could not open any camera.")
        return

    logger.info("Camera started. Strict Challenge Mode: Neutral -> Action -> Verify")

    window_name = "Smart Attendance - Liveness Check"

    # Thresholds
    EYE_AR_THRESH = 0.22
    EYE_AR_OPEN_THRESH = 0.25
    MOUTH_AR_THRESH = 0.35
    MOUTH_AR_CLOSED_THRESH = 0.30

    # State machine
    current_state = "IDLE"
    current_person = None
    challenge_type = None
    state_start_time = 0
    baseline_ear = 0.0
    baseline_mar = 0.0
    verification_success_time = 0
    display_message = "Scan Face..."
    message_color = (255, 255, 255)
    last_attendance_time = 0
    ATTENDANCE_COOLDOWN = 60

    while True:
        ret, frame = video_capture.read()
        if not ret:
            logger.error("Could not read frame.")
            break

        try:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        except Exception:
            continue

        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame, face_locations)

        if not face_locations:
            current_state = "IDLE"
            current_person = None
            display_message = "Scan Face..."
            message_color = (200, 200, 200)
            challenge_type = None
        else:
            face_encoding = face_encodings[0]
            landmarks = face_landmarks_list[0]
            (top, right, bottom, left) = face_locations[0]

            left_eye = landmarks["left_eye"]
            right_eye = landmarks["right_eye"]
            ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0
            mar = calculate_mar(landmarks)

            name = "Unknown"
            employee_id = None
            matches = face_recognition.compare_faces(
                known_face_encodings, face_encoding, tolerance=0.5
            )
            face_distances = face_recognition.face_distance(
                known_face_encodings, face_encoding
            )

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    employee_id = known_face_ids[best_match_index]

            if current_person != name and name != "Unknown":
                current_person = name
                current_state = "IDLE"

            if name == "Unknown":
                display_message = "Unknown User"
                message_color = (0, 0, 255)
                current_state = "IDLE"

            elif current_state == "IDLE":
                current_state = "CHECKING_NEUTRAL"
                state_start_time = time.time()
                display_message = "Keep Face Still..."
                message_color = (255, 255, 0)
                baseline_ear = ear
                baseline_mar = mar

            elif current_state == "CHECKING_NEUTRAL":
                baseline_ear = 0.1 * ear + 0.9 * baseline_ear
                baseline_mar = 0.1 * mar + 0.9 * baseline_mar

                if ear > 0.20 and mar < 0.35:
                    if time.time() - state_start_time > 1.0:
                        current_state = "ISSUING_CHALLENGE"
                else:
                    state_start_time = time.time()
                    display_message = "Keep Face Still..."

            elif current_state == "ISSUING_CHALLENGE":
                challenge_type = random.choice(["BLINK", "OPEN MOUTH"])
                current_state = "WAITING_FOR_ACTION"
                state_start_time = time.time()
                display_message = f"PLEASE {challenge_type} NOW!"
                message_color = (0, 255, 255)

            elif current_state == "WAITING_FOR_ACTION":
                if time.time() - state_start_time > 4.0:
                    current_state = "IDLE"
                    display_message = "Too Slow. Retry."

                success = False

                if challenge_type == "BLINK":
                    if ear < (baseline_ear - 0.05) and ear < 0.20:
                        success = True
                    if mar > (baseline_mar + 0.10):
                        current_state = "IDLE"
                        display_message = "Wrong Action!"

                elif challenge_type == "OPEN MOUTH":
                    if mar > (baseline_mar + 0.10):
                        success = True

                if success:
                    current_state = "VERIFIED"
                    verification_success_time = time.time()

                    if time.time() - last_attendance_time > ATTENDANCE_COOLDOWN:
                        now_disp = datetime.datetime.now()
                        time_disp = now_disp.strftime("%H:%M:%S")
                        date_disp = now_disp.strftime("%Y-%m-%d")
                        status_disp = determine_attendance_status(now_disp.hour)

                        logger.info(
                            "Verified: %s | %s | %s | %s",
                            name, date_disp, time_disp, status_disp,
                        )

                        mark_attendance(employee_id)
                        last_attendance_time = time.time()

                    display_message = "VERIFIED!"
                    message_color = (0, 255, 0)

            elif current_state == "VERIFIED":
                display_message = f"Welcome {name}"
                message_color = (0, 255, 0)
                if time.time() - verification_success_time > 3.0:
                    current_state = "IDLE"
                    current_person = None

            # Drawing UI
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), message_color, 2)
            cv2.rectangle(
                frame, (left, bottom - 35), (right, bottom), message_color, cv2.FILLED
            )
            cv2.putText(
                frame, name, (left + 6, bottom - 6),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 1,
            )
            cv2.putText(
                frame, display_message, (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, message_color, 3,
            )

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            logger.info("Exiting system...")
            break
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            logger.info("Window closed by user.")
            break

    video_capture.release()
    cv2.destroyAllWindows()
