from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.solidarity.models import Solidarities
from apps.solidarity.api.serializers import (
    SolidarityApplySerializer, SolidarityStatusSerializer,
    SolidarityListSerializer, SolidarityDetailSerializer
)
from drf_spectacular.utils import extend_schema

from apps.solidarity.api.utils import get_current_student, get_current_admin
from apps.solidarity.services.solidarity_service import SolidarityService
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class StudentSolidarityViewSet(viewsets.GenericViewSet):
    queryset = Solidarities.objects.none()
    permission_classes = [AllowAny]
    serializer_class = SolidarityApplySerializer

    @swagger_auto_schema(
        request_body=SolidarityApplySerializer,
        responses={201: SolidarityDetailSerializer}
    )
    @action(detail=False, methods=['post'], url_path='apply')
    def apply(self, request):
        serializer = SolidarityApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            student = get_current_student(request)
            solidarity = SolidarityService.create_application(student, serializer.validated_data)
            return Response(SolidarityDetailSerializer(solidarity).data, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses={200: SolidarityStatusSerializer(many=True)})
    @action(detail=False, methods=['get'], url_path='status')
    def status(self, request):
        try:
            student = get_current_student(request)
            qs = SolidarityService.get_student_applications(student)
            return Response(SolidarityStatusSerializer(qs, many=True).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class FacultyAdminSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = SolidarityListSerializer

    @swagger_auto_schema(responses={200: SolidarityListSerializer(many=True)})
    @action(detail=False, methods=['get'], url_path='applications')
    def list_applications(self, request):
        admin = get_current_admin(request)
        qs = SolidarityService.get_applications_for_review(admin)
        return Response(SolidarityListSerializer(qs, many=True).data)

    @swagger_auto_schema(responses={200: SolidarityDetailSerializer})
    @action(detail=True, methods=['get'], url_path='applications/(?P<pk>[^/.]+)')
    def get_application(self, request, pk=None):
        admin = get_current_admin(request)
        solidarity = SolidarityService.get_application_detail(pk)
        if admin.role == 'faculty_admin' and solidarity.faculty_id != admin.faculty_id:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return Response(SolidarityDetailSerializer(solidarity).data)


    @extend_schema(request=None)    
    @action(
    detail=True,
    methods=['post'],
    url_path='applications/(?P<pk>[^/.]+)/approve',
    )
    def approve(self, request, pk=None):
        admin = get_current_admin(request)
        try:
            result = SolidarityService.approve_application(pk, admin)
            return Response({'message': result['message']})
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=None)    
    @action(
    detail=True,
    methods=['post'],
    url_path='applications/(?P<pk>[^/.]+)/reject',
    )
    @swagger_auto_schema(responses={200: 'Application rejected successfully'})
    def reject(self, request, pk=None):
        admin = get_current_admin(request)
        try:
            result = SolidarityService.reject_application(pk, admin)
            return Response({'message': result['message']})
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        
class SuperDeptSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = SolidarityListSerializer
    queryset = Solidarities.objects.all()

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('faculty', openapi.IN_QUERY, description="Filter by faculty ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by request status (PENDING, APPROVED, REJECTED)", type=openapi.TYPE_STRING),
            openapi.Parameter('student_id', openapi.IN_QUERY, description="Filter by student ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('date_from', openapi.IN_QUERY, description="Filter by start date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY, description="Filter by end date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('housing_status', openapi.IN_QUERY, description="Filter by housing status (rent, owned)", type=openapi.TYPE_STRING),
            openapi.Parameter('grade', openapi.IN_QUERY, description="Filter by grade", type=openapi.TYPE_STRING),
            openapi.Parameter('father_status', openapi.IN_QUERY, description="Filter by father's status", type=openapi.TYPE_STRING),
            openapi.Parameter('mother_status', openapi.IN_QUERY, description="Filter by mother's status", type=openapi.TYPE_STRING),
            openapi.Parameter('total_income', openapi.IN_QUERY, description="Filter by total income", type=openapi.TYPE_NUMBER),
            openapi.Parameter('family_numbers', openapi.IN_QUERY, description="Filter by number of family members", type=openapi.TYPE_INTEGER),
        ],
        responses={200: SolidarityListSerializer(many=True)},
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

    @swagger_auto_schema(responses={200: SolidarityDetailSerializer})
    @action(detail=True, methods=['get'], url_path='student/(?P<pk>[^/.]+)')
    def student_application_detail(self, request, pk=None):
        solidarity = SolidarityService.get_application_detail(pk)
        return Response(SolidarityDetailSerializer(solidarity).data)
