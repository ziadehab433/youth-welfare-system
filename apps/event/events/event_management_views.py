from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.db import transaction
from apps.event.models import Events
from .serializers import EventCreateUpdateSerializer, EventListSerializer, EventDetailSerializer
from apps.accounts.models import AdminsUser
from apps.accounts.permissions import require_permission, IsRole
from apps.accounts.utils import (
    get_current_admin,
    get_client_ip,
    get_current_student,
    log_data_access
)
from django.db.models import Q

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.db import transaction
from apps.event.models import Events
from .serializers import EventCreateUpdateSerializer, EventListSerializer, EventDetailSerializer
from apps.accounts.models import AdminsUser
from apps.accounts.permissions import require_permission, IsRole
from apps.accounts.utils import (
    get_current_admin,
    get_client_ip,
    get_current_student,
    log_data_access
)
from django.db.models import Q

# faculty admins & department managers 
@extend_schema(tags=["Event Management APIs"])
class EventGetterViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية', 'مدير ادارة', 'مدير عام', 'مدير كلية']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return EventCreateUpdateSerializer
        elif self.action == 'retrieve':
            return EventDetailSerializer
        return EventListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        admin = get_current_admin(self.request)
        
        queryset = Events.objects.select_related(
            'created_by', 'faculty', 'dept', 'family'
        ).filter(family__isnull=True) 
        
        if admin.role == 'مسؤول كلية' or admin.role == 'مدير كلية':
            return queryset.filter(
                Q(faculty_id=admin.faculty_id) | Q(faculty_id__isnull=True)
            ).order_by('-created_at')
        elif admin.role == 'مدير عام':
            return queryset.filter(faculty_id__isnull=True)
        else: 
            return queryset.filter(faculty_id__isnull=True, dept_id=admin.dept_id)
        
        return queryset.none() 

    def get_object(self):
        queryset = self.get_queryset()
        
        obj = queryset.filter(pk=self.kwargs['pk']).first()
        
        if obj is None:
            raise PermissionDenied("You don't have permission to access this event")
        
        return obj

    @extend_schema(
        description="List all events in the admin's faculty",
        responses={200: EventListSerializer(many=True)}
    )
    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Get event details",
        responses={200: EventDetailSerializer}
    )
    def retrieve(self, request, pk=None):
        event = self.get_object()
        serializer = self.get_serializer(event)
        return Response(serializer.data)

    @extend_schema(
        description="Get events for department manager filtered by faculty_id",
        responses={200: EventListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path=r'faculty/(?P<faculty_id>\d+)')
    def get_events_by_faculty(self, request, faculty_id=None):
        admin = get_current_admin(request)
        faculty_id = int(faculty_id)
        
        if admin.role != 'مدير ادارة':
            raise PermissionDenied("ليس لديك صلاحية الوصول لهذا المورد")
        
        queryset = Events.objects.select_related(
            'created_by', 'faculty', 'dept', 'family'
        ).filter(
            family__isnull=True,
            dept_id=admin.dept_id, 
            faculty=faculty_id  
        ).order_by('-created_at')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# faculty admins & department managers 
@extend_schema(tags=["Event Management APIs"])
class EventManagementViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية', 'مدير ادارة']

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return EventCreateUpdateSerializer
        elif self.action == 'retrieve':
            return EventDetailSerializer
        return EventListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_object(self):
        obj = super().get_object()
        admin = get_current_admin(self.request)
        
        if admin.role == 'مدير ادارة':
            if obj.faculty_id is not None:
                raise PermissionDenied("You don't have permission to access this event")
        else:
            if obj.faculty_id != admin.faculty_id:
                raise PermissionDenied("You don't have permission to access this event")
    
        return obj

    def get_queryset(self):
        admin = get_current_admin(self.request)
        
        queryset = Events.objects.select_related(
            'created_by', 'faculty', 'dept', 'family'
        ).order_by('-created_at')
        
        if admin.role == 'مدير ادارة':
            return queryset.filter(faculty_id__isnull=True)
        else:
            return queryset.filter(faculty_id=admin.faculty_id)


    @extend_schema(
        description="Create a new event",
        request=EventCreateUpdateSerializer,
        responses={201: EventDetailSerializer},
    )
    def create(self, request):
        admin = get_current_admin(request)
        ip = get_client_ip(request)
        
        if admin.role == 'مسؤول كلية' and 'selected_facs' in request.data:
            raise PermissionDenied("Faculty admins cannot use the selected_facs field")
        
        if admin.role == 'مدير ادارة' and 'dept' in request.data:
            requested_dept_id = request.data.get('dept')
            if requested_dept_id != admin.dept_id:
                raise PermissionDenied(
                    f"You can only create events in your own department (ID: {admin.dept_id}). "
                    f"Requested department ID: {requested_dept_id}"
                )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            create_kwargs = {
                'created_by': admin,
            }
            
            if admin.role == 'مدير ادارة':
                create_kwargs['faculty_id'] = None
                create_kwargs['dept_id'] = admin.dept_id
            else:
                create_kwargs['faculty_id'] = admin.faculty_id
            
            event = serializer.save(**create_kwargs)
            
            log_data_access(
                actor_id=admin.admin_id,
                actor_type=admin.role,
                action=f"Created event: {event.title}",
                target_type='نشاط',
                event_id=event.event_id,
                ip_address=ip
            )
        
        detail_serializer = EventDetailSerializer(event)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        description="Partially update an event",
        request=EventCreateUpdateSerializer,
        responses={200: EventDetailSerializer},
    )
    def partial_update(self, request, pk=None):
        admin = get_current_admin(request)
        ip = get_client_ip(request)
        
        event = self.get_object()
        
        if admin.role == 'مسؤول كلية' and 'selected_facs' in request.data:
            raise PermissionDenied("Faculty admins cannot modify the selected_facs field")
        
        if 'faculty' in request.data:
            request.data.pop('faculty')
        
        if admin.role == 'مدير ادارة':
            if 'dept' in request.data:
                requested_dept_id = request.data.get('dept')
                if requested_dept_id != admin.dept_id:
                    raise PermissionDenied(
                        f"You can only update events in your own department (ID: {admin.dept_id}). "
                        f"Cannot change to department ID: {requested_dept_id}"
                    )
            
            if event.dept_id != admin.dept_id:
                raise PermissionDenied(
                    f"You can only update events in your own department. "
                    f"This event belongs to department ID: {event.dept_id}"
                )
        
        serializer = self.get_serializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            updated_event = serializer.save()
            
            if admin.role == 'مدير ادارة':
                if updated_event.faculty_id is not None:
                    updated_event.faculty_id = None
                    updated_event.save(update_fields=['faculty_id'])
                
                if updated_event.dept_id != admin.dept_id:
                    updated_event.dept_id = admin.dept_id
                    updated_event.save(update_fields=['dept_id'])
            
            log_data_access(
                actor_id=admin.admin_id,
                actor_type=admin.role,
                action=f"Updated event: {event.title}",
                target_type='نشاط',
                event_id=event.event_id,
                ip_address=ip
            )
        
        detail_serializer = EventDetailSerializer(updated_event)
        return Response(detail_serializer.data)

# faculty head & general admin
@extend_schema(tags=["Event Management APIs"])
class EventARViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مدير عام', 'مدير كلية']
    serializer_class = EventDetailSerializer

    def get_object(self):
        """Override get_object to add faculty validation for faculty admins only"""
        obj = super().get_object()
        admin = get_current_admin(self.request)
        
        if admin.role == 'مدير عام':
            if obj.faculty_id is not None:
                raise PermissionDenied("You don't have permission to access this event")
        else:
            if obj.faculty_id != admin.faculty_id:
                raise PermissionDenied("You don't have permission to access this event")
    
        return obj

    def get_queryset(self):
        admin = get_current_admin(self.request)
        
        queryset = Events.objects.select_related(
            'created_by', 'faculty', 'dept', 'family'
        ).order_by('-created_at')
        
        if admin.role == 'مدير عام':
            return queryset.filter(faculty_id__isnull=True)
        else:
            return queryset.filter(faculty_id=admin.faculty_id)

    @extend_schema(
        description="Approve an event (update status to 'مقبول')",
        request=None,  
        responses={
            200: OpenApiResponse(response=EventDetailSerializer, description="Event approved successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Event not found")
        }
    )
    @action(detail=True, methods=['patch'], url_path='approve')
    def approve_event(self, request, pk=None):
        """
        Approve an event by updating its status to 'مقبول'
        Only accessible by faculty heads and general admins
        """
        admin = get_current_admin(request)
        ip = get_client_ip(request)
        
        event = self.get_object()
        
        if event.status == 'مقبول':
            return Response(
                {"detail": "Event is already approved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            event.status = 'مقبول'
            event.save(update_fields=['status'])
            
            log_data_access(
                actor_id=admin.admin_id,
                actor_type=admin.role,
                action=f"Approved event: {event.title}",
                target_type='نشاط',
                event_id=event.event_id,
                ip_address=ip
            )
        
        serializer = EventDetailSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Reject an event (update status to 'مرفوض')",
        request=None,
        responses={
            200: OpenApiResponse(response=EventDetailSerializer, description="Event rejected successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Event not found")
        }
    )
    @action(detail=True, methods=['patch'], url_path='reject')
    def reject_event(self, request, pk=None):
        """
        Reject an event by updating its status to 'مرفوض'
        Only accessible by faculty heads and general admins
        """
        admin = get_current_admin(request)
        ip = get_client_ip(request)
        
        event = self.get_object() 
        
        if event.status == 'مرفوض':
            return Response(
                {"detail": "Event is already rejected"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            event.status = 'مرفوض'
            event.save(update_fields=['status'])
            
            log_data_access(
                actor_id=admin.admin_id,
                actor_type=admin.role,
                action=f"Rejected event: {event.title}",
                target_type='نشاط',
                event_id=event.event_id,
                ip_address=ip
            )
        
        serializer = EventDetailSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)


# faculty admins activating an event from a plan 
@extend_schema(tags=["Event Management APIs"])
class EventActivationViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية']
    serializer_class = EventCreateUpdateSerializer

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'activate_event':
            return EventCreateUpdateSerializer
        return EventDetailSerializer

    def get_serializer_context(self):
        """Add request to serializer context for role-based field access"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_object(self):
        """Override get_object to add faculty validation for faculty admins only"""
        obj = super().get_object()
        admin = get_current_admin(self.request)
        
        if admin.role == 'مدير ادارة':
            if obj.faculty_id is not None:
                raise PermissionDenied("You don't have permission to access this event")
        else:
            if obj.faculty_id != admin.faculty_id:
                raise PermissionDenied("You don't have permission to access this event")
    
        return obj

    def get_queryset(self):
        admin = get_current_admin(self.request)
        
        queryset = Events.objects.select_related(
            'created_by', 'faculty', 'dept', 'family'
        ).order_by('-created_at')
        
        if admin.role == 'مدير ادارة':
            return queryset.filter(faculty_id__isnull=True)
        else:
            return queryset.filter(faculty_id=admin.faculty_id)

    @extend_schema(
        description="Partially update an event and activate it (set active=True)",
        request=EventCreateUpdateSerializer,
        responses={200: EventDetailSerializer},
    )
    @action(detail=True, methods=['patch'], url_path='activate')
    def activate_event(self, request, pk=None):
        """
        Partially update an event and activate it by setting active to True
        """
        admin = get_current_admin(request)
        ip = get_client_ip(request)
        
        event = self.get_object()
        
        if admin.role == 'مسؤول كلية' and 'selected_facs' in request.data:
            raise PermissionDenied("Faculty admins cannot modify the selected_facs field")
        
        if 'faculty' in request.data:
            request.data.pop('faculty')
        
        serializer = self.get_serializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            updated_event = serializer.save()
            
            updated_event.active = True
            updated_event.save(update_fields=['active'])
            
            if admin.role == 'مدير ادارة' and updated_event.faculty_id is not None:
                updated_event.faculty_id = None
                updated_event.save(update_fields=['faculty_id'])
            
            log_data_access(
                actor_id=admin.admin_id,
                actor_type=admin.role,
                action=f"Activated event: {event.title}",
                target_type='نشاط',
                event_id=event.event_id,
                ip_address=ip
            )
        
        detail_serializer = EventDetailSerializer(updated_event)
        return Response(detail_serializer.data)