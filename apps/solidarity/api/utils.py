from django.shortcuts import get_object_or_404
from apps.solidarity.models import Students, Admins

def get_current_student(request):
    student_id = request.headers.get('X-Student-Id')
    if not student_id:
        raise ValueError("X-Student-Id header is required for student endpoints")
    return get_object_or_404(Students, pk=student_id)

def get_current_admin(request):
    admin_id = request.headers.get('X-Admin-Id')
    if not admin_id:
        admin_id=7                                            #just for testing
        #raise ValueError("X-Admin-Id header is required for admin endpoints") 
    return get_object_or_404(Admins, pk=admin_id)