from django.shortcuts import get_object_or_404
from apps.solidarity.models import Students, Admins
import os
import uuid
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.conf import settings

fs = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)

ALLOWED_MIME = {
    'application/pdf',
    'image/jpeg',
    'image/png',
    # add the types you accept
}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

def save_uploaded_file(uploaded_file, upload_subdir):
    # Basic checks
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise ValueError("File size exceeds the allowed limit.")

    if uploaded_file.content_type not in ALLOWED_MIME:
        raise ValueError("File type is not allowed.")

    # Ensure subdir exists (FileSystemStorage will handle location)
    ext = os.path.splitext(uploaded_file.name)[1]
    safe_name = f"{uuid.uuid4().hex}{ext}"
    relative_path = os.path.join(upload_subdir, safe_name).replace("\\", "/")
    # fs.save takes a path relative to storage.location
    saved_name = fs.save(relative_path, uploaded_file)
    # saved_name is the relative path under MEDIA_ROOT
    return {
        'file_name': uploaded_file.name,       # original filename
        'file_path': saved_name,               # relative path stored
        'mime_type': uploaded_file.content_type,
        'file_size': uploaded_file.size,
        'uploaded_at': timezone.now()
    }



def get_current_student(request):
    student_id = request.headers.get('X-Student-Id')
    if not student_id:
        student_id = 2
    return get_object_or_404(Students, pk=student_id)

def get_current_admin(request):
    admin_id = request.headers.get('X-Admin-Id')
    if not admin_id:
        admin_id=7 #just for testing
        #raise ValueError("X-Admin-Id header is required for admin endpoints") 
    return get_object_or_404(Admins, pk=admin_id)

def get_admin_faculty_id(admin):
    if hasattr(admin, 'faculty') and admin.faculty:
        return admin.faculty.faculty_id
    return None
