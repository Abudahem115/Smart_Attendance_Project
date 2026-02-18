# name file: ai_modules/face_recognizer.py
import cv2
import face_recognition
import numpy as np
import sys
import os
import datetime
from os import environ



# Add project path for database modules (adjusting for 'hardware/ai_modules' depth)
# Current file is in: root/hardware/ai_modules/face_recognizer.py
# Needed root: ../../../
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from database_modules.employee_crud import get_all_employees
    from database_modules.attendance_logger import mark_attendance
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running from the project root.")
    sys.exit(1)

# Try to import picamera2 for Pi OS Bookworm
PICAMERA2_AVAILABLE = False
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
    print("picamera2 library found.")
except ImportError:
    print("picamera2 not available, will try OpenCV backends.")

class PiCameraWrapper:
    """Wrapper to make Picamera2 behave like cv2.VideoCapture"""
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
        # Convert RGB to BGR for OpenCV compatibility
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
    # 1. Try picamera2 (BEST for Pi OS Bookworm)
    if PICAMERA2_AVAILABLE:
        print("Attempting Picamera2 connection...")
        try:
            cam = PiCameraWrapper()
            ret, _ = cam.read()
            if ret:
                print("Picamera2 backend works!")
                return cam
        except Exception as e:
            print(f"Picamera2 failed: {e}")

    # 2. Try GStreamer (Native Libcamera support)
    print("Attempting GStreamer connection...")
    gst_pipeline = (
        "libcamerasrc ! video/x-raw, width=640, height=480, framerate=15/1 ! "
        "videoconvert ! video/x-raw, format=BGR ! appsink drop=1"
    )
    try:
        cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        if cap.isOpened():
            ret, _ = cam.read()
            if ret:
                print("GStreamer backend works!")
                return cap
        cap.release()
    except Exception as e:
        print(f"GStreamer failed: {e}")

    # 3. Try V4L2 (Standard for libcamerify)
    print("Attempting V4L2 connection...")
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print("V4L2 backend works!")
                return cap
        cap.release()
    except Exception as e:
        print(f"V4L2 failed: {e}")

    # 4. Try Default (Fallback)
    print("Attempting Default connection...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print("Default backend works!")
                return cap
    except Exception as e:
        print(f"Default failed: {e}")
            
    return None


# ... (Camera Classes remain the same) ...


# ... (Camera Classes remain the same) ...


# ... (Camera Classes remain the same) ...

# NEW: Anti-Spoofing (Liveness) Logic v3 - STRICT CHALLENGE
import math
import random
import time

def calculate_ear(eye_points):
    """
    Calculate Eye Aspect Ratio (EAR) for blinking.
    """
    A = math.hypot(eye_points[1][0] - eye_points[5][0], eye_points[1][1] - eye_points[5][1])
    B = math.hypot(eye_points[2][0] - eye_points[4][0], eye_points[2][1] - eye_points[4][1])
    C = math.hypot(eye_points[0][0] - eye_points[3][0], eye_points[0][1] - eye_points[3][1])
    if C == 0: return 0
    return (A + B) / (2.0 * C)

def calculate_mar(mouth_points):
    """
    Calculate Mouth Aspect Ratio (MAR) for smiling/opening mouth.
    Using vertical distance of inner lip (or outer) vs horizontal width.
    """
    # Using outer lip points for simplicity and robustness with standard 68-point model
    # Top Lip: points 0-6 (outer), Bottom Lip: 0-6 (outer) in their respective lists?
    # No, face_recognition api returns dictionary.
    # 'top_lip' and 'bottom_lip' are lists.
    
    top_lip = mouth_points['top_lip']
    bottom_lip = mouth_points['bottom_lip']
    
    # Vertical: Top lip bottom edge (approx index 9) to Bottom lip top edge (approx index 9)
    # Using center points
    top_point = top_lip[9] 
    bottom_point = bottom_lip[9]
    
    # Horizontal: Mouth Corner Left (top_lip[0]) to Mouth Corner Right (top_lip[6])
    left_point = top_lip[0]
    right_point = top_lip[6]
    
    vert_dist = math.hypot(top_point[0] - bottom_point[0], top_point[1] - bottom_point[1])
    horiz_dist = math.hypot(left_point[0] - right_point[0], left_point[1] - right_point[1])
    
    if horiz_dist == 0: return 0
    return vert_dist / horiz_dist

def start_recognition_camera():
    print("\nSTARTING FACE RECOGNITION SYSTEM")
    
    # ... (Supabase checks) ...
    url = environ.get('SUPABASE_URL', '').strip()
    key = environ.get('SUPABASE_KEY', '').strip()
    if not url or not key:
        print("\nCRITICAL ERROR: Supabase credentials missing!")
        return

    # Loading message
    print("Loading employee data from database...")
    try:
        employees_data = get_all_employees()
    except Exception as e:
        print(f"Database Error: {e}")
        return
    
    known_face_encodings = []
    known_face_names = []
    known_face_ids = [] 
    
    for employee in employees_data:
        known_face_encodings.append(employee['encoding'])
        known_face_names.append(employee['name'])
        known_face_ids.append(employee['id'])
    
    print(f"System Ready: Loaded {len(known_face_names)} employees.")
    
    # Initialize Camera
    video_capture = get_camera()
    if video_capture is None:
        print("CRITICAL ERROR: Could not open any camera.")
        return

    print("Camera Started.")
    print("Strict Challenge Mode: Neutral -> Action -> Verify")
    print("To Exit: Press 'q' or 'ESC'.")
    
    window_name = 'Smart Attendance - Liveness Check'

    # --- Thresholds ---
    EYE_AR_THRESH = 0.22      # Below this = Blink
    EYE_AR_OPEN_THRESH = 0.25 # Above this = Open Check
    MOUTH_AR_THRESH = 0.35    # REDUCED: Easier to trigger Open Mouth (was 0.40)
    MOUTH_AR_CLOSED_THRESH = 0.30 # Below this = Mouth Closed
    
    # --- State Machine for Challenge ---
    # States: 'IDLE', 'CHECKING_NEUTRAL', 'ISSUING_CHALLENGE', 'WAITING_FOR_ACTION', 'VERIFIED'
    current_state = 'IDLE'
    current_person = None
    challenge_type = None # 'BLINK' or 'SMILE'
    state_start_time = 0
    
    # Success tracking
    verification_success_time = 0
    display_message = "Scan Face..."
    message_color = (255, 255, 255)

    last_attendance_time = 0
    ATTENDANCE_COOLDOWN = 60 # Seconds between marking same person
    
    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        try:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        except Exception:
            continue
            
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # 1. Face Detection
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame, face_locations)

        # Logic for Single Primary Face
        if not face_locations:
            current_state = 'IDLE'
            current_person = None
            display_message = "Scan Face..."
            message_color = (200, 200, 200) # Gray
            challenge_type = None
        else:
            # Process First Face Only
            face_encoding = face_encodings[0]
            landmarks = face_landmarks_list[0]
            (top, right, bottom, left) = face_locations[0]
            
            # --- Metrics Calculation ---
            left_eye = landmarks['left_eye']
            right_eye = landmarks['right_eye']
            ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0
            mar = calculate_mar(landmarks)
            
            # Identify
            name = "Unknown"
            employee_id = None
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    employee_id = known_face_ids[best_match_index]

            # --- Strict State Machine ---
            
            # Reset if person changes
            if current_person != name and name != "Unknown":
                current_person = name
                current_state = 'IDLE'
            
            if name == "Unknown":
                display_message = "Unknown User"
                message_color = (0, 0, 255)
                current_state = 'IDLE'
            
            elif current_state == 'IDLE':
                # Start Fresh
                current_state = 'CHECKING_NEUTRAL'
                state_start_time = time.time()
                display_message = "Keep Face Still..."
                message_color = (255, 255, 0) # Cyan
                baseline_ear = ear
                baseline_mar = mar
                
            elif current_state == 'CHECKING_NEUTRAL':
                # Update baselines continually while neutral
                # Alpha blending for smooth baseline: new = 0.1*curr + 0.9*old
                baseline_ear = 0.1 * ear + 0.9 * baseline_ear
                baseline_mar = 0.1 * mar + 0.9 * baseline_mar

                # Standard stillness check (Ensure eyes open, mouth closed-ish)
                # Relaxed absolute thresholds, rely on delta later
                if ear > 0.20 and mar < 0.35:
                    if time.time() - state_start_time > 1.0: # 1.0s of stillness (Faster)
                        current_state = 'ISSUING_CHALLENGE'
                else:
                    # Reset timer if they move/blink/talk
                    state_start_time = time.time() 
                    display_message = "Keep Face Still..."
            
            elif current_state == 'ISSUING_CHALLENGE':
                # Pick Random Challenge 
                challenge_type = random.choice(['BLINK', 'OPEN MOUTH'])
                current_state = 'WAITING_FOR_ACTION'
                state_start_time = time.time()
                display_message = f"PLEASE {challenge_type} NOW!"
                message_color = (0, 255, 255) # Yellow
            
            elif current_state == 'WAITING_FOR_ACTION':
                # Timeout
                if time.time() - state_start_time > 4.0:
                    current_state = 'IDLE'
                    display_message = "Too Slow. Retry."
                
                success = False
                
                if challenge_type == 'BLINK':
                    # Looking for significant drop in EAR (Closing eyes)
                    # Must be < baseline - 0.05 AND < absolute 0.2
                    if ear < (baseline_ear - 0.05) and ear < 0.20:
                        success = True
                    # Fail if they open mouth instead (significant increase in MAR)
                    if mar > (baseline_mar + 0.10):
                        current_state = 'IDLE'
                        display_message = "Wrong Action!"
                        
                elif challenge_type == 'OPEN MOUTH':
                    # Looking for significant increase in MAR (Opening mouth)
                    # Must be > baseline + 0.10
                    if mar > (baseline_mar + 0.10):
                        success = True
                    
                if success:
                    current_state = 'VERIFIED'
                    verification_success_time = time.time()
                    
                    # MARK ATTENDANCE
                    if time.time() - last_attendance_time > ATTENDANCE_COOLDOWN:
                        # Fetch readable time for display
                        now_disp = datetime.datetime.now()
                        time_disp = now_disp.strftime("%H:%M:%S")
                        date_disp = now_disp.strftime("%Y-%m-%d")
                        
                        # Determine Status for Console Output
                        current_hour = now_disp.hour
                        status_disp = "Present"
                        if 7 <= current_hour < 12:
                            status_disp = "Morning Check-In (تسجيل دخول صباحي)"
                        elif 12 <= current_hour < 13:
                            status_disp = "Morning Check-Out (تسجيل خروج صباحي)"
                        elif 13 <= current_hour < 16:
                            status_disp = "Afternoon Check-In (تسجيل دخول مسائي)"
                        elif 16 <= current_hour < 19:
                            status_disp = "Afternoon Check-Out (تسجيل خروج مسائي)"

                        print(f"Verified: {name} | {date_disp} | {time_disp} | {status_disp}")
                        
                        threading_success = mark_attendance(employee_id)
                        if threading_success:
                             # The logger handles the detailed print, but we can confirm here
                             pass
                            
                        last_attendance_time = time.time()
                    
                    display_message = "VERIFIED!"
                    message_color = (0, 255, 0) # Green

            elif current_state == 'VERIFIED':
                display_message = f"Welcome {name}"
                message_color = (0, 255, 0)
                if time.time() - verification_success_time > 3.0:
                    current_state = 'IDLE'
                    current_person = None

            # --- Drawing UI ---
            top *= 4; right *= 4; bottom *= 4; left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), message_color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), message_color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 1)

            # Metrics for Debug (Enabled for tuning)
            # cv2.putText(frame, f"EAR: {ear:.2f} MAR: {mar:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Challenge Overlay
            cv2.putText(frame, display_message, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, message_color, 3)

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            print("Exiting system...")
            break
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            print("Window closed by user.")
            break

    video_capture.release()
    cv2.destroyAllWindows()
