
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import face_recognition
import numpy as np
import sys
import os

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database_modules.employee_crud import add_new_employee
    from ai_modules.face_recognizer import get_camera
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# ============ DESIGN SYSTEM ============
# Modern Teal & Slate Theme
BG = "#0f172a"           # Deep navy background
CARD = "#1e293b"         # Slate card
CARD_LIGHT = "#334155"   # Lighter slate
TEAL = "#14b8a6"         # Primary teal
TEAL_DARK = "#0d9488"    # Darker teal
CORAL = "#f43f5e"        # Accent coral/pink
AMBER = "#f59e0b"        # Warning amber
WHITE = "#f8fafc"        # Clean white
GRAY = "#94a3b8"         # Muted gray
DARK_GRAY = "#475569"    # Dark gray

DEPARTMENTS = [
    "Administration",
    "Human Resources",
    "Information Technology",
    "Finance",
    "Marketing",
    "Operations",
    "Engineering",
    "Security",
    "Maintenance",
    "General",
]

REQUIRED_PHOTOS = 5


class EmployeeRegistrationApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Smart Attendance - Registration")
        self.window.geometry("960x680")
        self.window.configure(bg=BG)
        self.window.resizable(False, False)

        # State
        self.captured_encodings = []
        self.current_frame = None
        self.camera_active = True

        # Camera
        print("Initializing camera...")
        self.vid = get_camera()
        if self.vid is None or not self.vid.isOpened():
            messagebox.showerror("Error", "Unable to open camera source")
            sys.exit(1)
        print("Camera ready!")

        # ttk style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dept.TCombobox",
                        fieldbackground=CARD_LIGHT, background=CARD_LIGHT,
                        foreground=WHITE, selectbackground=TEAL,
                        arrowcolor=TEAL)
        style.map("Dept.TCombobox",
                  fieldbackground=[("readonly", CARD_LIGHT)],
                  foreground=[("readonly", WHITE)])

        self._build_ui()

        # Camera loop
        self.delay = 30
        self._update_camera()
        self.window.mainloop()

    # ==================== BUILD UI ====================
    def _build_ui(self):
        # --- HEADER ---
        hdr = tk.Frame(self.window, bg=TEAL, height=56)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="  Employee Registration",
                 font=("Helvetica", 17, "bold"), bg=TEAL, fg=WHITE
                 ).pack(side=tk.LEFT, padx=10)

        badge = tk.Label(hdr, text=f"  {REQUIRED_PHOTOS} Photos Required  ",
                         font=("Helvetica", 10, "bold"),
                         bg=TEAL_DARK, fg=WHITE)
        badge.pack(side=tk.RIGHT, padx=15, pady=14)

        # --- BODY ---
        body = tk.Frame(self.window, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # ===== LEFT COLUMN (Camera) =====
        left = tk.Frame(body, bg=CARD, bd=0)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        # Camera label
        cam_hdr = tk.Frame(left, bg=CARD)
        cam_hdr.pack(fill=tk.X, padx=15, pady=(12, 4))
        tk.Label(cam_hdr, text="Live Camera", font=("Helvetica", 11, "bold"),
                 bg=CARD, fg=WHITE).pack(side=tk.LEFT)
        self.lbl_face_detect = tk.Label(cam_hdr, text="  No Face  ",
                                         font=("Helvetica", 9, "bold"),
                                         bg=CORAL, fg=WHITE)
        self.lbl_face_detect.pack(side=tk.RIGHT)

        # Canvas
        self.canvas = tk.Canvas(left, width=440, height=340, bg="#000",
                                highlightthickness=2, highlightbackground=CARD_LIGHT)
        self.canvas.pack(padx=15, pady=4)

        # Capture button
        self.btn_capture = tk.Button(
            left, text=f"  Capture Photo  ( 0 / {REQUIRED_PHOTOS} )",
            font=("Helvetica", 13, "bold"), bg=TEAL, fg=WHITE,
            activebackground=TEAL_DARK, activeforeground=WHITE,
            relief=tk.FLAT, cursor="hand2", bd=0, pady=8,
            command=self._capture)
        self.btn_capture.pack(fill=tk.X, padx=15, pady=(6, 4))

        # Status bar
        self.lbl_status = tk.Label(left, text="Position your face in the camera and press Capture",
                                   font=("Helvetica", 9), bg=CARD, fg=GRAY, wraplength=400)
        self.lbl_status.pack(pady=(0, 4))

        # Photo progress dots
        dots_frame = tk.Frame(left, bg=CARD)
        dots_frame.pack(pady=(0, 14))
        self.dots = []
        for i in range(REQUIRED_PHOTOS):
            dot = tk.Canvas(dots_frame, width=28, height=28,
                            bg=CARD, highlightthickness=0)
            dot.pack(side=tk.LEFT, padx=4)
            # Draw circle
            dot.create_oval(2, 2, 26, 26, fill=CARD_LIGHT, outline=DARK_GRAY, width=2, tags="circle")
            dot.create_text(15, 15, text=str(i + 1), fill=DARK_GRAY,
                            font=("Helvetica", 10, "bold"), tags="num")
            self.dots.append(dot)

        # ===== RIGHT COLUMN (Form) =====
        right = tk.Frame(body, bg=CARD, width=330, bd=0)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(6, 0))
        right.pack_propagate(False)

        tk.Label(right, text="Employee Details",
                 font=("Helvetica", 13, "bold"), bg=CARD, fg=WHITE
                 ).pack(pady=(20, 5))

        # Divider
        tk.Frame(right, bg=TEAL, height=2).pack(fill=tk.X, padx=25, pady=(0, 15))

        # Fields
        self.entry_name = self._field(right, "Full Name", "Enter full name")
        self.entry_code = self._field(right, "Employee Code", "e.g. EMP001")
        self.entry_email = self._field(right, "Email", "employee@company.com")

        # Department dropdown
        dept_wrap = tk.Frame(right, bg=CARD)
        dept_wrap.pack(padx=25, pady=6, fill=tk.X)
        tk.Label(dept_wrap, text="DEPARTMENT", font=("Helvetica", 9, "bold"),
                 bg=CARD, fg=GRAY).pack(anchor="w")
        self.dept_var = tk.StringVar(value="General")
        self.dept_combo = ttk.Combobox(dept_wrap, textvariable=self.dept_var,
                                        values=DEPARTMENTS, state="readonly",
                                        font=("Helvetica", 11), style="Dept.TCombobox")
        self.dept_combo.pack(fill=tk.X, pady=(4, 0), ipady=5)

        # Spacer
        tk.Frame(right, bg=CARD, height=20).pack()

        # Save button
        self.btn_save = tk.Button(
            right, text="  Save Employee",
            font=("Helvetica", 13, "bold"), bg=TEAL, fg=WHITE,
            activebackground=TEAL_DARK, activeforeground=WHITE,
            relief=tk.FLAT, cursor="hand2", bd=0, pady=8,
            command=self._save, state=tk.DISABLED,
            disabledforeground=DARK_GRAY)
        self.btn_save.pack(fill=tk.X, padx=25, pady=(0, 6))

        # Reset button
        self.btn_reset = tk.Button(
            right, text="  Reset",
            font=("Helvetica", 11), bg=CARD_LIGHT, fg=GRAY,
            activebackground=DARK_GRAY, activeforeground=WHITE,
            relief=tk.FLAT, cursor="hand2", bd=0, pady=5,
            command=self._reset)
        self.btn_reset.pack(fill=tk.X, padx=25, pady=(0, 8))

        # Tip
        tip_frame = tk.Frame(right, bg="#1a2e3d")
        tip_frame.pack(fill=tk.X, padx=25, pady=(10, 15))
        tk.Label(tip_frame, text="Tip: Change your face angle\nbetween each capture for\nbetter recognition accuracy.",
                 font=("Helvetica", 9), bg="#1a2e3d", fg=TEAL,
                 justify=tk.CENTER, pady=8).pack()

        # --- FOOTER ---
        ftr = tk.Frame(self.window, bg=CARD_LIGHT, height=28)
        ftr.pack(fill=tk.X, side=tk.BOTTOM)
        ftr.pack_propagate(False)
        tk.Label(ftr, text="Smart Attendance System  •  Face Recognition Registration",
                 font=("Helvetica", 8), bg=CARD_LIGHT, fg=DARK_GRAY).pack(pady=5)

    # ==================== HELPERS ====================
    def _field(self, parent, label, placeholder=""):
        wrap = tk.Frame(parent, bg=CARD)
        wrap.pack(padx=25, pady=6, fill=tk.X)
        tk.Label(wrap, text=label.upper(), font=("Helvetica", 9, "bold"),
                 bg=CARD, fg=GRAY).pack(anchor="w")
        entry = tk.Entry(wrap, font=("Helvetica", 11), bg=CARD_LIGHT, fg=WHITE,
                         insertbackground=TEAL, relief=tk.FLAT, bd=0)
        entry.pack(fill=tk.X, pady=(4, 0), ipady=7)

        # Placeholder behavior
        entry.insert(0, placeholder)
        entry.config(fg=DARK_GRAY)

        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg=WHITE)

        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=DARK_GRAY)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry._placeholder = placeholder
        return entry

    def _get_entry_value(self, entry):
        """Get entry value, ignoring placeholder text."""
        val = entry.get().strip()
        if val == entry._placeholder:
            return ""
        return val

    def _update_camera(self):
        if self.camera_active:
            ret, frame = self.vid.read()
            if ret:
                self.current_frame = frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                display = cv2.resize(frame_rgb, (440, 340))

                # Face detection on small frame for speed
                small = cv2.resize(frame_rgb, (0, 0), fx=0.25, fy=0.25)
                locs = face_recognition.face_locations(small)

                if locs:
                    self.lbl_face_detect.config(text="  Face Detected  ", bg=TEAL)
                    for (top, right, bottom, left) in locs:
                        t, r, b, l = top * 4, right * 4, bottom * 4, left * 4
                        h, w = frame_rgb.shape[:2]
                        sx, sy = 440 / w, 340 / h
                        x1, y1 = int(l * sx), int(t * sy)
                        x2, y2 = int(r * sx), int(b * sy)
                        # Draw teal rectangle
                        cv2.rectangle(display, (x1, y1), (x2, y2), (20, 184, 166), 2)
                        # Corner accents
                        corner = 12
                        for cx, cy, dx, dy in [(x1, y1, 1, 1), (x2, y1, -1, 1),
                                                (x1, y2, 1, -1), (x2, y2, -1, -1)]:
                            cv2.line(display, (cx, cy), (cx + corner * dx, cy), (20, 184, 166), 3)
                            cv2.line(display, (cx, cy), (cx, cy + corner * dy), (20, 184, 166), 3)
                else:
                    self.lbl_face_detect.config(text="  No Face  ", bg=CORAL)

                self.photo = ImageTk.PhotoImage(image=Image.fromarray(display))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self._update_camera)

    def _capture(self):
        if self.current_frame is None:
            self.lbl_status.config(text="No camera frame available.", fg=AMBER)
            return

        if len(self.captured_encodings) >= REQUIRED_PHOTOS:
            return

        self.lbl_status.config(text="Processing capture...", fg=AMBER)
        self.window.update_idletasks()

        rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb)

        if len(boxes) == 0:
            self.lbl_status.config(text="No face detected. Please try again.", fg=CORAL)
            return
        if len(boxes) > 1:
            self.lbl_status.config(text="Multiple faces detected! Only one person allowed.", fg=CORAL)
            return

        try:
            encs = face_recognition.face_encodings(rgb, boxes)
            if encs:
                self.captured_encodings.append(encs[0])
                count = len(self.captured_encodings)

                # Update dot indicator
                dot = self.dots[count - 1]
                dot.delete("circle")
                dot.delete("num")
                dot.create_oval(2, 2, 26, 26, fill=TEAL, outline=TEAL, width=2, tags="circle")
                dot.create_text(15, 15, text="✓", fill=WHITE,
                                font=("Helvetica", 12, "bold"), tags="num")

                self.btn_capture.config(
                    text=f"  Capture Photo  ( {count} / {REQUIRED_PHOTOS} )")

                if count >= REQUIRED_PHOTOS:
                    self.btn_capture.config(state=tk.DISABLED, bg=CARD_LIGHT)
                    self.btn_save.config(state=tk.NORMAL, bg=TEAL)
                    self.camera_active = False
                    self.lbl_status.config(
                        text=f"All {REQUIRED_PHOTOS} photos captured! Fill in details and Save.",
                        fg=TEAL)
                else:
                    left = REQUIRED_PHOTOS - count
                    self.lbl_status.config(
                        text=f"Photo {count} captured!  {left} remaining. Please change angle.",
                        fg=TEAL)
            else:
                self.lbl_status.config(text="Could not encode face. Try again.", fg=CORAL)
        except Exception as e:
            print(f"Error: {e}")
            self.lbl_status.config(text=f"Error: {e}", fg=CORAL)

    def _save(self):
        name = self._get_entry_value(self.entry_name)
        code = self._get_entry_value(self.entry_code)
        email = self._get_entry_value(self.entry_email)
        dept = self.dept_var.get()

        if not name or not code or not email:
            messagebox.showwarning("Missing Info", "Please fill in Name, Code, and Email.")
            return

        if len(self.captured_encodings) < REQUIRED_PHOTOS:
            messagebox.showwarning("Photos Required",
                                   f"Please capture all {REQUIRED_PHOTOS} photos first.")
            return

        self.lbl_status.config(text="Computing average face encoding...", fg=AMBER)
        self.window.update_idletasks()

        # Average all encodings for maximum accuracy
        avg_encoding = np.mean(self.captured_encodings, axis=0)

        self.lbl_status.config(text="Saving to database...", fg=AMBER)
        self.window.update_idletasks()

        try:
            success = add_new_employee(name, code, email, avg_encoding, dept)
            if success:
                messagebox.showinfo("Success",
                                    f"Employee '{name}' registered successfully!\n"
                                    f"Department: {dept}\n"
                                    f"Photos used: {REQUIRED_PHOTOS}")
                self._reset()
            else:
                self.lbl_status.config(text="Failed to save. Check console for details.", fg=CORAL)
                messagebox.showerror("Error",
                                     "Failed to add employee.\nPossible duplicate face or employee code.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.lbl_status.config(text=f"Error: {e}", fg=CORAL)

    def _reset(self):
        self.captured_encodings = []
        self.current_frame = None
        self.camera_active = True

        # Reset fields
        for entry in [self.entry_name, self.entry_code, self.entry_email]:
            entry.delete(0, tk.END)
            entry.insert(0, entry._placeholder)
            entry.config(fg=DARK_GRAY)
        self.dept_var.set("General")

        # Reset buttons
        self.btn_capture.config(state=tk.NORMAL,
                                text=f"  Capture Photo  ( 0 / {REQUIRED_PHOTOS} )",
                                bg=TEAL)
        self.btn_save.config(state=tk.DISABLED)

        # Reset dots
        for i, dot in enumerate(self.dots):
            dot.delete("circle")
            dot.delete("num")
            dot.create_oval(2, 2, 26, 26, fill=CARD_LIGHT, outline=DARK_GRAY, width=2, tags="circle")
            dot.create_text(15, 15, text=str(i + 1), fill=DARK_GRAY,
                            font=("Helvetica", 10, "bold"), tags="num")

        self.lbl_status.config(text="Position your face in the camera and press Capture", fg=GRAY)


if __name__ == "__main__":
    try:
        import tkinter
    except ImportError:
        print("Tkinter is not installed. Install with: sudo apt install python3-tk")
        sys.exit(1)

    root = tk.Tk()
    app = EmployeeRegistrationApp(root)
