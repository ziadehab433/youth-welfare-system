# apps/solidarity/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError , PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound 

from apps.accounts.permissions import IsRole
from apps.solidarity.models import Solidarities
from apps.solidarity.api.serializers import (
    SolidarityApplySerializer,
    SolidarityStatusSerializer,
    SolidarityListSerializer,
    SolidarityDetailSerializer,
    FacultyDiscountUpdateSerializer,
    LogSerializer,
)
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from apps.solidarity.api.serializers import DeptFacultySummarySerializer
from apps.solidarity.services.solidarity_service import SolidarityService
from .serializers import FacultyApprovedResponseSerializer, SolidarityApprovedRowSerializer
from .serializers import DiscountAssignSerializer, SolidarityDocsSerializer
from apps.solidarity.api.utils import get_current_student, get_current_admin
from apps.solidarity.services.solidarity_service import SolidarityService
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # first IP in the list
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================
# STUDENT VIEWSET
# ============================================================

class StudentSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = [ IsRole]
    allowed_roles = ['student']
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["Student APIs"],
        description="Submit a new solidarity application (multipart/form-data). Upload optional documents.",
        request=SolidarityApplySerializer,
        responses={201: SolidarityDetailSerializer, 400: OpenApiResponse(description="Validation error")}
    )
    
    @action(detail=False, methods=['post'], url_path='apply')
    def apply(self, request):
        student = get_current_student(request)
        serializer = SolidarityApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = serializer.validated_data
            uploaded_docs = {
                field: request.FILES[field]
                for field in [
                    'social_research_file', 'salary_proof_file',
                    'father_id_file', 'student_id_file',
                    'land_ownership_file', 'sd_file'
                ]
                if field in request.FILES
            }

            solidarity = SolidarityService.create_application(student, data, uploaded_docs=uploaded_docs)
            return Response(SolidarityDetailSerializer(solidarity).data, status=status.HTTP_201_CREATED)

        except (DjangoValidationError, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Student APIs"],
        description="Get the list of solidarity applications for the logged-in student",
        responses={200: SolidarityStatusSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='status')
    def status(self, request):
        student = get_current_student(request)
        qs = Solidarities.objects.filter(student=student).order_by('-created_at')
        return Response(SolidarityStatusSerializer(qs, many=True).data)

    @extend_schema(
        tags=["Student APIs"],
        description="Get detailed information for a specific solidarity application (including all documents)",
        responses={
            200: SolidarityDetailSerializer, 
            404: OpenApiResponse(description="Application not found or access denied")
        }
    )
    @action(detail=True, methods=['get'], url_path='detail')
    def get_application_detail(self, request, pk=None):
        student = get_current_student(request)
        
        try:
            solidarity = SolidarityService.get_student_application_detail(pk, student)
            docs = SolidarityService.get_docs_by_solidarity_id(pk)
            solidarity_data = SolidarityDetailSerializer(solidarity).data
            context = {'request': request}
            solidarity_data['documents'] = SolidarityDocsSerializer(docs, many=True, context=context).data
            
            return Response(solidarity_data)

        except NotFound as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
# ============================================================
# FACULTY ADMIN VIEWSET
# ============================================================

class FacultyAdminSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = [ IsRole]
    allowed_roles = ['مسؤول كلية']
    serializer_class = SolidarityListSerializer

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="List all solidarity applications for the current faculty admin",
        responses={200: SolidarityListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='applications')
    def list_applications(self, request):
        admin = get_current_admin(request)
        qs = SolidarityService.get_applications_for_review(admin)
        return Response(SolidarityListSerializer(qs, many=True).data)

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Retrieve details of a specific solidarity application",
        responses={200: SolidarityDetailSerializer, 403: OpenApiResponse(description="Forbidden"), 404: OpenApiResponse(description="Not found")}
    )
    @action(detail=True, methods=['get'], url_path='applications')
    def get_application(self, request, pk=None):
        client_ip = get_client_ip(request)

        admin = get_current_admin(request)
        try:
            solidarity = SolidarityService.get_application_detail(pk, admin)
        except ValidationError as e:
            msg = str(e)
            if "from your faculty" in msg:
                return Response({'error': msg}, status=status.HTTP_403_FORBIDDEN)
            elif "not found" in msg.lower():
                return Response({'error': msg}, status=status.HTTP_404_NOT_FOUND)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
            #  Log that this admin viewed the solidarity details

        SolidarityService.log_data_access(
            actor_id=admin.admin_id,
            actor_type=admin.role,
            action='عرض بيانات الطلب',      # “Viewed solidarity details”
            target_type='تكافل',
            solidarity_id=pk,
            ip_address=client_ip

        )
        return Response(SolidarityDetailSerializer(solidarity).data)

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Retrieve all uploaded documents for a specific solidarity application",
        responses={200: SolidarityDocsSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='documents')
    def get_documents(self, request, pk=None):

        admin = get_current_admin(request)
        docs_qs = SolidarityService.get_docs_by_solidarity_id(pk)

        docs = SolidarityService.get_docs_by_solidarity_id(pk)
        if not docs.exists():
            return Response({'detail': 'No documents found for this solidarity_id'}, status=404)
           # # Log document access
        solidarity = docs_qs.first().solidarity 
        if admin.faculty_id != solidarity.faculty_id:
           raise PermissionDenied("You can only view applications from your faculty.")      
        client_ip = get_client_ip(request)

        SolidarityService.log_data_access(
        actor_id=admin.admin_id,
        actor_type=admin.role,
        action='عرض مستندات الطلب',     # “Viewed solidarity documents”
        target_type='تكافل',
        solidarity_id=pk,
        ip_address=client_ip
    )
       # ""

        return Response(SolidarityDocsSerializer(docs, many=True , context={'request': request}).data)


    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Approve a solidarity application",
        responses={200: OpenApiResponse(description="Application approved successfully")}
    )
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        admin = get_current_admin(request)
        result = SolidarityService.approve_application(pk, admin)
        return Response({'message': result['message']})

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Pre-approve a solidarity application before final approval",
        responses={200: OpenApiResponse(description="Application pre-approved successfully")}
    )
    @action(detail=True, methods=['post'], url_path='pre_approve')
    def pre_approve(self, request, pk=None):
        admin = get_current_admin(request)
        result = SolidarityService.pre_approve_application(pk, admin)
        return Response({'message': result['message']})

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Reject a solidarity application",
        responses={200: OpenApiResponse(description="Application rejected successfully")}
    )
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        admin = get_current_admin(request)
        result = SolidarityService.reject_application(pk, admin)
        return Response({'message': result['message']})

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Assign discount(s) to a solidarity application",
        request=DiscountAssignSerializer,
        responses={200: OpenApiResponse(description="Discount assigned successfully")}
    )
    @action(detail=True, methods=['patch'], url_path='assign_discount')
    def assign_discount(self, request, pk=None):
        admin = get_current_admin(request)
        serializer = DiscountAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        discount_data = serializer.validated_data['discounts']
        
        solidarity = SolidarityService.get_application_detail(pk, admin)
        updated_solidarity = SolidarityService.assign_discounts(admin, solidarity, discount_data)

        return Response({
            "message": "تم تطبيق الخصم بنجاح",
            "total_discount": updated_solidarity.total_discount
        })
    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Update faculty discount values for the current faculty",
        request=FacultyDiscountUpdateSerializer,
        responses={200: OpenApiResponse(description="Faculty discounts updated successfully")}
    )
    @action(detail=False, methods=['patch'], url_path='update_faculty_discounts')
    def update_faculty_discounts(self, request):
        admin = get_current_admin(request)
        serializer = FacultyDiscountUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_faculty = SolidarityService.update_faculty_discounts(admin, serializer.validated_data)
        return Response({
            "message": "تم تحديث خصومات الكلية بنجاح",
            "faculty_discounts": {
                "aff_discount": updated_faculty.aff_discount,
                "reg_discount": updated_faculty.reg_discount,
                "bk_discount": updated_faculty.bk_discount,
                "full_discount": updated_faculty.full_discount,
            }
        })

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Get current faculty discount values",
        responses={200: OpenApiResponse(description="Faculty discounts retrieved successfully")}
    )
    @action(detail=False, methods=['get'], url_path='faculty/discounts')
    def get_faculty_discounts(self, request):
        admin = get_current_admin(request)
        faculty = admin.faculty
        data = {
            "aff_discount": faculty.aff_discount,
            "reg_discount": faculty.reg_discount,
            "bk_discount": faculty.bk_discount,
            "full_discount": faculty.full_discount
        }
        return Response({
            "message": "تم جلب خصومات الكلية بنجاح",
            "discounts": data
        })
    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Get approved applications summary for faculty admin",
        responses={200: FacultyApprovedResponseSerializer}  
    )
    @action(detail=False, methods=['get'], url_path='faculty_approved')
    def faculty_approved(self, request):
        admin = get_current_admin(request)
        rows_qs, totals = SolidarityService.get_approved_for_faculty_admin(admin)

        rows = []
        for r in rows_qs:
            rows.append({
                'solidarity_id': r['solidarity_id'],
                'student_name': r['student_name'],
                'student_id': r['student_pk'],
                'total_income': r.get('total_income') or 0,
                'discount_amount': r.get('total_discount_coalesced') or 0
            })

        serializer = SolidarityApprovedRowSerializer(rows, many=True)
        return Response({
            'total_approved': totals['total_approved'],
            'total_discount': totals['total_discount'],
            'results': serializer.data
        })
# ============================================================
# SUPER / DEPARTMENT ADMIN VIEWSET
# ============================================================

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
                'total_pending_count': totals['total_pending_count']
            }
        }, status=status.HTTP_200_OK)