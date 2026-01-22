# name file: ai_modules/face_recognizer.py
import cv2
import face_recognition
import numpy as np
import sys
import os

# Add project path for database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_modules.employee_crud import get_all_employees
from database_modules.attendance_logger import mark_attendance

def start_recognition_camera():
    # Loading message
    print("⏳ Loading employee data from database...")
    
    employees_data = get_all_employees()
    
    known_face_encodings = []
    known_face_names = []
    known_face_ids = [] 
    
    # Load into RAM
    for employee in employees_data:
        known_face_encodings.append(employee['encoding'])
        known_face_names.append(employee['name'])
        known_face_ids.append(employee['id'])
    
    print(f"✅ System Ready: Loaded {len(known_face_names)} employees.")
    print("📷 Camera Started.")
    print("ℹ️  To Exit: Press 'q', 'ESC', or click the 'X' button on the window.")
    
    # Open camera with V4L2 backend (specifically for Pi)
    video_capture = cv2.VideoCapture(0, cv2.CAP_V4L2)
    
    # Set Resolution and Format to avoid libcamerify crash
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    video_capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    window_name = 'Smart Attendance System'

    while True:
        # Read frame
        ret, frame = video_capture.read()
        if not ret:
            print("❌ Error: Could not read frame from camera.")
            break

        # Resize for speed
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
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