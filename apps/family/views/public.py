# views.py

from rest_framework import viewsets
from apps.solidarity.models import Departments
from ..serializers import DepartmentSerializer
from drf_spectacular.utils import extend_schema

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Departments.objects.all()
    serializer_class = DepartmentSerializer

    @extend_schema(
        tags=["Public APIs"],
        description="List all departments with their ID and name.",
        responses={200: DepartmentSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)