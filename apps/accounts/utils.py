
from django.db import connection
from django.shortcuts import get_object_or_404
from apps.accounts.models import Students
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.conf import settings

from io import BytesIO
from pyppeteer import launch
    
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.shortcuts import get_object_or_404
from apps.accounts.models import AdminsUser
from apps.solidarity.models import Logs


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # first IP in the list
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

async def html_to_pdf_buffer(html):
    browser = await launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ],
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False
    )

    page = await browser.newPage()
    await page.setContent(html)
    pdf = await page.pdf({
        "format": "A4",
        "printBackground": True
    })

    await browser.close()

    buffer = BytesIO(pdf)
    buffer.seek(0)
    return buffer

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
        if isinstance(user, AdminsUser):
            return user
        
        # fallback if token payload has admin_id
        admin_id = token.payload.get('admin_id') or token.payload.get('user_id')
        if not admin_id:
            raise AuthenticationFailed("لا يحتوي  على admin_id.")
        
        return get_object_or_404(AdminsUser, pk=admin_id)

    except Exception as e:
        raise AuthenticationFailed(f"خطأ في التوكن: {str(e)}")
    




# for read logs

@staticmethod
def log_data_access(actor_id, actor_type, action, target_type, solidarity_id=None , ip_address=None):
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO logs (actor_id, actor_type, action, target_type, solidarity_id, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, [actor_id, actor_type, action, target_type, solidarity_id, ip_address])



@staticmethod
def get_all_logs(filters=None):
    queryset = Logs.objects.select_related('actor', 'solidarity').order_by('-logged_at')

    if filters:
        if filters.get('actor_id'):
            queryset = queryset.filter(actor__admin_id=filters['actor_id'])
        if filters.get('action'):
            queryset = queryset.filter(action__icontains=filters['action'])
        if filters.get('target_type'):
            queryset = queryset.filter(target_type=filters['target_type'])
            
    return queryset
    