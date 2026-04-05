# File: web_interface/services/face_service.py
"""
Face-encoding service layer.

Centralises all face-recognition logic used by the web interface so that
route handlers stay thin and focused on request/response.
"""
import base64
import logging
import os
from typing import List, Optional

import cv2
import face_recognition
import numpy as np

logger = logging.getLogger(__name__)


def process_uploaded_photos(
    files, upload_folder: str
) -> List[np.ndarray]:
    """
    Process uploaded photo files and return face encodings.

    Each file is saved temporarily, encoded, then removed.
    """
    encodings: List[np.ndarray] = []

    for file in files:
        if file and file.filename != "":
            filepath = os.path.join(upload_folder, file.filename)
            file.save(filepath)
            try:
                img = face_recognition.load_image_file(filepath)
                encs = face_recognition.face_encodings(img)
                if len(encs) > 0:
                    encodings.append(encs[0])
            except Exception as e:
                logger.warning("Error processing uploaded image '%s': %s", file.filename, e)
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)

    return encodings


def process_captured_photos(
    captured_list: List[str],
    upload_folder: str,
    employee_code: str,
) -> List[np.ndarray]:
    """
    Process base64-encoded captured photos and return face encodings.
    """
    encodings: List[np.ndarray] = []

    for i, item in enumerate(captured_list):
        try:
            if "," in item:
                _, encoded = item.split(",", 1)
                data = base64.b64decode(encoded)
                temp_path = os.path.join(
                    upload_folder, f"capture_{employee_code}_{i}.jpg"
                )
                with open(temp_path, "wb") as f:
                    f.write(data)

                img = face_recognition.load_image_file(temp_path)
                encs = face_recognition.face_encodings(img)
                if len(encs) > 0:
                    encodings.append(encs[0])

                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            logger.warning("Error processing captured image %d: %s", i, e)

    return encodings


def compute_average_encoding(
    encodings: List[np.ndarray],
) -> Optional[np.ndarray]:
    """
    Compute the element-wise average of multiple face encodings.

    Returns ``None`` if the list is empty.
    """
    if not encodings:
        return None
    return np.mean(encodings, axis=0)
