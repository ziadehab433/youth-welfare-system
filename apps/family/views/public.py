from rest_framework import viewsets
from apps.family.serializers import DepartmentSerializer
from apps.solidarity.models import Departments, Faculties
from drf_spectacular.utils import extend_schema
from apps.solidarity.serializers import DeptFacultiesSerializer
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

class FacultyViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Faculties.objects.all()
    serializer_class = DeptFacultiesSerializer

    @extend_schema(
        tags=["Public APIs"],
        description="List all faculties with their ID and name.",
        responses={200: DeptFacultiesSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)