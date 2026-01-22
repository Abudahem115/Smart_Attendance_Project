#!/bin/bash

# Smart Attendance System - Raspberry Pi Deployment Script
# This script installs necessary system libraries and Python dependencies for Face Recognition.

echo "🚀 Starting Deployment for Smart Attendance System on Raspberry Pi..."

# 1. Update System
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install System Dependencies for OpenCV & Dlib
echo "🛠️ Installing system dependencies for OpenCV and Dlib..."
# Basic build tools
sudo apt-get install -y build-essential cmake pkg-config gfortran

# Image & Video I/O
sudo apt-get install -y libjpeg-dev libtiff5-dev libpng-dev
sudo apt-get install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get install -y libxvidcore-dev libx264-dev

# GUI backend (for cv2.imshow)
sudo apt-get install -y libgtk-3-dev libcanberra-gtk*

# Mathematical optimizations
sudo apt-get install -y libatlas-base-dev libopenblas-dev liblapack-dev

# Python headers
sudo apt-get install -y python3-dev

# 3. Create Virtual Environment
echo "🐍 Setting up Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created."
else
    echo "ℹ️  Virtual environment already exists."
fi

# Activate venv
source venv/bin/activate

# 4. Install Python Dependencies
echo "📥 Installing Python libraries..."
pip install --upgrade pip

# Install numpy first
pip install numpy

# Install OpenCV (headless often better for servers, but user wants imshow so we need GUI support)
# Try system opencv if pip builds fail, but let's try pip first.
echo "   - Installing opencv-python..."
pip install opencv-python

# Install Face Recognition (this will build dlib, might take 20-40 mins on Pi 4)
echo "   - Installing face_recognition (This may take a while to compile dlib)..."
pip install face-recognition

# Install other requirements
if [ -f "requirements_pi.txt" ]; then
    pip install -r requirements_pi.txt
else
    echo "⚠️ requirements_pi.txt not found, installing defaults..."
    pip install click colorama
fi

echo "✅ Dependencies installed!"
echo ""
echo "🎉 Setup Complete!"
echo "To run the system:"
echo "  source venv/bin/activate"
echo "  python start_system.py"
