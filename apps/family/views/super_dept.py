from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from apps.family.models import Families
from apps.accounts.permissions import IsRole
from apps.family.serializers import FamiliesListSerializer, FamiliesDetailSerializer
from rest_framework.decorators import action
from drf_spectacular.utils import OpenApiResponse
from apps.accounts.utils import get_client_ip, log_data_access
from rest_framework.response import Response
from rest_framework import viewsets, status
@extend_schema(tags=["Family Super_Dept"])
class SuperDeptFamilyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Families.objects.all()
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['مدير ادارة', 'مشرف النظام']
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FamiliesDetailSerializer
        return FamiliesListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        family_type = self.request.query_params.get('type')
        if family_type:
            queryset = queryset.filter(type=family_type)
        faculty_id = self.request.query_params.get('faculty')
        if faculty_id:
            queryset = queryset.filter(faculty_id=faculty_id)

        return queryset
    @extend_schema(
        operation_id="list_families_filtered",
        description="Fetch families filtered by Type (e.g., specialized) and Faculty ID.",
        parameters=[
            OpenApiParameter(
                name='type', 
                description='Family Type', 
                required=False, 
                type=str,
                enum=['مركزية', 'نوعية', 'اصدقاء البيئة'] 
            ),
            OpenApiParameter(
                name='faculty', 
                description='Faculty ID (e.g., for specialized families)', 
                required=False, 
                type=int
            ),
        ],
        responses={200: FamiliesListSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    @extend_schema(
        operation_id="get_family_details_with_events",
        description="Fetch all details for a specific family, INCLUDING its events history.",
        responses={200: FamiliesDetailSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    @extend_schema(
        description="Reject the family request (changes status to 'مرفوض').",
        request=None,
        responses={
            200: OpenApiResponse(description="Family rejected successfully"),
            400: OpenApiResponse(description="Cannot reject family in current status")
        }
    )
    @action(detail=True, methods=['patch'], url_path='reject')
    def reject_family(self, request, pk=None):
        family = self.get_object()
        if family.status not in ['منتظر', 'موافقة مبدئية']:
            return Response(
                {"error": "لا يمكن رفض الطلب. الحالة الحالية لا تسمح بذلك."},
                status=status.HTTP_400_BAD_REQUEST
            )
        family.status = 'مرفوض'
        family.save()
        log_data_access(
            actor_id=request.user.admin_id,
            actor_type=request.user.role,
            action='رفض الأسرة (إدارة مركزية)',
            target_type='اسر',
            family_id=family.family_id,
            ip_address=get_client_ip(request)
        )

        return Response({"message": "تم رفض الأسرة بنجاح"}, status=status.HTTP_200_OK)
    @extend_schema(
        description="Approve the family creation request and convert it to an active family (Status: 'مقبول').",
        request=None,
        responses={
            200: OpenApiResponse(description="Family finally approved and active"),
            400: OpenApiResponse(description="Invalid status for final approval")
        }
    )
    @action(detail=True, methods=['post'], url_path='final_approve')
    def final_approve(self, request, pk=None):
        family = self.get_object()
        if family.status != 'موافقة مبدئية':
             return Response(
                {"error": "يجب أن تكون الأسرة حاصلة على 'موافقة مبدئية' أولاً لمنح الموافقة النهائية."},
                status=status.HTTP_400_BAD_REQUEST
            )
        family.status = 'مقبول'
        family.approved_by = request.user 
        family.save()
        log_data_access(
            actor_id=request.user.admin_id,
            actor_type=request.user.role,
            action='موافقة نهائية (إدارة مركزية)',
            target_type='اسر',
            family_id=family.family_id,
            ip_address=get_client_ip(request)
        )

        return Response({"message": "تم تفعيل الأسرة بنجاح"}, status=status.HTTP_200_OK)
    @extend_schema(
        description="Fetch all 'Specialized' (نوعية) families with 'Pre-Approved' (موافقة مبدئية) status, filtered by faculty.",
        parameters=[
            OpenApiParameter(
                name='faculty', 
                description='Filter by Faculty ID', 
                required=False, 
                type=int
            ),
        ],
        responses={200: FamiliesListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='pre_approved_requests')
    def list_pre_approved_specialized(self, request):
        queryset = Families.objects.filter(
            type='نوعية',
            status='موافقة مبدئية'
        )
        faculty_id = request.query_params.get('faculty')
        if faculty_id:
            queryset = queryset.filter(faculty_id=faculty_id)
        queryset = queryset.order_by('-created_at')
        return Response(FamiliesListSerializer(queryset, many=True).data)