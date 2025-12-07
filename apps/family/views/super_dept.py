from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.family.models import Families
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import IsRole
from apps.family.serializers import (
    FamiliesListSerializer, 
    FamiliesDetailSerializer, 
    CentralFamilyCreateSerializer 
)

@extend_schema(tags=["Family Super_Dept"])  
class SuperDeptFamilyViewSet(viewsets.ModelViewSet):
    queryset = Families.objects.all()
    http_method_names = ['get', 'post']
    permission_classes = [IsAuthenticated, IsRole]   
    allowed_roles = ['مدير ادارة', 'مشرف النظام']
    def get_serializer_class(self):
        if self.action == 'create':
            return CentralFamilyCreateSerializer
        elif self.action == 'retrieve':
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
        description="Get families filtered by type and faculty ID.",
        parameters=[
            OpenApiParameter(name='type', description='Family Type', required=False, type=str),
            OpenApiParameter(name='faculty', description='Faculty ID', required=False, type=int),
        ],
        responses={200: FamiliesListSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        description="Create a new Central family (Type and Faculty are set automatically).",
        request=CentralFamilyCreateSerializer, 
        responses={201: CentralFamilyCreateSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user, 
            status='مقبول',    
            type='مركزية',       
            faculty=None,      
            min_limit=50        
        )