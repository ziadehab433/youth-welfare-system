from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse

from apps.family.models import Families
from apps.family.serializers import FamiliesListSerializer, FamiliesDetailSerializer
from apps.family.services.family_service import FamilyService
from apps.accounts.utils import get_current_admin, get_client_ip , log_data_access
from apps.accounts.permissions import IsRole, require_permission

from django.core.exceptions import ValidationError

class FamilyFacultyAdminViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية']  # Faculty Admin
    serializer_class = FamiliesListSerializer

    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="List all families for the current faculty",
        responses={200: FamiliesListSerializer(many=True)}
    )
    # GET/api/family/family/families/
    @action(detail=False, methods=['get'], url_path='families')
    @require_permission('read')
    def list_families(self, request):
        """Get all families related to the faculty of current admin"""
        admin = get_current_admin(request)
        
        try:
            qs = FamilyService.get_families_for_faculty(admin)
            return Response(FamiliesListSerializer(qs, many=True).data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="Retrieve details of a specific family",
        responses={
            200: FamiliesDetailSerializer,
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not found")
        }
    )
    @action(detail=True, methods=['get'], url_path='families')
    @require_permission('read')
    #GET/api/family/family/{id}/families/
    def get_family(self, request, pk=None):
        """Get specific family details"""
        client_ip = get_client_ip(request)
        admin = get_current_admin(request)
        
        try:
            family = FamilyService.get_family_detail(pk, admin)
            
             #Optional: Log data access
            # log_data_access(
            #     actor_id=admin.admin_id,
            #     actor_type=admin.role,
            #     action='عرض تفاصيل الأسرة',
            #     target_type='اسر',
            #     family_id=pk,  # do not forget to fix the log_data_fun to be genaric to fit with all actions (osar , tkafol , events)
            #     ip_address=client_ip
            # )
            
            return Response(FamiliesDetailSerializer(family).data)
        except ValidationError as e:
            msg = str(e)
            if "does not belong" in msg:
                return Response({'error': msg}, status=status.HTTP_403_FORBIDDEN)
            elif "not found" in msg.lower():
                return Response({'error': msg}, status=status.HTTP_404_NOT_FOUND)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)