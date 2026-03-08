from django.db import DatabaseError
from django.http import HttpResponse
from django.template.loader import render_to_string
import io as io
import asyncio
import logging
from apps.solidarity.models import Solidarities, Faculties
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.parsers import MultiPartParser, FormParser
from apps.accounts.permissions import IsRole, require_permission
from apps.solidarity.serializers import (
    SolidarityApplySerializer,
    SolidarityStatusSerializer,
    SolidarityListSerializer,
    SolidarityDetailSerializer,
    FacultyDiscountUpdateSerializer,
    LogSerializer,
    DeptFacultiesSerializer,
    DeptFacultySummarySerializer,
    DiscountAssignSerializer,
    SolidarityDocsSerializer
)
from apps.solidarity.services.solidarity_service import SolidarityService
from apps.accounts.utils import (
    get_client_ip, 
    get_current_admin, 
    get_current_student, 
    get_object_or_404,
    log_data_access,
    get_all_logs
)
from apps.solidarity.utils import handle_report_data, html_to_pdf_buffer

class SuperDeptSolidarityViewSet(viewsets.GenericViewSet):
    permission_classes = []  
    allowed_roles = ['مدير ادارة', 'مشرف النظام']
    serializer_class = SolidarityListSerializer
    queryset = Solidarities.objects.all()
    logger = logging.getLogger('solidarity.views')

    def get_permissions(self):
        if self.action == 'faculties':
            return []
        return []

    def handle_exception(self, exc):
        if isinstance(exc, (NotFound, PermissionDenied, ValidationError)):
            raise
        self.logger.error(f"Unexpected error in {self.action}: {str(exc)}", exc_info=True)
        return Response(
            {"detail": "An unexpected error occurred"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
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
        try:
            filter_keys = [
                'faculty', 'status', 'student_id', 'date_from', 'date_to',
                'housing_status', 'grade', 'father_status', 'mother_status',
                'total_income', 'family_numbers', 'disabilities'
            ]
            filters = {k: v for k in filter_keys if (v := request.query_params.get(k)) is not None}
            
            queryset = SolidarityService.get_all_applications(filters=filters)
            return Response(SolidarityListSerializer(queryset, many=True).data)
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Retrieve detailed application data for a specific student",
        responses={200: SolidarityDetailSerializer, 404: OpenApiResponse(description="Not found")}
    )
    @action(detail=True, methods=['get'], url_path='applications')
    @require_permission('read')
    def student_application_detail(self, request, pk=None):
        try:
            client_ip = get_client_ip(request)
            admin = get_current_admin(request)
            solidarity = SolidarityService.get_app_dtl(pk, admin)
            
            # Log data access (commented out for now)
            # log_data_access(
            #     actor_id=admin.admin_id,
            #     actor_type=admin.role,
            #     action='عرض بيانات الطلب',
            #     target_type='تكافل',
            #     solidarity_id=pk,
            #     ip_address=client_ip
            # )
            
            return Response(SolidarityDetailSerializer(solidarity).data)
        except Solidarities.DoesNotExist:
            raise NotFound(f"Solidarity application with id {pk} not found")
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Retrieve all uploaded documents for a specific solidarity application",
        responses={200: SolidarityDocsSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='documents')
    @require_permission('read')
    def get_documents(self, request, pk=None):
        try:
            get_object_or_404(Solidarities, solidarity_id=pk)
            
            admin = get_current_admin(request)
            client_ip = get_client_ip(request)

            docs = SolidarityService.get_docs_by_solidarity_id(pk)
            if not docs.exists():
                return Response(
                    {'detail': 'No documents found for this solidarity_id'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
           
            # Log document access (commented out for now)
            # log_data_access(
            #     actor_id=admin.admin_id,
            #     actor_type=admin.role,
            #     action='عرض مستندات الطلب',
            #     target_type='تكافل',
            #     solidarity_id=pk,
            #     ip_address=client_ip
            # )
            
            return Response(
                SolidarityDocsSerializer(docs, many=True, context={'request': request}).data
            )
        except Solidarities.DoesNotExist:
            raise NotFound(f"Solidarity application with id {pk} not found")
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Change status of request to 'Approved'",
        responses={200: SolidarityDetailSerializer, 404: OpenApiResponse(description="Not found")}
    )
    @action(detail=True, methods=['post'], url_path='change_to_approve')
    @require_permission('update')
    def change_to_approve(self, request, pk=None):
        try:
            admin = get_current_admin(request)
            result = SolidarityService.change_to_approve(pk, admin)
            return Response(result)
        except Solidarities.DoesNotExist:
            raise NotFound(f"Solidarity application with id {pk} not found")
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Change status of request to 'Rejected'",
        responses={200: SolidarityDetailSerializer, 404: OpenApiResponse(description="Not found")}
    )
    @action(detail=True, methods=['post'], url_path='change_to_reject')
    @require_permission('update')
    def change_to_reject(self, request, pk=None):
        try:
            admin = get_current_admin(request)
            result = SolidarityService.change_to_reject(pk, admin)
            return Response(result)
        except Solidarities.DoesNotExist:
            raise NotFound(f"Solidarity application with id {pk} not found")
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        tags=["Super Admin APIs"],
        description="Retrieve system logs (Restricted to Super/Dept Admins)",
        parameters=[
            OpenApiParameter('actor_id', str, location=OpenApiParameter.QUERY, description="Filter by Admin ID"),
            OpenApiParameter('action', str, location=OpenApiParameter.QUERY, description="Filter by action description"),
            OpenApiParameter('target_type', str, location=OpenApiParameter.QUERY, description="Filter by target type"),
        ],
        responses={200: LogSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='system_logs')
    @require_permission('read')
    def get_system_logs(self, request):
        try:
            admin = get_current_admin(request)
            if admin.role not in ['مشرف النظام']:
                raise PermissionDenied("Only system administrators can view system logs.")

            filter_keys = ['actor_id', 'action', 'target_type']
            filters = {k: v for k in filter_keys if (v := request.query_params.get(k)) is not None}
            
            queryset = get_all_logs(filters=filters)
            return Response(LogSerializer(queryset, many=True).data)
            
        except PermissionDenied:
            raise
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Get Faculty Summary (name, approved amount, approved count, pending count)",
        responses={200: OpenApiResponse(description="Returns rows list and totals object")}
    )
    @action(detail=False, methods=['get'], url_path='faculty_summary')
    @require_permission('read')
    def faculty_summary(self, request):
        try:
            admin = get_current_admin(request)
            rows, totals = SolidarityService.get_faculty_summary_for_dept_manager(admin)
            
            serializer = DeptFacultySummarySerializer(rows, many=True)
            
            return Response({
                'rows': serializer.data,
                'totals': {
                    'total_approved_amount': str(totals['total_approved_amount']),
                    'total_approved_count': totals['total_approved_count'],
                    'total_pending_count': totals['total_pending_count'],
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Get Faculties",
        responses={200: OpenApiResponse(description="Returns a list of faculties in the db")}
    )
    @action(detail=False, methods=['get'], url_path='faculties')
    def faculties(self, request):
        try:
            data = Faculties.objects.all()
            serializer = DeptFacultiesSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except DatabaseError as e:
            self.logger.error(f"Database error in faculties: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Error fetching faculties from database"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in faculties: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


