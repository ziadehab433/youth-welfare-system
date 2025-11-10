# apps/solidarity/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError , PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.parsers import MultiPartParser, FormParser

# fixed import — use IsRole, IsStudent, and IsFacultyAdmin
from apps.accounts.permissions import IsRole, IsStudent, IsFacultyAdmin
from apps.solidarity.models import Solidarities
from apps.solidarity.api.serializers import (
    SolidarityApplySerializer,
    SolidarityStatusSerializer,
    SolidarityListSerializer,
    SolidarityDetailSerializer,
    FacultyDiscountUpdateSerializer,
    LogSerializer,
)
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

        docs = SolidarityService.get_docs_by_solidarity_id(pk)
        if not docs.exists():
            return Response({'detail': 'No documents found for this solidarity_id'}, status=404)
           # # Log document access
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
            OpenApiParameter('target_type', str, location=OpenApiParameter.QUERY, description="Filter by target type (e.g., 'solidarity', 'student')"),
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