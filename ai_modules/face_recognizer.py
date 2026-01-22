# name file: ai_modules/face_recognizer.py
import cv2
import face_recognition
import numpy as np
import sys
import os
from os import environ

# Add project path for database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from database_modules.employee_crud import get_all_employees
    from database_modules.attendance_logger import mark_attendance
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Ensure you are running from the project root.")
    sys.exit(1)

# Try to import picamera2 for Pi OS Bookworm
PICAMERA2_AVAILABLE = False
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
    print("✅ picamera2 library found.")
except ImportError:
    print("ℹ️  picamera2 not available, will try OpenCV backends.")

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
        print("📷 Attempting Picamera2 connection...")
        try:
            cam = PiCameraWrapper()
            ret, _ = cam.read()
            if ret:
                print("✅ Picamera2 backend works!")
                return cam
        except Exception as e:
            print(f"⚠️ Picamera2 failed: {e}")

    # 2. Try GStreamer (Native Libcamera support)
    print("📷 Attempting GStreamer connection...")
    gst_pipeline = (
        "libcamerasrc ! video/x-raw, width=640, height=480, framerate=15/1 ! "
        "videoconvert ! video/x-raw, format=BGR ! appsink drop=1"
    )
    try:
        cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print("✅ GStreamer backend works!")
                return cap
        cap.release()
    except Exception as e:
        print(f"⚠️ GStreamer failed: {e}")

    # 3. Try V4L2 (Standard for libcamerify)
    print("📷 Attempting V4L2 connection...")
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print("✅ V4L2 backend works!")
                return cap
        cap.release()
    except Exception as e:
        print(f"⚠️ V4L2 failed: {e}")

    # 4. Try Default (Fallback)
    print("📷 Attempting Default connection...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print("✅ Default backend works!")
                return cap
    except Exception as e:
        print(f"⚠️ Default failed: {e}")
            
    return None

def start_recognition_camera():
    print("\n🔵 STARTING FACE RECOGNITION (Version 4.0 - Picamera2)")
    
    # 1. Check Credentials FIRST
    url = environ.get('SUPABASE_URL', '').strip()
    key = environ.get('SUPABASE_KEY', '').strip()
    
    if not url or not key:
        print("\n❌ CRITICAL ERROR: Supabase credentials missing!")
        print("➡️  Please edit your .env file: 'nano .env'")
        return

    if not url.startswith("http"):
        print(f"\n❌ CRITICAL ERROR: Invalid Supabase URL: '{url}'")
        print("➡️  The URL must start with 'https://'")
        return

    # Loading message
    print("⏳ Loading employee data from database...")
    
    try:
        employees_data = get_all_employees()
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return
    
    known_face_encodings = []
    known_face_names = []
    known_face_ids = [] 
    
    for employee in employees_data:
        known_face_encodings.append(employee['encoding'])
        known_face_names.append(employee['name'])
        known_face_ids.append(employee['id'])
    
    print(f"✅ System Ready: Loaded {len(known_face_names)} employees.")
    
    # 2. Initialize Camera
    video_capture = get_camera()
    
    if video_capture is None:
        print("❌ CRITICAL ERROR: Could not open any camera.")
        return

    print("📷 Camera Started.")
    print("ℹ️  To Exit: Press 'q' or 'ESC'.")
    
    window_name = 'Smart Attendance System'

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("❌ Error: Could not read frame.")
            break

        try:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        except Exception:
            continue
            
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"
            
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    employee_id = known_face_ids[best_match_index]
                    
                    is_new_attendance = mark_attendance(employee_id)
                    
                    if is_new_attendance:
                        print(f"🔔 Notification: {name} is present!")

            face_names.append(name)

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == 27:
            print("🛑 Exiting system...")
            break

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            print("🛑 Window closed by user.")
            break

    video_capture.release()
    cv2.destroyAllWindows()