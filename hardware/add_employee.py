
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import face_recognition
import numpy as np
import sys
import os

# Add project path to find database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database_modules.employee_crud import add_new_employee
    from ai_modules.face_recognizer import get_camera
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# --- Color Palette ---
BG_COLOR = "#1a1a2e"
CARD_COLOR = "#16213e"
ACCENT_COLOR = "#0f3460"
PRIMARY_COLOR = "#e94560"
SUCCESS_COLOR = "#00b894"
WARNING_COLOR = "#fdcb6e"
TEXT_COLOR = "#ffffff"
SUBTEXT_COLOR = "#a0a0b0"

# --- Department Options ---
DEPARTMENTS = [
    "Administration",
    "Human Resources",
    "Information Technology",
    "Finance",
    "Marketing",
    "Operations",
    "Engineering",
    "Security",
    "General",
]

REQUIRED_PHOTOS = 3


class EmployeeRegistrationApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Smart Attendance - Employee Registration")
        self.window.geometry("900x650")
        self.window.configure(bg=BG_COLOR)
        self.window.resizable(False, False)

        # State
        self.captured_encodings = []  # List of numpy arrays
        self.current_frame = None
        self.camera_active = True

        # Initialize Camera
        print("Initializing camera...")
        self.vid = get_camera()
        if self.vid is None or not self.vid.isOpened():
            messagebox.showerror("Error", "Unable to open camera source")
            sys.exit(1)
        print("Camera ready!")

        # --- Style ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=ACCENT_COLOR, background=ACCENT_COLOR, foreground=TEXT_COLOR)

        # ==================== HEADER ====================
        header = tk.Frame(window, bg=PRIMARY_COLOR, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="Employee Registration", font=("Arial", 18, "bold"),
                 bg=PRIMARY_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=20, pady=10)
        tk.Label(header, text=f"Capture {REQUIRED_PHOTOS} photos per employee",
                 font=("Arial", 10), bg=PRIMARY_COLOR, fg="#ffcccc").pack(side=tk.RIGHT, padx=20)

        # ==================== MAIN CONTENT ====================
        main_frame = tk.Frame(window, bg=BG_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # --- LEFT: Camera Section ---
        cam_card = tk.Frame(main_frame, bg=CARD_COLOR, relief=tk.FLAT, bd=0)
        cam_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        tk.Label(cam_card, text="Camera Preview", font=("Arial", 12, "bold"),
                 bg=CARD_COLOR, fg=TEXT_COLOR).pack(pady=(15, 5))

        self.canvas = tk.Canvas(cam_card, width=420, height=320, bg="#000000",
                                highlightthickness=1, highlightbackground=ACCENT_COLOR)
        self.canvas.pack(padx=15, pady=5)

        # Capture Button
        self.btn_capture = tk.Button(cam_card, text=f"Capture Photo (0/{REQUIRED_PHOTOS})",
                                     font=("Arial", 13, "bold"), bg=PRIMARY_COLOR, fg=TEXT_COLOR,
                                     activebackground="#c0392b", activeforeground=TEXT_COLOR,
                                     relief=tk.FLAT, cursor="hand2", width=25, height=1,
                                     command=self.capture_face)
        self.btn_capture.pack(pady=8)

        # Status
        self.lbl_status = tk.Label(cam_card, text="Status: Ready - Position face in camera",
                                   font=("Arial", 10), bg=CARD_COLOR, fg=SUBTEXT_COLOR)
        self.lbl_status.pack(pady=(0, 5))

        # Photo Indicators
        indicator_frame = tk.Frame(cam_card, bg=CARD_COLOR)
        indicator_frame.pack(pady=(0, 15))
        tk.Label(indicator_frame, text="Photos:", font=("Arial", 10),
                 bg=CARD_COLOR, fg=SUBTEXT_COLOR).pack(side=tk.LEFT, padx=5)
        self.photo_indicators = []
        for i in range(REQUIRED_PHOTOS):
            lbl = tk.Label(indicator_frame, text=f"  {i+1}  ", font=("Arial", 10, "bold"),
                           bg=ACCENT_COLOR, fg=SUBTEXT_COLOR, relief=tk.FLAT, padx=8, pady=2)
            lbl.pack(side=tk.LEFT, padx=3)
            self.photo_indicators.append(lbl)

        # --- RIGHT: Form Section ---
        form_card = tk.Frame(main_frame, bg=CARD_COLOR, relief=tk.FLAT, bd=0, width=320)
        form_card.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        form_card.pack_propagate(False)

        tk.Label(form_card, text="Employee Details", font=("Arial", 12, "bold"),
                 bg=CARD_COLOR, fg=TEXT_COLOR).pack(pady=(20, 15))

        # Input Fields
        self.entry_name = self._create_field(form_card, "Full Name")
        self.entry_code = self._create_field(form_card, "Employee Code")
        self.entry_email = self._create_field(form_card, "Email Address")

        # Department Dropdown
        dept_frame = tk.Frame(form_card, bg=CARD_COLOR)
        dept_frame.pack(padx=20, pady=8, fill=tk.X)
        tk.Label(dept_frame, text="Department", font=("Arial", 10),
                 bg=CARD_COLOR, fg=SUBTEXT_COLOR, anchor="w").pack(fill=tk.X)
        self.dept_var = tk.StringVar(value="General")
        self.dept_combo = ttk.Combobox(dept_frame, textvariable=self.dept_var,
                                        values=DEPARTMENTS, state="readonly",
                                        font=("Arial", 12))
        self.dept_combo.pack(fill=tk.X, pady=(3, 0), ipady=4)

        # Spacer
        tk.Frame(form_card, bg=CARD_COLOR, height=15).pack()

        # Save Button
        self.btn_save = tk.Button(form_card, text="Save Employee",
                                   font=("Arial", 13, "bold"), bg=SUCCESS_COLOR, fg=TEXT_COLOR,
                                   activebackground="#00a884", activeforeground=TEXT_COLOR,
                                   relief=tk.FLAT, cursor="hand2", width=20, height=1,
                                   command=self.save_employee, state=tk.DISABLED)
        self.btn_save.pack(pady=5)

        # Reset Button
        self.btn_reset = tk.Button(form_card, text="Reset All",
                                    font=("Arial", 11), bg=ACCENT_COLOR, fg=SUBTEXT_COLOR,
                                    activebackground="#1a2a5e", activeforeground=TEXT_COLOR,
                                    relief=tk.FLAT, cursor="hand2", width=20,
                                    command=self.reset_form)
        self.btn_reset.pack(pady=5)

        # Info Label
        tk.Label(form_card, text=f"Capture {REQUIRED_PHOTOS} different angles\nfor better recognition accuracy",
                 font=("Arial", 9), bg=CARD_COLOR, fg=SUBTEXT_COLOR,
                 justify=tk.CENTER).pack(pady=(20, 10))

        # ==================== FOOTER ====================
        footer = tk.Frame(window, bg=ACCENT_COLOR, height=30)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="Smart Attendance System v2.0", font=("Arial", 9),
                 bg=ACCENT_COLOR, fg=SUBTEXT_COLOR).pack(pady=5)

        # Start camera loop
        self.delay = 30
        self.update_camera()
        self.window.mainloop()

    def _create_field(self, parent, label_text):
        frame = tk.Frame(parent, bg=CARD_COLOR)
        frame.pack(padx=20, pady=8, fill=tk.X)
        tk.Label(frame, text=label_text, font=("Arial", 10),
                 bg=CARD_COLOR, fg=SUBTEXT_COLOR, anchor="w").pack(fill=tk.X)
        entry = tk.Entry(frame, font=("Arial", 12), bg=ACCENT_COLOR, fg=TEXT_COLOR,
                         insertbackground=TEXT_COLOR, relief=tk.FLAT, bd=0)
        entry.pack(fill=tk.X, pady=(3, 0), ipady=6)
        return entry

    def update_camera(self):
        if self.camera_active:
            ret, frame = self.vid.read()
            if ret:
                self.current_frame = frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (420, 320))

                # Draw face detection overlay
                small = cv2.resize(frame_rgb, (0, 0), fx=0.25, fy=0.25)
                face_locs = face_recognition.face_locations(small)
                if face_locs:
                    for (top, right, bottom, left) in face_locs:
                        top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
                        # Scale to canvas size
                        h, w = frame_rgb.shape[:2]
                        sx, sy = 420 / w, 320 / h
                        cv2.rectangle(frame_resized,
                                      (int(left * sx), int(top * sy)),
                                      (int(right * sx), int(bottom * sy)),
                                      (233, 69, 96), 2)

                self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_resized))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update_camera)

    def capture_face(self):
        if self.current_frame is None:
            self.lbl_status.config(text="Status: No camera frame available", fg=WARNING_COLOR)
            return

        if len(self.captured_encodings) >= REQUIRED_PHOTOS:
            self.lbl_status.config(text="Status: All photos captured!", fg=SUCCESS_COLOR)
            return

        self.lbl_status.config(text="Status: Processing...", fg=WARNING_COLOR)
        self.window.update_idletasks()

        rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb_frame)

        if len(boxes) == 0:
            self.lbl_status.config(text="Status: No face detected! Try again.", fg=PRIMARY_COLOR)
            return

        if len(boxes) > 1:
            self.lbl_status.config(text="Status: Multiple faces! Only 1 person please.", fg=PRIMARY_COLOR)
            return

        try:
            encodings = face_recognition.face_encodings(rgb_frame, boxes)
            if len(encodings) > 0:
                self.captured_encodings.append(encodings[0])
                count = len(self.captured_encodings)

                # Update indicator
                self.photo_indicators[count - 1].config(bg=SUCCESS_COLOR, fg=TEXT_COLOR)

                # Update button text
                self.btn_capture.config(text=f"Capture Photo ({count}/{REQUIRED_PHOTOS})")

                if count >= REQUIRED_PHOTOS:
                    self.btn_capture.config(state=tk.DISABLED, bg=ACCENT_COLOR)
                    self.btn_save.config(state=tk.NORMAL)
                    self.camera_active = False
                    self.lbl_status.config(
                        text=f"Status: All {REQUIRED_PHOTOS} photos captured! Fill details & Save.",
                        fg=SUCCESS_COLOR)
                else:
                    remaining = REQUIRED_PHOTOS - count
                    self.lbl_status.config(
                        text=f"Status: Photo {count} captured! {remaining} more needed. Change angle.",
                        fg=SUCCESS_COLOR)
            else:
                self.lbl_status.config(text="Status: Could not encode face.", fg=PRIMARY_COLOR)
        except Exception as e:
            print(f"Encoding error: {e}")
            self.lbl_status.config(text=f"Status: Error - {e}", fg=PRIMARY_COLOR)

    def save_employee(self):
        name = self.entry_name.get().strip()
        code = self.entry_code.get().strip()
        email = self.entry_email.get().strip()
        dept = self.dept_var.get()

        if not name or not code or not email:
            messagebox.showwarning("Missing Info", "Please fill in Name, Code, and Email.")
            return

        if len(self.captured_encodings) < REQUIRED_PHOTOS:
            messagebox.showwarning("Missing Photos", f"Please capture {REQUIRED_PHOTOS} photos first.")
            return

        self.lbl_status.config(text="Status: Computing average encoding...", fg=WARNING_COLOR)
        self.window.update_idletasks()

        # Average all encodings for better accuracy
        avg_encoding = np.mean(self.captured_encodings, axis=0)

        self.lbl_status.config(text="Status: Saving to database...", fg=WARNING_COLOR)
        self.window.update_idletasks()

        try:
            success = add_new_employee(name, code, email, avg_encoding, dept)
            if success:
                messagebox.showinfo("Success", f"Employee '{name}' has been registered successfully!")
                self.reset_form()
            else:
                self.lbl_status.config(text="Status: Failed to save. Check console.", fg=PRIMARY_COLOR)
                messagebox.showerror("Error", "Failed to add employee. Possible duplicate face or code.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.lbl_status.config(text="Status: Error", fg=PRIMARY_COLOR)

    def reset_form(self):
        self.captured_encodings = []
        self.current_frame = None
        self.camera_active = True

        # Reset fields
        self.entry_name.delete(0, tk.END)
        self.entry_code.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.dept_var.set("General")

        # Reset UI
        self.btn_capture.config(state=tk.NORMAL, text=f"Capture Photo (0/{REQUIRED_PHOTOS})",
                                bg=PRIMARY_COLOR)
        self.btn_save.config(state=tk.DISABLED)
        for ind in self.photo_indicators:
            ind.config(bg=ACCENT_COLOR, fg=SUBTEXT_COLOR)
        self.lbl_status.config(text="Status: Ready - Position face in camera", fg=SUBTEXT_COLOR)


if __name__ == "__main__":
    try:
        import tkinter
    except ImportError:
        print("Tkinter is not installed. Please install 'python3-tk'.")
        sys.exit(1)

    root = tk.Tk()
    app = EmployeeRegistrationApp(root)
