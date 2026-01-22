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

# Python headers and venv
sudo apt-get install -y python3-dev python3-venv

# 3. Create Virtual Environment
echo "🐍 Setting up Python Virtual Environment..."
# Ensure permissions are correct for current directory
sudo chown -R $USER:$USER .

if [ ! -d "venv" ]; then
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created."
    else
        echo "❌ Failed to create virtual environment. Trying to install python3-venv again..."
        sudo apt-get install -y python3-venv
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo "❌ Critical Error: Could not create venv. Exiting."
            exit 1
        fi
    fi
else
    echo "ℹ️  Virtual environment already exists."
fi

    echo "✅ Swap increased to 2048MB. Attempting installation now..."
else
    echo "✅ Swap space is sufficient ($SWAP_SIZE MB)."
fi

# Force single-core compilation for dlib to save RAM
export MAKEFLAGS="-j1"
echo "🐌 Set MAKEFLAGS='-j1' to reduce memory usage during compilation (this will be slower but safer)."

# 4. Install Python Dependencies
echo "📥 Installing Python libraries..."
pip install --upgrade pip

# Install numpy first (sometimes helps avoid build issues)
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
    pip install click colorama supabase python-dotenv waitress
fi

echo "✅ Dependencies installed!"
echo ""
echo "🎉 Setup Complete!"
echo "To run the system:"
echo "  source venv/bin/activate"
echo "  python start_system.py"
