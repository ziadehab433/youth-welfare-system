from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from apps.solidarity.models import Solidarities
from apps.solidarity.api.serializers import (
    SolidarityApplySerializer, SolidarityStatusSerializer,
    SolidarityListSerializer, SolidarityDetailSerializer
)
from apps.solidarity.api.utils import get_current_student, get_current_admin
from apps.solidarity.services.solidarity_service import SolidarityService
from .serializers import DiscountAssignSerializer
from apps.solidarity.api.serializers import FacultyDiscountUpdateSerializer
from rest_framework.parsers import MultiPartParser, FormParser

# ============================================================
# STUDENT VIEWSET
# ============================================================


class StudentSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["Student APIs"],
        description="Submit a new solidarity application (multipart/form-data). Upload optional documents.",
        request=SolidarityApplySerializer,
        responses={201: SolidarityDetailSerializer, 400: OpenApiResponse(description="Validation error")}
    )
    @action(detail=False, methods=['post'], url_path='apply')
    def apply(self, request):
        serializer = SolidarityApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            student = get_current_student(request)
            data = serializer.validated_data

            # Build uploaded_docs dict for the service: key -> InMemoryUploadedFile
            uploaded_docs = {}
            for field in ['social_research_file', 'salary_proof_file', 'father_id_file', 'student_id_file', 'land_ownership_file' , 'sd_file']:
                if field in request.FILES:
                    uploaded_docs[field] = request.FILES[field]

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
        try:
            student = get_current_student(request)
            qs = Solidarities.objects.filter(student=student).order_by('-created_at')
            return Response(SolidarityStatusSerializer(qs, many=True).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ============================================================
# FACULTY ADMIN VIEWSET
# ============================================================
class FacultyAdminSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = SolidarityListSerializer

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="List all solidarity applications available for the current faculty admin",
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
        admin = get_current_admin(request)
        try:
            solidarity = SolidarityService.get_application_detail(pk, admin)
        except ValidationError as e:
            error_msg = str(e)
            if "from your faculty" in error_msg:
                return Response({'error': error_msg}, status=status.HTTP_403_FORBIDDEN)
            elif "not found" in error_msg.lower():
                return Response({'error': error_msg}, status=status.HTTP_404_NOT_FOUND)
            else:
                Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SolidarityDetailSerializer(solidarity).data)

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Approve a solidarity application",
        request=None,
        responses={200: OpenApiResponse(description="Application approved successfully"), 400: OpenApiResponse(description="Validation error")}
    )
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        admin = get_current_admin(request)
        try:
            result = SolidarityService.approve_application(pk, admin)
            return Response({'message': result['message']})
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Pre-approve a solidarity application before final approval",
        responses={200: OpenApiResponse(description="Application pre-approved successfully")},
    )
    @action(detail=True, methods=['post'], url_path='pre_approve')
    def pre_approve(self, request, pk=None):
        admin = get_current_admin(request)
        try:
            result = SolidarityService.pre_approve_application(pk, admin)
            return Response({'message': result['message']})
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Reject a solidarity application",
        request=None,
        responses={200: OpenApiResponse(description="Application rejected successfully"), 400: OpenApiResponse(description="Validation error")}
    )
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        admin = get_current_admin(request)
        try:
            result = SolidarityService.reject_application(pk, admin)
            return Response({'message': result['message']})
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Assign discount(s) to a solidarity application based on faculty discount values",
        request=DiscountAssignSerializer,
        responses={200: OpenApiResponse(description="Discount assigned successfully")}
    )
    @action(detail=True, methods=['patch'], url_path='assign-discount')
    def assign_discount(self, request, pk=None):
        admin = get_current_admin(request)
        serializer = DiscountAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        discount_types = serializer.validated_data['discount_types']

        try:
            solidarity = SolidarityService.get_application_detail(pk, admin)
            updated_solidarity = SolidarityService.assign_discounts(admin, solidarity, discount_types)
            return Response({
                "message": "تم تطبيق الخصم بنجاح",
                "total_discount": updated_solidarity.total_discount
            }, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Faculty Admin APIs"],
        description="Update faculty discount values for the current faculty",
        request=FacultyDiscountUpdateSerializer,
        responses={200: OpenApiResponse(description="Faculty discounts updated successfully")}
    )
    @action(detail=False, methods=['patch'], url_path='update-faculty-discounts')
    def update_faculty_discounts(self, request):
        admin = get_current_admin(request)
        serializer = FacultyDiscountUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_faculty = SolidarityService.update_faculty_discounts(admin, serializer.validated_data)
            return Response({
                "message": "تم تحديث خصومات الكلية بنجاح",
                "faculty_discounts": {
                    "aff_discount": updated_faculty.aff_discount,
                    "reg_discount": updated_faculty.reg_discount,
                    "bk_discount": updated_faculty.bk_discount,
                    "full_discount": updated_faculty.full_discount,
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        }, status=status.HTTP_200_OK)
# ============================================================
# SUPER/DEPT ADMIN VIEWSET
# ============================================================
class SuperDeptSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = SolidarityListSerializer
    queryset = Solidarities.objects.all()

    @extend_schema(
            tags = ["Dept&super Admin API"],
        description="Retrieve all solidarity applications with optional filters",
        parameters=[
            OpenApiParameter('faculty', str, description="Filter by faculty ID"),
            OpenApiParameter('status', str, description="Filter by request status"),
            OpenApiParameter('student_id', str, description="Filter by student ID"),
            OpenApiParameter('date_from', str, description="Filter by start date (YYYY-MM-DD)"),
            OpenApiParameter('date_to', str, description="Filter by end date (YYYY-MM-DD)"),
            OpenApiParameter('housing_status', str, description="Filter by housing status"),
            OpenApiParameter('grade', str, description="Filter by grade"),
            OpenApiParameter('father_status', str, description="Filter by father’s status"),
            OpenApiParameter('mother_status', str, description="Filter by mother’s status"),
            OpenApiParameter('total_income', str, description="Filter by total income"),
            OpenApiParameter('family_numbers', str, description="Filter by number of family members"),
        ],
        responses={200: SolidarityListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='all-applications')
    def all_applications(self, request):
        filters = {
            'faculty': request.query_params.get('faculty'),
            'status': request.query_params.get('status'),
            'student_id': request.query_params.get('student_id'),
            'date_from': request.query_params.get('date_from'),
            'date_to': request.query_params.get('date_to'),
            'housing_status': request.query_params.get('housing_status'),
            'grade': request.query_params.get('grade'),
            'father_status': request.query_params.get('father_status'),
            'mother_status': request.query_params.get('mother_status'),
            'total_income': request.query_params.get('total_income'),
            'family_numbers': request.query_params.get('family_numbers'),
        }
        queryset = SolidarityService.get_all_applications(filters=filters)
        serializer = SolidarityListSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags = ["Dept&super Admin API"],
        description="Retrieve detailed application data for a specific student",
        responses={200: SolidarityDetailSerializer, 404: OpenApiResponse(description="Not found")}
    )
    @action(detail=True, methods=['get'], url_path='applications')
    def student_application_detail(self, request, pk=None):
        admin = get_current_admin(request)
        solidarity = SolidarityService.get_app_dtl(pk,admin)
        return Response(SolidarityDetailSerializer(solidarity).data)


    @extend_schema(
        tags = ["Dept&super Admin API"],
        description="change status of request to approve for a specific student",
        responses={200: SolidarityDetailSerializer, 404: OpenApiResponse(description="Not found")}
    )
    @action(detail=True, methods=['post'], url_path='change_to_approve')
    def change_to_approve(self, request, pk=None):
        admin = get_current_admin(request)
        try:
            result = SolidarityService.change_to_approve(pk, admin)
            return Response(result, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Solidarities.DoesNotExist:
            return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)
        
    @extend_schema(
        tags = ["Dept&super Admin API"],
        description="change status of request to reject for a specific student",
        responses={200: SolidarityDetailSerializer, 404: OpenApiResponse(description="Not found")}
    )   
    @action(detail=True, methods=['post'], url_path='change_to_reject')
    def change_to_reject(self, request, pk=None):
        admin = get_current_admin(request)
        try:
            result = SolidarityService.change_to_reject(pk, admin)
            return Response(result, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Solidarities.DoesNotExist:
            return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)