# File Name: ai_modules/face_encoder.py
import face_recognition
import os
import sys

# Add project root path to allow importing database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Changed from student_crud to employee_crud for consistency
from database_modules.employee_crud import add_new_employee

def register_new_employee(image_path, name, employee_code, email):
    """
    Comprehensive function that performs the following:
    1. Load the image
    2. Extract face encoding
    3. Save data to the database
    """
    
    # Check if image file exists
    if not os.path.exists(image_path):
        print(f"Error: The image file is not found in the path: {image_path}")
        return False

    print(f"Processing image for: {name} ...")
    
    try:
        # 1. Load image using face_recognition library
        image = face_recognition.load_image_file(image_path)
        
        # 2. Find faces in the image
        # This step returns a list of all faces found (we expect one face)
        face_encodings = face_recognition.face_encodings(image)
        
        # Check if a face was found
        if len(face_encodings) == 0:
            print("Warning: No face was found in the picture! Please use a clear picture.")
            return False
        
        if len(face_encodings) > 1:
            print("Warning: There is more than one face in the picture! Please use only a personal photo of the employee.")
            return False

        # Take the first face found (since we expect one face)
        employee_face_encoding = face_encodings[0]
        
        # 3. Send data to save in the database
        # Call the function we wrote previously in employee_crud
        result = add_new_employee(name, employee_code, email, employee_face_encoding)
        
        return result

    except Exception as e:
        print(f"An error occurred while processing the image: {e}")
        return False
