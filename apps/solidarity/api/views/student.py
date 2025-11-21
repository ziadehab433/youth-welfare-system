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
from ..serializers import FacultyApprovedResponseSerializer, SolidarityApprovedRowSerializer
from ..serializers import DiscountAssignSerializer, SolidarityDocsSerializer
from apps.solidarity.api.utils import get_current_student, get_current_admin, handle_report_data, html_to_pdf_buffer, get_client_ip
from apps.solidarity.services.solidarity_service import SolidarityService

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