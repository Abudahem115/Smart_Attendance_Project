# اسم الملف: ai_modules/face_encoder.py
import face_recognition
import os
import sys

# إضافة المسار الرئيسي للمشروع لكي نستطيع استدعاء ملفات قاعدة البيانات
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_modules.student_crud import add_new_student

def register_new_student(image_path, name, student_code, email):
    """
    دالة شاملة تقوم بالتالي:
    1. تحميل الصورة
    2. استخراج بصمة الوجه
    3. حفظ البيانات في قاعدة البيانات
    """
    
    # التأكد من أن ملف الصورة موجود
    if not os.path.exists(image_path):
        print(f"❌ Error: The image file is not found in the path: {image_path}")
        return False

    print(f"🔄 Student image being processed: {name} ...")
    
    try:
        # 1. تحميل الصورة باستخدام مكتبة face_recognition
        image = face_recognition.load_image_file(image_path)
        
        # 2. البحث عن الوجوه في الصورة
        # هذه الخطوة ترجع قائمة بكل الوجوه الموجودة (نحن نتوقع وجهاً واحداً)
        face_encodings = face_recognition.face_encodings(image)
        
        # التحقق هل تم العثور على وجه أم لا
        if len(face_encodings) == 0:
            print("⚠️ Warning: No face was found in the picture! Please use a clear picture.")
            return False
        
        if len(face_encodings) > 1:
            print("⚠️ Warning: There is more than one face in the picture! Please use only a personal photo of the student.")
            return False

        # نأخذ أول وجه تم العثور عليه (لأننا نتوقع وجهاً واحداً)
        student_face_encoding = face_encodings[0]
        
        # 3. إرسال البيانات للحفظ في قاعدة البيانات
        # نستدعي الدالة التي كتبناها سابقاً في student_crud
        result = add_new_student(name, student_code, email, student_face_encoding)
        
        return result

    except Exception as e:
        print(f"❌ An error occurred while processing the image: {e}")
        return False