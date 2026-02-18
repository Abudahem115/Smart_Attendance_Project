# Smart Attendance System - Deployment Guide

This guide covers how to deploy the **Web Interface** to a VPS (using Docker) and how to set up the **Hardware Component** on a Raspberry Pi.

---

## Part 1: Deploying Web Interface to VPS (Docker)

The web interface is containerized for easy deployment on any VPS (DigitalOcean, AWS, Linode, etc.).

### Prerequisites
- A VPS with **Docker** and **Docker Compose** installed.
- Access to your GitHub repository.

### Steps

1.  **Clone the Repository** on your VPS:
    ```bash
    git clone https://github.com/Abudahem115/Smart_Attendance_Project.git
    cd Smart_Attendance_Project
    ```

2.  **Create `.env` File**:
    Create a `.env` file in the project root with your secrets:
    ```bash
    nano .env
    ```
    Paste the following (fill in your actual values):
    ```ini
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_key
    SENDER_EMAIL=your_email@gmail.com
    SENDER_PASSWORD=your_app_password
    SECRET_KEY=your_random_secret_string
    ```

3.  **Build and Run with Docker**:
    ```bash
    # Build the image
    docker build -t smart_attendance_web .

    # Run the container (background mode, mapping port 80 to 8090)
    docker run -d --name smart_attendance -p 80:8090 --env-file .env --restart always smart_attendance_web
    ```

4.  **Verify**:
    Open your VPS IP address in a browser (e.g., `http://your-vps-ip`). You should see the login page.
    (Note: The container exposes port 8090 internally, but we mapped it to port 80 on the host).

---

## Part 2: Hardware Setup (Raspberry Pi)

The hardware component (camera & face recognition) runs directly on the Raspberry Pi.

### Prerequisites
- Raspberry Pi 4 (Recommended) with 64-bit OS (Bookworm or Bullseye).
- Camera Module connected.
- Internet connection.

### Steps

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/Abudahem115/Smart_Attendance_Project.git
    cd Smart_Attendance_Project
    ```

2.  **Run Setup Script**:
    We have a dedicated script to install dependencies (OpenCV, dlib, etc.):
    ```bash
    cd hardware
    chmod +x deploy_face_scan.sh
    ./deploy_face_scan.sh
    ```
    *Note: This may take 15-30 minutes as it compiles libraries.*

3.  **Configure `.env`**:
    Copy your `.env` file from your PC to the `hardware/` directory (or project root, the script checks both).

4.  **Test the Camera**:
    ```bash
    source venv/bin/activate
    python start_system.py
    ```
    - Press `q` to exit.

5.  **Auto-Start on Boot (Optional)**:
    Add the script to your `.bashrc` or create a systemd service to run it automatically on startup.

---

## Troubleshooting

-   **"Camera not found"**: Ensure `legacy camera` is enabled via `sudo raspi-config` if using older OS, or verify standard camera functioning with `libcamera-hello`.
-   **"Unknown User"**: Check lighting conditions and ensure the user is registered in the database with a clear face encoding.
