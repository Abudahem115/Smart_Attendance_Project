
import cv2

def test_cameras():
    print("📸 Testing Camera Indices on Raspberry Pi...")
    
    # Test indices 0 to 9
    available_cameras = []
    
    for index in range(10):
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            print(f"✅ Camera found at Index {index}")
            available_cameras.append(index)
            cap.release()
        else:
            print(f"❌ No camera at Index {index}")
            cap.release()
            
    print("\nSUMMARY:")
    if available_cameras:
        print(f"Working cameras ID: {available_cameras}")
        print(f"👉 Try changing 'cv2.VideoCapture(0)' to 'cv2.VideoCapture({available_cameras[0]})' in ai_modules/face_recognizer.py")
    else:
        print("⚠️ No cameras detected!")
        print("Check:")
        print("1. Is the camera connected?")
        print("2. Is Legacy Camera enabled in raspi-config?")
        print("3. Try 'libcamera-hello' in terminal.")

if __name__ == "__main__":
    test_cameras()
