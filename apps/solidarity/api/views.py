from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.solidarity.models import Solidarities
from apps.solidarity.api.serializers import (
    SolidarityApplySerializer, SolidarityStatusSerializer,
    SolidarityListSerializer, SolidarityDetailSerializer,
    ApprovalSerializer, RejectionSerializer
)
from rest_framework.permissions import AllowAny
from apps.solidarity.api.utils import get_current_student, get_current_admin
from apps.solidarity.services.solidarity_service import SolidarityService

class StudentSolidarityViewSet(viewsets.GenericViewSet):
    queryset = Solidarities.objects.none()
    permission_classes = [AllowAny]  # Allow any for testing

    @action(detail=False, methods=['post'], url_path='apply')
    def apply(self, request):
        serializer = SolidarityApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            student = get_current_student(request)
            solidarity = SolidarityService.create_application(student, serializer.validated_data)
            out = SolidarityDetailSerializer(solidarity)
            return Response(out.data, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

    @action(detail=False, methods=['get'])
    def list_applications(self, request):
        admin = get_current_admin(request)
        qs = SolidarityService.get_applications_for_review(admin)
        return Response(SolidarityListSerializer(qs, many=True).data)

    @action(detail=True, methods=['get'])
    def get_application(self, request, pk=None):
        admin = get_current_admin(request)
        solidarity = SolidarityService.get_application_detail(pk)
        if admin.role == 'FACULTY_ADMIN' and solidarity.faculty_id != admin.faculty_id:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return Response(SolidarityDetailSerializer(solidarity).data)
        

    @action(detail=True, methods=['post'], url_path='applications/(?P<pk>[^/.]+)/approve')
    def approve(self, request, pk=None):
        admin = get_current_admin(request)
        try:
            result = SolidarityService.approve_application(pk, admin)
            return Response({'message': result['message']})
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='applications/(?P<pk>[^/.]+)/reject')
    def reject(self, request, pk=None):
        admin = get_current_admin(request)
        ser = RejectionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            result = SolidarityService.reject_application(pk, admin, ser.validated_data.get('rejection_reason'))
            return Response({'message': result['message']})
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SuperDeptSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]  # Allow any for testing

    @action(detail=False, methods=['get'], url_path='all-applications')
    def all_applications(self, request):
        filters = {
            'faculty': request.query_params.get('faculty'),
            'status': request.query_params.get('status'),
            'student_id': request.query_params.get('student_id'),
            'date_from': request.query_params.get('date_from'),
            'date_to': request.query_params.get('date_to'),
        }
        qs = SolidarityService.get_all_applications(filters)
        return Response(SolidarityListSerializer(qs, many=True).data)

    @action(detail=True, methods=['get'], url_path='student')
    def student_application_detail(self, request, pk=None):
        solidarity = SolidarityService.get_application_detail(pk)
        return Response(SolidarityDetailSerializer(solidarity).data)