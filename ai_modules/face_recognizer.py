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

def get_camera():
    """
    Try to open camera using different backends.
    Best for Raspberry Pi Bookworm is GStreamer or V4L2 via libcamerify.
    """
    # 1. Try GStreamer (Native Libcamera support)
    print("📷 Attempting GStreamer connection...")
    gst_pipeline = (
        "libcamerasrc ! video/x-raw, width=640, height=480, framerate=15/1 ! "
        "videoconvert ! video/x-raw, format=BGR ! appsink drop=1"
    )
    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
    if cap.isOpened():
        ret, _ = cap.read()
        if ret:
            print("✅ GStreamer backend works!")
            return cap
    cap.release()

    # 2. Try V4L2 (Standard for libcamerify)
    print("📷 Attempting V4L2 connection...")
    # Using specific index -1 to let OpenCV choose best V4L2 device
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    # Set safe common resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if cap.isOpened():
        ret, _ = cap.read()
        if ret:
            print("✅ V4L2 backend works!")
            return cap
    cap.release()

    # 3. Try Default (Fallback)
    print("📷 Attempting Default connection...")
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, _ = cap.read()
        if ret:
            print("✅ Default backend works!")
            return cap
            
    return None

def start_recognition_camera():
    # 1. Check Credentials FIRST
    url = environ.get('SUPABASE_URL')
    key = environ.get('SUPABASE_KEY')
    
    if not url or not key:
        print("\n❌ CRITICAL ERROR: Supabase credentials missing from environment!")
        print(f"   URL: {'[SET]' if url else '[MISSING]'}")
        print(f"   KEY: {'[SET]' if key else '[MISSING]'}")
        print("➡️  Please edit your .env file: 'nano .env'")
        return

    if "your_url_here" in url or "http" not in url:
        print(f"\n❌ CRITICAL ERROR: Invalid Supabase URL: '{url}'")
        print("➡️  It normally starts with 'https://' and looks like 'https://xyz.supabase.co'")
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
    
    # Load into RAM
    for employee in employees_data:
        known_face_encodings.append(employee['encoding'])
        known_face_names.append(employee['name'])
        known_face_ids.append(employee['id'])
    
    print(f"✅ System Ready: Loaded {len(known_face_names)} employees.")
    
    # 2. Initialize Camera
    video_capture = get_camera()
    
    if video_capture is None or not video_capture.isOpened():
        print("❌ CRITICAL ERROR: Could not open any camera.")
        print("ℹ️  Try running with: libcamerify python start_system.py")
        return

    print("📷 Camera Started.")
    print("ℹ️  To Exit: Press 'q', 'ESC', or click the 'X' button on the window.")
    
    window_name = 'Smart Attendance System'

    while True:
        # Read frame
        ret, frame = video_capture.read()
        if not ret:
            print("❌ Error: Could not read frame from camera.")
            break

        # Resize for speed
        try:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        except Exception:
            continue
            
        # Color conversion BGR -> RGB
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []

        for face_encoding in face_encodings:
            # Compare faces
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"
            
            # Distance logic
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    employee_id = known_face_ids[best_match_index]
                    
                    # Mark attendance in DB
                    is_new_attendance = mark_attendance(employee_id)
                    
                    if is_new_attendance:
                        print(f"🔔 Notification: {name} is present!")

            face_names.append(name)

        # Draw results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Color (Green for known, Red for unknown)
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            
            # Draw box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw label
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)

        # Show window
        cv2.imshow(window_name, frame)

        # Listen for exit keys
        key = cv2.waitKey(1) & 0xFF

        # Exit on 'q' or 'ESC'
        if key == ord('q') or key == 27:
            print("🛑 Exiting system...")
            break

        # Exit on window close
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            print("🛑 Window closed by user.")
            break

    video_capture.release()
    cv2.destroyAllWindows()