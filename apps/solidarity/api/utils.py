from django.shortcuts import get_object_or_404
from apps.solidarity.models import Students, Admins
import os
import uuid
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.conf import settings
    
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.shortcuts import get_object_or_404
# from apps.accounts.models import Admins


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
    """
    Safely get the current authenticated student using the JWT token.
    """
    auth = JWTAuthentication()
    header = request.headers.get('Authorization')

    if not header or not header.startswith('Bearer '):
        raise AuthenticationFailed("Missing or invalid Authorization header")

    raw_token = header.split(' ')[1]
    try:
        validated_token = auth.get_validated_token(raw_token)
        payload = validated_token.payload

        student_id = payload.get('student_id')
        if not student_id:
            raise AuthenticationFailed("Token missing student_id claim")

        return get_object_or_404(Students, pk=student_id)

    except Exception as e:
        raise AuthenticationFailed(str(e))
    



def get_current_admin(request):
    """
    Get the current authenticated admin based on the JWT token.
    If the token is valid, extract the admin_id from its payload.
    """
    jwt_auth = JWTAuthentication()
    try:
        # validate the token and get (user, token) tuple
        user, token = jwt_auth.authenticate(request)
        if not user:
            raise AuthenticationFailed("لم يتم العثور على مستخدم مرتبط .")
        
        # the user should already be an instance of Admins
        if isinstance(user, Admins):
            return user
        
        # fallback if token payload has admin_id
        admin_id = token.payload.get('admin_id') or token.payload.get('user_id')
        if not admin_id:
            raise AuthenticationFailed("لا يحتوي  على admin_id.")
        
        return get_object_or_404(Admins, pk=admin_id)

    except Exception as e:
        raise AuthenticationFailed(f"خطأ في التوكن: {str(e)}")


def get_admin_faculty_id(admin):
    if hasattr(admin, 'faculty') and admin.faculty:
        return admin.faculty.faculty_id
    return None
