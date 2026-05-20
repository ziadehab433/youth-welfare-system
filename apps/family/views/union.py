import logging
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from apps.accounts.permissions import IsRole, require_permission
from apps.accounts.utils import get_current_admin
from apps.family.models import Families, FamilyAdmins
from apps.accounts.models import Students
from apps.solidarity.models import Departments, Faculties
from apps.family.serializers import (
    CreateUnionSerializer,
    UpdateUnionSerializer,
    UnionListSerializer,
    UnionDetailSerializer
)

logger = logging.getLogger(__name__)

UNION_TYPE = 'اتحاد'


@extend_schema(tags=["Union Management APIs"])
class UnionViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing Unions (اتحاد)
    - GET: Available to all admins
    - POST/PATCH: Limited to faculty admin and department manager
    """
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية', 'مدير ادارة', 'مشرف النظام']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUnionSerializer
        elif self.action == 'partial_update':
            return UpdateUnionSerializer
        elif self.action == 'retrieve':
            return UnionDetailSerializer
        return UnionListSerializer
    
    def get_queryset(self):
        """Get unions based on admin role"""
        admin = get_current_admin(self.request)
        queryset = Families.objects.filter(type=UNION_TYPE).order_by('-created_at')
        
        if admin.role == 'مسؤول كلية':
            # Faculty admin sees only their faculty's unions
            return queryset.filter(faculty_id=admin.faculty_id)
        elif admin.role == 'مدير ادارة':
            # Department manager sees all unions (like system admin)
            return queryset
        elif admin.role == 'مشرف النظام':
            # System admin sees all unions
            return queryset
        
        return queryset.none()
    
    @extend_schema(
        description="List all unions accessible to the current admin",
        responses={200: UnionListSerializer(many=True)}
    )
    def list(self, request):
        """List unions"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Get detailed information about a specific union",
        responses={200: UnionDetailSerializer}
    )
    def retrieve(self, request, pk=None):
        """Get union details"""
        try:
            union = self.get_queryset().get(family_id=pk)
        except Families.DoesNotExist:
            raise NotFound(f"Union with id {pk} not found")
        
        serializer = self.get_serializer(union)
        return Response(serializer.data)
    
    @extend_schema(
        description="Create a new union. Only faculty admins and department managers can create.",
        request=CreateUnionSerializer,
        responses={
            201: UnionDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    @require_permission('create')
    def create(self, request):
        """Create a new union"""
        admin = get_current_admin(request)
        
        # Permission check: only مسؤول كلية and مدير ادارة
        if admin.role not in ['مسؤول كلية', 'مدير ادارة']:
            raise PermissionDenied("Only faculty admins and department managers can create unions")
        
        # Deserialize and validate request body
        serializer = CreateUnionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Determine faculty_id
        faculty_id = serializer.validated_data.get('faculty_id')
        
        if admin.role == 'مسؤول كلية':
            # Faculty admin: use their faculty or the provided one
            if faculty_id is None:
                faculty_id = admin.faculty_id
            elif faculty_id != admin.faculty_id:
                raise PermissionDenied("Faculty admins can only create unions for their own faculty")
        elif admin.role == 'مدير ادارة':
            # Department manager: must create global unions (faculty_id = NULL)
            if faculty_id is not None:
                raise PermissionDenied("Department managers can only create global unions (without faculty)")
            faculty_id = None
        
        try:
            with transaction.atomic():
                # Create the union family
                union = Families.objects.create(
                    name=serializer.validated_data['name'],
                    description=serializer.validated_data['description'],
                    faculty_id=faculty_id,
                    type=UNION_TYPE,
                    status='مقبول',
                    min_limit=16,  # 16 persons for union
                    created_by=admin
                )
                
                # Create president
                president = serializer.validated_data['president']
                FamilyAdmins.objects.create(
                    family=union,
                    name=president.name,
                    nid=president.nid,
                    ph_no=president.phone_number if hasattr(president, 'phone_number') else '',
                    role='رئيس اتحاد'
                )
                
                # Create vice president
                vice_president = serializer.validated_data['vice_president']
                FamilyAdmins.objects.create(
                    family=union,
                    name=vice_president.name,
                    nid=vice_president.nid,
                    ph_no=vice_president.phone_number if hasattr(vice_president, 'phone_number') else '',
                    role='نائب رئيس اتحاد'
                )
                
                # Create committee heads and assistants
                for committee in serializer.validated_data['committees']:
                    # Create committee head
                    head_student = Students.objects.get(uid=committee['head']['uid'])
                    dept = Departments.objects.get(dept_id=committee['head']['dept_id'])
                    
                    FamilyAdmins.objects.create(
                        family=union,
                        name=head_student.name,
                        nid=head_student.nid,
                        ph_no=head_student.phone_number if hasattr(head_student, 'phone_number') else '',
                        role='أمين لجنة',
                        dept=dept
                    )
                    
                    # Create committee assistant
                    assistant_student = Students.objects.get(uid=committee['assistant']['uid'])
                    
                    FamilyAdmins.objects.create(
                        family=union,
                        name=assistant_student.name,
                        nid=assistant_student.nid,
                        ph_no=assistant_student.phone_number if hasattr(assistant_student, 'phone_number') else '',
                        role='أمين مساعد لجنة',
                        dept=dept
                    )
                
                logger.info(f"Union '{union.name}' created by {admin.name}")
        
        except Exception as e:
            logger.error(f"Error creating union: {str(e)}")
            raise ValidationError(f"Error creating union: {str(e)}")
        
        response_serializer = UnionDetailSerializer(union)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        description="Update a union. Only faculty admins and department managers can update.",
        request=UpdateUnionSerializer,
        responses={
            200: UnionDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Union not found")
        }
    )
    @require_permission('update')
    def partial_update(self, request, pk=None):
        """Update a union"""
        admin = get_current_admin(request)
        
        # Permission check: only مسؤول كلية and مدير ادارة
        if admin.role not in ['مسؤول كلية', 'مدير ادارة']:
            raise PermissionDenied("Only faculty admins and department managers can update unions")
        
        # Get union
        try:
            union = self.get_queryset().get(family_id=pk)
        except Families.DoesNotExist:
            raise NotFound(f"Union with id {pk} not found")
        
        # Deserialize and validate request body
        serializer = UpdateUnionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                # Update basic fields
                if 'name' in serializer.validated_data:
                    union.name = serializer.validated_data['name']
                if 'description' in serializer.validated_data:
                    union.description = serializer.validated_data['description']
                
                union.updated_at = timezone.now()
                union.save()
                
                # Update president if provided
                if 'president' in serializer.validated_data:
                    president = serializer.validated_data['president']
                    FamilyAdmins.objects.filter(
                        family=union,
                        role='رئيس اتحاد'
                    ).update(
                        name=president.name,
                        nid=president.nid,
                        ph_no=president.phone_number if hasattr(president, 'phone_number') else ''
                    )
                
                # Update vice president if provided
                if 'vice_president' in serializer.validated_data:
                    vice_president = serializer.validated_data['vice_president']
                    FamilyAdmins.objects.filter(
                        family=union,
                        role='نائب رئيس اتحاد'
                    ).update(
                        name=vice_president.name,
                        nid=vice_president.nid,
                        ph_no=vice_president.phone_number if hasattr(vice_president, 'phone_number') else ''
                    )
                
                # Update committees if provided
                if 'committees' in serializer.validated_data and serializer.validated_data['committees']:
                    # Delete existing committee members
                    FamilyAdmins.objects.filter(
                        family=union,
                        role__in=['أمين لجنة', 'أمين مساعد لجنة']
                    ).delete()
                    
                    # Create new committee members
                    for committee in serializer.validated_data['committees']:
                        # Create committee head
                        head_student = Students.objects.get(uid=committee['head']['uid'])
                        dept = Departments.objects.get(dept_id=committee['head']['dept_id'])
                        
                        FamilyAdmins.objects.create(
                            family=union,
                            name=head_student.name,
                            nid=head_student.nid,
                            ph_no=head_student.phone_number if hasattr(head_student, 'phone_number') else '',
                            role='أمين لجنة',
                            dept=dept
                        )
                        
                        # Create committee assistant
                        assistant_student = Students.objects.get(uid=committee['assistant']['uid'])
                        
                        FamilyAdmins.objects.create(
                            family=union,
                            name=assistant_student.name,
                            nid=assistant_student.nid,
                            ph_no=assistant_student.phone_number if hasattr(assistant_student, 'phone_number') else '',
                            role='أمين مساعد لجنة',
                            dept=dept
                        )
                
                logger.info(f"Union '{union.name}' updated by {admin.name}")
        
        except Exception as e:
            logger.error(f"Error updating union: {str(e)}")
            raise ValidationError(f"Error updating union: {str(e)}")
        
        response_serializer = UnionDetailSerializer(union)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
