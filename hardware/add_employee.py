
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import face_recognition
import numpy as np
import sys
import os

# Add project path to find database modules
# Current file: hardware/add_employee.py
# Root: ../../
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database_modules.employee_crud import add_new_employee
except ImportError as e:
    print(f"❌ Error importing database modules: {e}")
    sys.exit(1)

class EmployeeRegistrationApp:
    def __init__(self, window, window_title="Smart Attendance - Registration"):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("800x600")

        # Variables
        self.video_source = 0
        self.vid = cv2.VideoCapture(self.video_source)
        
        if not self.vid.isOpened():
             messagebox.showerror("Error", "Unable to open camera source")
             sys.exit(1)

        self.current_frame = None
        self.captured_frame = None
        self.face_encoding = None

        # --- UI Layout ---
        
        # Left Side: Camera
        self.camera_frame = tk.Frame(window, width=400, height=400)
        self.camera_frame.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.camera_frame, width=400, height=300)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.btn_capture = tk.Button(self.camera_frame, text="📸 Capture Face", width=30, command=self.capture_face, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.btn_capture.pack(pady=10)
        
        self.lbl_status = tk.Label(self.camera_frame, text="Status: Ready", fg="blue")
        self.lbl_status.pack(pady=5)

        # Right Side: Form
        self.form_frame = tk.Frame(window, width=300)
        self.form_frame.pack(side=tk.RIGHT, padx=20, fill=tk.Y)

        tk.Label(self.form_frame, text="New Employee Details", font=("Arial", 16, "bold")).pack(pady=20)

        # Fields
        self.entry_name = self.create_input_field("Full Name")
        self.entry_code = self.create_input_field("Employee Code")
        self.entry_email = self.create_input_field("Email")
        self.entry_dept = self.create_input_field("Department")

        # Submit Button
        self.btn_save = tk.Button(self.form_frame, text="✅ Save Employee", width=25, command=self.save_employee, bg="#2196F3", fg="white", font=("Arial", 12, "bold"))
        self.btn_save.pack(pady=30)
        
        self.btn_retake = tk.Button(self.form_frame, text="🔄 Retake Photo", width=25, command=self.retake_photo, state=tk.DISABLED)
        self.btn_retake.pack(pady=5)

        # Loop
        self.delay = 15
        self.update()

        self.window.mainloop()

    def create_input_field(self, label_text):
        frame = tk.Frame(self.form_frame)
        frame.pack(pady=5, fill=tk.X)
        tk.Label(frame, text=label_text, anchor="w").pack(fill=tk.X)
        entry = tk.Entry(frame, font=("Arial", 12))
        entry.pack(fill=tk.X)
        return entry

    def update(self):
        if self.captured_frame is None:
            ret, frame = self.vid.read()
            if ret:
                self.current_frame = frame
                # OpenCV uses BGR, Tkinter uses RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize to fit canvas logic if needed, but for now just display
                # Ideally resize to fixed size
                frame_resized = cv2.resize(frame_rgb, (400, 300))
                
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_resized))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        
        self.window.after(self.delay, self.update)

    def capture_face(self):
        if self.current_frame is not None:
            self.captured_frame = self.current_frame.copy()
            
            # Show processing
            self.lbl_status.config(text="Status: Processing...", fg="orange")
            self.window.update_idletasks()

            # Detect Face
            rgb_frame = cv2.cvtColor(self.captured_frame, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb_frame)
            
            if len(boxes) == 0:
                messagebox.showwarning("No Face", "No face detected! Please try again.")
                self.captured_frame = None
                self.lbl_status.config(text="Status: No face detected", fg="red")
                return
            
            if len(boxes) > 1:
                 messagebox.showwarning("Multiple Faces", "Multiple faces detected! Please ensure only one person is in frame.")
                 self.captured_frame = None
                 self.lbl_status.config(text="Status: Multiple faces", fg="red")
                 return

            # Encode
            try:
                encodings = face_recognition.face_encodings(rgb_frame, boxes)
                if len(encodings) > 0:
                    self.face_encoding = encodings[0]
                    self.lbl_status.config(text="Status: Face Captured & Encoded ✅", fg="green")
                    self.btn_capture.config(state=tk.DISABLED)
                    self.btn_retake.config(state=tk.NORMAL)
                    
                    # Draw box on captured frame for visual confirmation
                    top, right, bottom, left = boxes[0]
                    cv2.rectangle(self.captured_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    frame_rgb = cv2.cvtColor(self.captured_frame, cv2.COLOR_BGR2RGB)
                    frame_resized = cv2.resize(frame_rgb, (400, 300))
                    self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_resized))
                    self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
                else:
                     messagebox.showwarning("Error", "Could not encode face.")
                     self.captured_frame = None
            except Exception as e:
                print(e)
                messagebox.showerror("Error", f"Encoding error: {e}")
                self.captured_frame = None

    def retake_photo(self):
        self.captured_frame = None
        self.face_encoding = None
        self.btn_capture.config(state=tk.NORMAL)
        self.btn_retake.config(state=tk.DISABLED)
        self.lbl_status.config(text="Status: Ready", fg="blue")

    def save_employee(self):
        # 1. Validate Inputs
        name = self.entry_name.get().strip()
        code = self.entry_code.get().strip()
        email = self.entry_email.get().strip()
        dept = self.entry_dept.get().strip() or "General"

        if not name or not code or not email:
            messagebox.showwarning("Missing Info", "Please fill in Name, Code, and Email.")
            return

        if self.face_encoding is None:
            messagebox.showwarning("Missing Face", "Please capture a face first.")
            return

        # 2. Call CRUD
        self.lbl_status.config(text="Status: Saving to Database...", fg="blue")
        self.window.update_idletasks()

        try:
            success = add_new_employee(name, code, email, self.face_encoding, dept)
            
            if success:
                messagebox.showinfo("Success", f"Employee {name} added successfully!")
                self.clear_form()
            else:
                messagebox.showerror("Error", "Failed to add employee. Check console/logs for details (e.g., duplicates).")
                self.lbl_status.config(text="Status: Error Saving", fg="red")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.lbl_status.config(text="Status: Error", fg="red")

    def clear_form(self):
        self.entry_name.delete(0, tk.END)
        self.entry_code.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.entry_dept.delete(0, tk.END)
        self.retake_photo()


if __name__ == "__main__":
    # Check for dependencies
    try:
        import tkinter
    except ImportError:
        print("❌ Tkinter is not installed. Please install 'python3-tk' (Linux) or run with standard Python.")
        sys.exit(1)

    root = tk.Tk()
    app = EmployeeRegistrationApp(root)
