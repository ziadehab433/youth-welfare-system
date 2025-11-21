from django.db import DatabaseError
from django.http import HttpResponse
from django.template.loader import render_to_string
import io as io
import asyncio

from apps.solidarity.models import Solidarities

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError , PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiTypes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound 

from apps.accounts.permissions import IsRole , require_permission
from apps.solidarity.models import Solidarities
from apps.solidarity.models import Faculties
from apps.solidarity.serializers import (
    SolidarityApplySerializer,
    SolidarityStatusSerializer,
    SolidarityListSerializer,
    SolidarityDetailSerializer,
    FacultyDiscountUpdateSerializer,
    LogSerializer,
    DeptFacultiesSerializer
)
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from apps.solidarity.serializers import DeptFacultySummarySerializer
from apps.solidarity.services.solidarity_service import SolidarityService
# from ..serializers import FacultyApprovedResponseSerializer, SolidarityApprovedRowSerializer
from ..serializers import DiscountAssignSerializer, SolidarityDocsSerializer
from apps.solidarity.utils import get_current_student, get_current_admin, handle_report_data, html_to_pdf_buffer, get_client_ip
from apps.solidarity.services.solidarity_service import SolidarityService

class SuperDeptSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = [ IsRole]
    allowed_roles = ['مدير ادارة', 'مشرف النظام']
    serializer_class = SolidarityListSerializer
    queryset = Solidarities.objects.all()

    @extend_schema(
        tags=["Dept&Super Admin APIs"],
        description="Retrieve all solidarity applications with optional filters",
        parameters=[
            OpenApiParameter('faculty', str, description="Filter by faculty ID"),
            OpenApiParameter('status', str, description="Filter by request status"),
            OpenApiParameter('student_id', str, description="Filter by student ID"),
            OpenApiParameter('housing_status', str, description="Filter by housing status"),
            OpenApiParameter('grade', str, description="Filter by grade"),
            OpenApiParameter('disabilities', str, description="Filter by disabilities"),
            OpenApiParameter('father_status', str, description="Filter by father’s status"),
            OpenApiParameter('mother_status', str, description="Filter by mother’s status"),
            OpenApiParameter('total_income', str, description="Filter by total income"),
            OpenApiParameter('family_numbers', str, description="Filter by number of family members"),
        ],
        responses={200: SolidarityListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='all_applications')
    @require_permission('read')
    def all_applications(self, request):
        filters = {key: request.query_params.get(key) for key in [
            'faculty', 'status', 'student_id', 'date_from', 'date_to',
            'housing_status', 'grade', 'father_status', 'mother_status',
            'total_income', 'family_numbers', 'disabilities'
        ]}
        queryset = SolidarityService.get_all_applications(filters=filters)
        return Response(SolidarityListSerializer(queryset, many=True).data)

    @extend_schema(
        tags=["Dept&Super Admin APIs"],
        description="Retrieve detailed application data for a specific student",
        responses={200: SolidarityDetailSerializer, 404: OpenApiResponse(description="Not found")}
    )
    @action(detail=True, methods=['get'], url_path='applications')
    @require_permission('read')
    def student_application_detail(self, request, pk=None):
        client_ip = get_client_ip(request)

        admin = get_current_admin(request)
        solidarity = SolidarityService.get_app_dtl(pk, admin)

        SolidarityService.log_data_access(
        actor_id=admin.admin_id,
        actor_type=admin.role,
        action='عرض بيانات الطلب',
        target_type='تكافل',
        solidarity_id=pk,
        ip_address=client_ip
    )
        return Response(SolidarityDetailSerializer(solidarity).data)



    @extend_schema(
        tags=["Dept&Super Admin APIs"],
        description="Retrieve all uploaded documents for a specific solidarity application",
        responses={200: SolidarityDocsSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='documents')
    @require_permission('read')
    def get_documents(self, request, pk=None):

        admin = get_current_admin(request)
        client_ip = get_client_ip(request)


        docs = SolidarityService.get_docs_by_solidarity_id(pk)
        if not docs.exists():
            return Response({'detail': 'No documents found for this solidarity_id'}, status=404)
       
           # # Log document access
        SolidarityService.log_data_access(
        actor_id=admin.admin_id,
        actor_type=admin.role,
        action='عرض مستندات الطلب',     # “Viewed solidarity documents”
        target_type='تكافل',
        solidarity_id=pk,
        ip_address=client_ip
    )
        return Response(SolidarityDocsSerializer(docs, many=True , context={'request': request}).data)





    @extend_schema(
        tags=["Dept&Super Admin APIs"],
        description="Change status of request to 'Approved'",
        responses={200: SolidarityDetailSerializer, 404: OpenApiResponse(description="Not found")}
    )
    @action(detail=True, methods=['post'], url_path='change_to_approve')
    @require_permission('update')
    #@require_any_permission('update', 'create')  # Can have either
    def change_to_approve(self, request, pk=None):
        admin = get_current_admin(request)
        result = SolidarityService.change_to_approve(pk, admin)
        return Response(result)

    @extend_schema(
        tags=["Dept&Super Admin APIs"],
        description="Change status of request to 'Rejected'",
        responses={200: SolidarityDetailSerializer, 404: OpenApiResponse(description="Not found")}
    )
    @action(detail=True, methods=['post'], url_path='change_to_reject')
    @require_permission('update' )
    def change_to_reject(self, request, pk=None):
        admin = get_current_admin(request)
        result = SolidarityService.change_to_reject(pk, admin)
        return Response(result)

    @extend_schema(
        tags=["Super Admin APIs"],
        description="Retrieve system logs (Restricted to Super/Dept Admins)",
        parameters=[
            OpenApiParameter('actor_id', str, location=OpenApiParameter.QUERY, description="Filter by Admin ID"),
            OpenApiParameter('action', str, location=OpenApiParameter.QUERY, description="Filter by action description (e.g., 'رفض')"),
            OpenApiParameter('target_type', str, location=OpenApiParameter.QUERY, description="Filter by target type (e.g., 'تكافل', 'نشاط')"),
        ],
        responses={200: LogSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='system_logs')
    @require_permission('read')
    def get_system_logs(self, request):
        admin = get_current_admin(request)
        
        if admin.role not in ['مشرف النظام']:
            raise PermissionDenied("You do not have permission to view system logs.")

        filters = {
            'actor_id': request.query_params.get('actor_id'),
            'action': request.query_params.get('action'),
            'target_type': request.query_params.get('target_type'),
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        
        queryset = SolidarityService.get_all_logs(filters=filters)
        
        return Response(LogSerializer(queryset, many=True).data)
    
# ... (داخل كلاس SuperDeptSolidarityViewSet) ...

    @extend_schema(
        tags=["Dept&Super Admin APIs"],
        description="Get Faculty Summary (name, approved amount, approved count, pending count)",
        # نستخدم OpenApiResponse هنا لأن شكل الرد مخصص (Custom Dictionary)
        responses={200: OpenApiResponse(description="Returns rows list and totals object")}
    )
    @action(detail=False, methods=['get'], url_path='faculty_summary')
    @require_permission('read')
    def faculty_summary(self, request):
        admin = get_current_admin(request)
        
        try:
            rows, totals = SolidarityService.get_faculty_summary_for_dept_manager(admin)
        except Exception as e:
            # يفضل إرجاع 400 أو 500 حسب نوع الخطأ، لكن 403 كما طلبت
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

        # استخدام الـ Serializer لضمان تنسيق البيانات (الأرقام العشرية وغيرها)
        serializer = DeptFacultySummarySerializer(rows, many=True)
        
        return Response({
            'rows': serializer.data,
            'totals': {
                'total_approved_amount': str(totals['total_approved_amount']), # تحويل لـ String للحفاظ على الدقة في JSON
                'total_approved_count': totals['total_approved_count'],
                'total_pending_count': totals['total_pending_count'],
                
            }
        }, status=status.HTTP_200_OK)



    def get_permissions(self):
        # Make "faculties" public
        if self.action == 'faculties':
            return []   
        return [permission() for permission in self.permission_classes]
    
    
    @extend_schema(
        tags=["Dept&Super Admin APIs"],
        description="Get Faculties",
        responses={200: OpenApiResponse(description="Returns a list of faculties in the db")}
    )
    @action(detail=False, methods=['get'], url_path='faculties')
    def faculties(self, request):
        try: 
            data = Faculties.objects.all()
        except DatabaseError:
            return Response({"details": "error fetching faculties from db"}, status=500)

        serializer = DeptFacultiesSerializer(data, many=True).data
        
        return Response(serializer, status=status.HTTP_200_OK)


