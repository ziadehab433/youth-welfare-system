import logging
from django.db import DatabaseError
from apps.solidarity.models import Solidarities, Faculties
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from apps.accounts.permissions import IsRole, require_permission
from apps.accounts.utils import (
    get_client_ip,
    get_current_admin,
    get_object_or_404,
    log_data_access,
    get_all_logs
)
from apps.solidarity.serializers import (
    SolidarityListSerializer,
    SolidarityDetailSerializer,
    LogSerializer,
    DeptFacultiesSerializer,
    DeptFacultySummarySerializer,
    SolidarityDocsSerializer
)
from apps.solidarity.services.solidarity_service import SolidarityService
logger = logging.getLogger(__name__)

def extract_filters(request, keys):
    return {k: v for k in keys if (v := request.query_params.get(k)) is not None}

class SuperDeptSolidarityViewSet(viewsets.GenericViewSet):

    permission_classes = [IsRole]
    allowed_roles = ['مدير ادارة', 'مشرف النظام']
    serializer_class = SolidarityListSerializer
    queryset = Solidarities.objects.all()
    def handle_exception(self, exc):
        if isinstance(exc, (NotFound, PermissionDenied, ValidationError)):
            raise
        logger.error(
            f"Unexpected error in {self.action}: {str(exc)}",
            exc_info=True
        )

        return Response(
            {"detail": "An unexpected error occurred"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Retrieve all solidarity applications with optional filters",
        parameters=[
            OpenApiParameter('faculty', str),
            OpenApiParameter('status', str),
            OpenApiParameter('student_id', str),
            OpenApiParameter('housing_status', str),
            OpenApiParameter('grade', str),
            OpenApiParameter('disabilities', str),
            OpenApiParameter('father_status', str),
            OpenApiParameter('mother_status', str),
            OpenApiParameter('total_income', str),
            OpenApiParameter('family_numbers', str),
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
            filters = extract_filters(request, filter_keys)
            queryset = SolidarityService.get_all_applications(filters=filters)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Retrieve detailed application data for a specific student",
        responses={200: SolidarityDetailSerializer}
    )
    @action(detail=True, methods=['get'], url_path='applications')
    @require_permission('read')
    def student_application_detail(self, request, pk=None):
        try:
            admin = get_current_admin(request)
            solidarity = SolidarityService.get_app_dtl(pk, admin)
            serializer = SolidarityDetailSerializer(solidarity)
            return Response(serializer.data)
        except Solidarities.DoesNotExist:
            raise NotFound(f"Solidarity application with id {pk} not found")
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Retrieve documents for solidarity application",
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
            # optional logging
            # log_data_access(
            #     actor_id=admin.admin_id,
            #     actor_type=admin.role,
            #     action='عرض مستندات الطلب',
            #     target_type='تكافل',
            #     solidarity_id=pk,
            #     ip_address=client_ip
            # )

            serializer = SolidarityDocsSerializer(
                docs,
                many=True,
                context={'request': request}
            )
            return Response(serializer.data)
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        request=None,
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Change status of request to 'Approved'",
        responses={200: OpenApiResponse(description="Application approved")}
    )
    @action(detail=True, methods=['post'], url_path='change_to_approve')
    @require_permission('update')
    def change_to_approve(self, request, pk=None):
        try:
            from apps.accounts.utils import execute_admin_action
            
            def business_operation(admin, ip):
                return SolidarityService.change_to_approve(pk, admin)
            
            result = execute_admin_action(
                request=request,
                operation=business_operation,
                action='موافقة مشرف النظام على طلب تكافل',
                target_type='تكافل',
                solidarity_id=pk
            )
            
            return Response(result)
        except Solidarities.DoesNotExist:
            raise NotFound(f"Solidarity application with id {pk} not found")
        except Exception as e:
            return self.handle_exception(e)
        
    @extend_schema(
        request=None,
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Change status of request to 'Rejected'",
        responses={200: OpenApiResponse(description="Application rejected")}
    )
    @action(detail=True, methods=['post'], url_path='change_to_reject')
    @require_permission('update')
    def change_to_reject(self, request, pk=None):
        try:
            from apps.accounts.utils import execute_admin_action
            
            def business_operation(admin, ip):
                return SolidarityService.change_to_reject(pk, admin)
            
            result = execute_admin_action(
                request=request,
                operation=business_operation,
                action='رفض مشرف النظام لطلب تكافل',
                target_type='تكافل',
                solidarity_id=pk
            )
            
            return Response(result)
        except Solidarities.DoesNotExist:
            raise NotFound(f"Solidarity application with id {pk} not found")
        except Exception as e:
            return self.handle_exception(e)
    @extend_schema(
        tags=["Super Admin APIs"],
        description="Retrieve system logs",
        parameters=[
            OpenApiParameter('actor_id', str),
            OpenApiParameter('action', str),
            OpenApiParameter('target_type', str),
        ],
        responses={200: LogSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='system_logs')
    @require_permission('read')
    def get_system_logs(self, request):
        try:
            admin = get_current_admin(request)
            if admin.role != 'مشرف النظام':
                raise PermissionDenied(
                    "Only system administrators can view system logs."
                )
            filter_keys = ['actor_id', 'action', 'target_type']
            filters = extract_filters(request, filter_keys)
            queryset = get_all_logs(filters=filters)
            serializer = LogSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return self.handle_exception(e)

    @extend_schema(
        tags=["Solidarity Dept&Super Admin APIs"],
        description="Get Faculty Summary"
    )
    @action(detail=False, methods=['get'], url_path='faculty_summary')
    @require_permission('read')
    def faculty_summary(self, request):
        try:
            admin = get_current_admin(request)
            rows, totals = SolidarityService.get_faculty_summary_for_dept_manager(admin)
            serializer = DeptFacultySummarySerializer(rows, many=True)
            return Response({
                "rows": serializer.data,
                "totals": {
                    "total_approved_amount": str(totals["total_approved_amount"]),
                    "total_approved_count": totals["total_approved_count"],
                    "total_pending_count": totals["total_pending_count"],
                }
            })
        except Exception as e:
            return self.handle_exception(e)
