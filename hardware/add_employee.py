import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import cv2
import face_recognition
import numpy as np
import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database_modules.employee_crud import add_new_employee
    from ai_modules.face_recognizer import get_camera
except ImportError as e:
    print(f'Error importing modules: {e}')
    sys.exit(1)

# ============ THEME SYSTEM ============
THEMES = {
    'dark': {
        'bg': '#0f172a',
        'card': '#1e293b',
        'card_hover': '#334155',
        'input_bg': '#1e293b',
        'text': '#f8fafc',
        'text_secondary': '#94a3b8',
        'text_muted': '#64748b',
        'primary': '#6366f1',
        'primary_hover': '#4f46e5',
        'success': '#10b981',
        'danger': '#f43f5e',
        'warning': '#f59e0b',
        'border': '#334155',
        'toggle_bg': '#334155',
    },
    'light': {
        'bg': '#f1f5f9',
        'card': '#ffffff',
        'card_hover': '#f8fafc',
        'input_bg': '#f8fafc',
        'text': '#0f172a',
        'text_secondary': '#475569',
        'text_muted': '#94a3b8',
        'primary': '#6366f1',
        'primary_hover': '#4f46e5',
        'success': '#10b981',
        'danger': '#ef4444',
        'warning': '#f59e0b',
        'border': '#e2e8f0',
        'toggle_bg': '#e2e8f0',
    }
}

DEPARTMENTS = ['Administration', 'Human Resources', 'Information Technology', 'Finance', 'Marketing', 'Operations', 'Engineering', 'Security', 'Maintenance', 'General']
REQUIRED_PHOTOS = 5


class ModernEmployeeRegistration:
    def __init__(self, window):
        self.window = window
        self.window.title('Add Employee - Smart Attendance')
        self.window.geometry('1100x750')
        self.window.resizable(False, False)
        
        self.current_theme = 'dark'
        self.theme = THEMES[self.current_theme]
        
        self.captured_encodings = []
        self.current_frame = None
        self.camera_active = True
        self.auto_capture_running = False
        
        print('Initializing camera...')
        self.vid = get_camera()
        if self.vid is None or not self.vid.isOpened():
            messagebox.showerror('Error', 'Unable to open camera')
            sys.exit(1)
        print('Camera ready!')
        
        self._setup_styles()
        self._build_ui()
        self._apply_theme()
        
        self.delay = 30
        self._update_camera()
        self.window.mainloop()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

    def _toggle_theme(self):
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.theme = THEMES[self.current_theme]
        self._apply_theme()
        self.theme_btn.config(text='☀️' if self.current_theme == 'dark' else '🌙')

    def _apply_theme(self):
        t = self.theme
        self.window.configure(bg=t['bg'])
        self.main_frame.configure(bg=t['bg'])
        self.content_frame.configure(bg=t['bg'])
        self.header.configure(bg=t['card'])
        self.title_frame.configure(bg=t['card'])
        self.title_label.configure(bg=t['card'], fg=t['text'])
        self.subtitle_label.configure(bg=t['card'], fg=t['text_secondary'])
        self.theme_btn.configure(bg=t['card'], fg=t['text'], activebackground=t['card_hover'])
        self.left_panel.configure(bg=t['card'])
        self.right_panel.configure(bg=t['card'])
        self.camera_frame.configure(bg=t['card'])
        self.camera_title.configure(bg=t['card'], fg=t['text'])
        
        status_text = self.face_status.cget("text").strip()
        face_bg = t['success'] if status_text == 'Face Detected' else t['danger']
        self.face_status.configure(bg=face_bg, fg='#ffffff')
        
        self.canvas.configure(bg='#000000', highlightbackground=t['border'])
        self.btn_frame.configure(bg=t['card'])
        
        btn_auto_text = self.btn_auto.cget("text")
        if "All Photos Captured" in btn_auto_text:
            self.btn_auto.configure(bg=t['success'])
        elif str(self.btn_auto.cget("state")) == str(tk.DISABLED):
            self.btn_auto.configure(bg=t['card_hover'])
        else:
            self.btn_auto.configure(bg=t['primary'])
        self.btn_auto.configure(fg='#ffffff', activebackground=t['primary_hover'])
        
        self.btn_row.configure(bg=t['card'])
        self.btn_manual.configure(bg=t['card_hover'], fg=t['text'], activebackground=t['border'])
        self.btn_upload.configure(bg=t['card_hover'], fg=t['text'], activebackground=t['border'])
        self.status_label.configure(bg=t['card'], fg=t['text_secondary'])
        self.dots_frame.configure(bg=t['card'])
        self.form_title.configure(bg=t['card'], fg=t['text'])
        self.form_subtitle.configure(bg=t['card'], fg=t['text_secondary'])
        for wrap, lbl, entry, border in self.form_fields:
            wrap.configure(bg=t['card'])
            lbl.configure(bg=t['card'], fg=t['text_secondary'])
            entry.configure(bg=t['input_bg'], fg=t['text'], insertbackground=t['primary'])
            border.configure(bg=t['border'])
        self.id_notice_frame.configure(bg=t['primary'])
        self.id_notice_label.configure(bg=t['primary'], fg='#ffffff')
        self.dept_wrap.configure(bg=t['card'])
        self.dept_label.configure(bg=t['card'], fg=t['text_secondary'])
        self.style.configure('Custom.TCombobox', fieldbackground=t['input_bg'], background=t['input_bg'], foreground=t['text'], arrowcolor=t['primary'])
        self.style.map('Custom.TCombobox', fieldbackground=[('readonly', t['input_bg'])], foreground=[('readonly', t['text'])])
        self.spacer.configure(bg=t['card'])
        self.btn_save.configure(bg=t['success'], fg='#ffffff', activebackground='#059669')
        self.btn_reset.configure(bg=t['card_hover'], fg=t['text_secondary'], activebackground=t['border'])
        self.footer.configure(bg=t['card'])
        self.footer_label.configure(bg=t['card'], fg=t['text_muted'])
        for dot in self.dots:
            dot.configure(bg=t['card'])
            dot.delete('all')
        self._reset_dots()
        for i in range(len(self.captured_encodings)):
            self._update_dot(i)

    def _build_ui(self):
        t = self.theme
        
        self.main_frame = tk.Frame(self.window, bg=t['bg'])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.header = tk.Frame(self.main_frame, bg=t['card'], height=70)
        self.header.pack(fill=tk.X, padx=15, pady=(15, 10))
        self.header.pack_propagate(False)
        
        self.title_frame = tk.Frame(self.header, bg=t['card'])
        self.title_frame.pack(side=tk.LEFT, padx=20, pady=12)
        
        self.title_label = tk.Label(self.title_frame, text='Add New Employee', font=('Segoe UI', 18, 'bold'), bg=t['card'], fg=t['text'])
        self.title_label.pack(anchor='w')
        
        self.subtitle_label = tk.Label(self.title_frame, text='Register employee with face recognition', font=('Segoe UI', 10), bg=t['card'], fg=t['text_secondary'])
        self.subtitle_label.pack(anchor='w')
        
        self.theme_btn = tk.Button(self.header, text='☀️', font=('Segoe UI', 14), bg=t['card'], fg=t['text'], bd=0, cursor='hand2', activebackground=t['card_hover'], command=self._toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=20)
        
        # Content
        self.content_frame = tk.Frame(self.main_frame, bg=t['bg'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left Panel - Camera
        self.left_panel = tk.Frame(self.content_frame, bg=t['card'], width=580)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.left_panel.pack_propagate(False)
        
        self.camera_frame = tk.Frame(self.left_panel, bg=t['card'])
        self.camera_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        self.camera_title = tk.Label(self.camera_frame, text='Live Camera', font=('Segoe UI', 12, 'bold'), bg=t['card'], fg=t['text'])
        self.camera_title.pack(side=tk.LEFT)
        
        self.face_status = tk.Label(self.camera_frame, text='  No Face  ', font=('Segoe UI', 9, 'bold'), bg=t['danger'], fg='#ffffff', padx=8, pady=2)
        self.face_status.pack(side=tk.RIGHT)
        
        self.canvas = tk.Canvas(self.left_panel, width=520, height=360, bg='#000', highlightthickness=2, highlightbackground=t['border'])
        self.canvas.pack(padx=20, pady=5)
        
        # Buttons
        self.btn_frame = tk.Frame(self.left_panel, bg=t['card'])
        self.btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.btn_auto = tk.Button(self.btn_frame, text=f'▶  Auto Capture {REQUIRED_PHOTOS} Photos', font=('Segoe UI', 11, 'bold'), bg=t['primary'], fg='#ffffff', bd=0, pady=10, cursor='hand2', activebackground=t['primary_hover'], command=self._start_auto_capture)
        self.btn_auto.pack(fill=tk.X, pady=(0, 8))
        
        self.btn_row = tk.Frame(self.btn_frame, bg=t['card'])
        self.btn_row.pack(fill=tk.X)
        
        self.btn_manual = tk.Button(self.btn_row, text='📷  Manual', font=('Segoe UI', 10), bg=t['card_hover'], fg=t['text'], bd=0, pady=8, cursor='hand2', command=self._capture)
        self.btn_manual.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        
        self.btn_upload = tk.Button(self.btn_row, text='📁  Upload', font=('Segoe UI', 10), bg=t['card_hover'], fg=t['text'], bd=0, pady=8, cursor='hand2', command=self._upload_photos)
        self.btn_upload.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))
        
        self.status_label = tk.Label(self.left_panel, text='Position your face in the camera', font=('Segoe UI', 9), bg=t['card'], fg=t['text_secondary'])
        self.status_label.pack(pady=5)
        
        # Progress Dots
        self.dots_frame = tk.Frame(self.left_panel, bg=t['card'])
        self.dots_frame.pack(pady=10)
        
        self.dots = []
        for i in range(REQUIRED_PHOTOS):
            dot = tk.Canvas(self.dots_frame, width=36, height=36, bg=t['card'], highlightthickness=0)
            dot.pack(side=tk.LEFT, padx=6)
            self.dots.append(dot)
        self._reset_dots()
        
        # Right Panel - Form
        self.right_panel = tk.Frame(self.content_frame, bg=t['card'], width=450)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        self.right_panel.pack_propagate(False)
        
        self.form_title = tk.Label(self.right_panel, text='Employee Details', font=('Segoe UI', 14, 'bold'), bg=t['card'], fg=t['text'])
        self.form_title.pack(anchor='w', padx=25, pady=(20, 2))
        
        self.form_subtitle = tk.Label(self.right_panel, text='Fill in the information below', font=('Segoe UI', 9), bg=t['card'], fg=t['text_secondary'])
        self.form_subtitle.pack(anchor='w', padx=25, pady=(0, 15))
        
        # Form Fields
        self.form_fields = []
        self.entry_name = self._create_field('Full Name', 'Enter employee name')
        self.entry_email = self._create_field('Email Address', 'employee@company.com')
        
        # Auto ID Notice
        self.id_notice_frame = tk.Frame(self.right_panel, bg=t['primary'])
        self.id_notice_frame.pack(fill=tk.X, padx=25, pady=10)
        
        self.id_notice_label = tk.Label(self.id_notice_frame, text='✓  Employee ID will be auto-generated', font=('Segoe UI', 9, 'bold'), bg=t['primary'], fg='#ffffff', pady=8)
        self.id_notice_label.pack()
        
        # Department
        self.dept_wrap = tk.Frame(self.right_panel, bg=t['card'])
        self.dept_wrap.pack(fill=tk.X, padx=25, pady=8)
        
        self.dept_label = tk.Label(self.dept_wrap, text='Department', font=('Segoe UI', 10, 'bold'), bg=t['card'], fg=t['text_secondary'])
        self.dept_label.pack(anchor='w', pady=(0, 5))
        
        self.dept_var = tk.StringVar(value='General')
        self.dept_combo = ttk.Combobox(self.dept_wrap, textvariable=self.dept_var, values=DEPARTMENTS, state='readonly', font=('Segoe UI', 11), style='Custom.TCombobox')
        self.dept_combo.pack(fill=tk.X, ipady=6)
        
        # Spacer
        self.spacer = tk.Frame(self.right_panel, bg=t['card'], height=20)
        self.spacer.pack()
        
        # Buttons
        self.btn_save = tk.Button(self.right_panel, text='💾  Save Employee', font=('Segoe UI', 12, 'bold'), bg=t['success'], fg='#ffffff', bd=0, pady=12, cursor='hand2', state=tk.DISABLED, command=self._save)
        self.btn_save.pack(fill=tk.X, padx=25, pady=(0, 8))
        
        self.btn_reset = tk.Button(self.right_panel, text='↺  Reset Form', font=('Segoe UI', 10), bg=t['card_hover'], fg=t['text_secondary'], bd=0, pady=8, cursor='hand2', command=self._reset)
        self.btn_reset.pack(fill=tk.X, padx=25)
        
        # Footer
        self.footer = tk.Frame(self.main_frame, bg=t['card'], height=35)
        self.footer.pack(fill=tk.X, padx=15, pady=(10, 15))
        self.footer.pack_propagate(False)
        
        self.footer_label = tk.Label(self.footer, text='Smart Attendance System  •  Face Recognition Registration', font=('Segoe UI', 9), bg=t['card'], fg=t['text_muted'])
        self.footer_label.pack(pady=8)

    def _create_field(self, label, placeholder):
        t = self.theme
        wrap = tk.Frame(self.right_panel, bg=t['card'])
        wrap.pack(fill=tk.X, padx=25, pady=8)
        
        lbl = tk.Label(wrap, text=label, font=('Segoe UI', 10, 'bold'), bg=t['card'], fg=t['text_secondary'])
        lbl.pack(anchor='w', pady=(0, 5))
        
        entry = tk.Entry(wrap, font=('Segoe UI', 11), bg=t['input_bg'], fg=t['text'], insertbackground=t['primary'], relief=tk.FLAT, bd=0)
        entry.pack(fill=tk.X, ipady=10, padx=2)
        entry.insert(0, placeholder)
        entry.config(fg=t['text_muted'])
        entry._placeholder = placeholder
        
        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg=self.theme['text'])
        
        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=self.theme['text_muted'])
        
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        
        # Border line
        border_line = tk.Frame(wrap, bg=t['border'], height=2)
        border_line.pack(fill=tk.X)
        
        self.form_fields.append((wrap, lbl, entry, border_line))
        return entry

    def _get_value(self, entry):
        val = entry.get().strip()
        return '' if val == entry._placeholder else val

    def _reset_dots(self):
        t = self.theme
        for i, dot in enumerate(self.dots):
            dot.delete('all')
            dot.create_oval(4, 4, 32, 32, fill=t['card_hover'], outline=t['border'], width=2)
            dot.create_text(18, 18, text=str(i+1), fill=t['text_muted'], font=('Segoe UI', 10, 'bold'))

    def _update_dot(self, index):
        t = self.theme
        if index < len(self.dots):
            dot = self.dots[index]
            dot.delete('all')
            dot.create_oval(4, 4, 32, 32, fill=t['success'], outline=t['success'], width=2)
            dot.create_text(18, 18, text='✓', fill='#ffffff', font=('Segoe UI', 12, 'bold'))

    def _update_camera(self):
        if self.camera_active:
            ret, frame = self.vid.read()
            if ret:
                self.current_frame = frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                display = cv2.resize(frame_rgb, (520, 360))
                small = cv2.resize(frame_rgb, (0, 0), fx=0.25, fy=0.25)
                locs = face_recognition.face_locations(small)
                
                if locs:
                    self.face_status.config(text='  Face Detected  ', bg=self.theme['success'])
                    for (top, right, bottom, left) in locs:
                        t, r, b, l = top*4, right*4, bottom*4, left*4
                        h, w = frame_rgb.shape[:2]
                        sx, sy = 520/w, 360/h
                        x1, y1 = int(l*sx), int(t*sy)
                        x2, y2 = int(r*sx), int(b*sy)
                        cv2.rectangle(display, (x1, y1), (x2, y2), (99, 102, 241), 2)
                        cv2.rectangle(display, (x1, y1-25), (x2, y1), (99, 102, 241), -1)
                        cv2.putText(display, 'FACE', (x1+5, y1-7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
                else:
                    self.face_status.config(text='  No Face  ', bg=self.theme['danger'])
                
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(display))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        
        self.window.after(self.delay, self._update_camera)

    def _upload_photos(self):
        if len(self.captured_encodings) >= REQUIRED_PHOTOS:
            return
        filepaths = filedialog.askopenfilenames(title='Select Face Photos', filetypes=[('Images', '*.jpg *.jpeg *.png *.bmp')])
        if not filepaths:
            return
        self.status_label.config(text='Processing...', fg=self.theme['warning'])
        self.window.update_idletasks()
        for fp in filepaths:
            if len(self.captured_encodings) >= REQUIRED_PHOTOS:
                break
            try:
                img = face_recognition.load_image_file(fp)
                boxes = face_recognition.face_locations(img)
                if len(boxes) == 1:
                    encs = face_recognition.face_encodings(img, boxes)
                    if encs:
                        self.captured_encodings.append(encs[0])
                        self._update_dot(len(self.captured_encodings)-1)
            except Exception:
                pass
        if len(self.captured_encodings) >= REQUIRED_PHOTOS:
            self._on_complete()
        else:
            self.status_label.config(text=f'{len(self.captured_encodings)}/{REQUIRED_PHOTOS} photos. Need more.', fg=self.theme['text_secondary'])

    def _start_auto_capture(self):
        if self.auto_capture_running or len(self.captured_encodings) >= REQUIRED_PHOTOS:
            return
        self.auto_capture_running = True
        self.btn_auto.config(state=tk.DISABLED, bg=self.theme['card_hover'])
        self.btn_manual.config(state=tk.DISABLED)
        self.btn_upload.config(state=tk.DISABLED)
        self._countdown(3)

    def _countdown(self, n):
        if n > 0:
            self.status_label.config(text=f'Starting in {n}...', fg=self.theme['warning'])
            self.window.after(1000, lambda: self._countdown(n-1))
        else:
            self._auto_sequence()

    def _auto_sequence(self):
        if len(self.captured_encodings) >= REQUIRED_PHOTOS:
            self._on_complete()
            return
        if self.current_frame is None:
            self.window.after(500, self._auto_sequence)
            return
        rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb)
        if len(boxes) != 1:
            self.status_label.config(text='Position face...', fg=self.theme['warning'])
            self.window.after(500, self._auto_sequence)
            return
        try:
            encs = face_recognition.face_encodings(rgb, boxes)
            if encs:
                self.captured_encodings.append(encs[0])
                c = len(self.captured_encodings)
                self._update_dot(c-1)
                self.status_label.config(text=f'Photo {c}/{REQUIRED_PHOTOS} - Move slightly', fg=self.theme['success'])
                if c >= REQUIRED_PHOTOS:
                    self._on_complete()
                else:
                    self.window.after(1200, self._auto_sequence)
            else:
                self.window.after(500, self._auto_sequence)
        except Exception:
            self.window.after(500, self._auto_sequence)

    def _on_complete(self):
        self.auto_capture_running = False
        self.btn_auto.config(text='✓  All Photos Captured!', bg=self.theme['success'])
        self.btn_manual.config(state=tk.DISABLED)
        self.btn_upload.config(state=tk.DISABLED)
        self.btn_save.config(state=tk.NORMAL, bg=self.theme['success'])
        self.camera_active = False
        self.status_label.config(text='Ready! Fill details and save.', fg=self.theme['success'])

    def _capture(self):
        if self.current_frame is None or len(self.captured_encodings) >= REQUIRED_PHOTOS:
            return
        rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb)
        if len(boxes) != 1:
            self.status_label.config(text='No face detected', fg=self.theme['danger'])
            return
        try:
            encs = face_recognition.face_encodings(rgb, boxes)
            if encs:
                self.captured_encodings.append(encs[0])
                c = len(self.captured_encodings)
                self._update_dot(c-1)
                if c >= REQUIRED_PHOTOS:
                    self._on_complete()
                else:
                    self.status_label.config(text=f'Photo {c}/{REQUIRED_PHOTOS}', fg=self.theme['success'])
        except Exception as e:
            self.status_label.config(text=str(e), fg=self.theme['danger'])

    def _save(self):
        name = self._get_value(self.entry_name)
        email = self._get_value(self.entry_email)
        dept = self.dept_var.get()
        code = f'EMP{uuid.uuid4().hex[:8].upper()}'
        
        if not name or not email:
            messagebox.showwarning('Missing', 'Please fill Name and Email')
            return
        if len(self.captured_encodings) < REQUIRED_PHOTOS:
            messagebox.showwarning('Photos', f'Need {REQUIRED_PHOTOS} photos')
            return
        
        self.status_label.config(text='Saving...', fg=self.theme['warning'])
        self.window.update_idletasks()
        
        avg = np.mean(self.captured_encodings, axis=0)
        try:
            if add_new_employee(name, code, email, avg, dept):
                messagebox.showinfo('Success', f'Employee registered!\n\nID: {code}\nName: {name}\nDept: {dept}')
                self._reset()
            else:
                messagebox.showerror('Error', 'Failed. Duplicate face?')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _reset(self):
        self.captured_encodings = []
        self.current_frame = None
        self.camera_active = True
        self.auto_capture_running = False
        
        for _, _, entry, _ in self.form_fields:
            entry.delete(0, tk.END)
            entry.insert(0, entry._placeholder)
            entry.config(fg=self.theme['text_muted'])
        self.dept_var.set('General')
        
        self.btn_auto.config(state=tk.NORMAL, text=f'▶  Auto Capture {REQUIRED_PHOTOS} Photos', bg=self.theme['primary'])
        self.btn_manual.config(state=tk.NORMAL)
        self.btn_upload.config(state=tk.NORMAL)
        self.btn_save.config(state=tk.DISABLED)
        
        self._reset_dots()
        self.status_label.config(text='Position your face in the camera', fg=self.theme['text_secondary'])


if __name__ == '__main__':
    root = tk.Tk()
    app = ModernEmployeeRegistration(root)
