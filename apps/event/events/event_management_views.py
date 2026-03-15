from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from apps.event.models import Events, Prtcps, EventDocs, Plans
from .serializers import (
    EventCreateUpdateSerializer, 
    EventListSerializer, 
    EventDetailSerializer,
    EventImageUploadSerializer,
    EventDocsSerializer
)
from apps.accounts.models import AdminsUser
from apps.accounts.permissions import require_permission, IsRole
from apps.accounts.utils import (
    get_current_admin,
    get_client_ip,
    get_current_student,
    log_data_access,
    get_current_user_token_payload
)
from apps.accounts.mixins import AdminActionMixin
from django.db.models import Q, Prefetch

# faculty admins & department managers 
@extend_schema(tags=["Event Management APIs"])
class EventGetterViewSet(AdminActionMixin, viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية', 'مدير ادارة', 'مدير عام', 'مدير كلية', 'مشرف النظام']

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

    def get_queryset(self, queryset=None):
        admin = get_current_admin(self.request)
        admin_payload = get_current_user_token_payload(self.request)
        
        if queryset is None: 
            queryset = Events.objects.select_related(
                'created_by', 'faculty', 'dept', 'family'
            ).filter(family__isnull=True).exclude(status='ملغي')
        
        if admin.role == 'مسؤول كلية':
            return queryset.filter(
                Q(faculty_id=admin.faculty_id) | Q(faculty_id__isnull=True),
                dept_id__in=admin_payload.get('dept_ids', [])
            ).order_by('-created_at')
        elif admin.role == 'مدير كلية':
            return queryset.filter(faculty_id=admin.faculty_id).order_by('-created_at').exclude(status="منتظر")
        elif admin.role == 'مدير عام':
            return queryset.filter(faculty_id__isnull=True).exclude(status="منتظر")
        elif admin.role == 'مشرف النظام': 
            return queryset
        elif admin.role == 'مدير ادارة': 
            return queryset.filter(dept_id=admin.dept_id)
        
        return queryset.none() 

    def get_object(self):
        """
        Custom get_object that:
        1. Fetches event directly by pk
        2. For destroy action, allows event creator full access
        3. For other actions, applies role-based filtering
        """
        admin = get_current_admin(self.request)
        event = get_object_or_404(
            Events.objects.select_related('created_by', 'faculty', 'dept', 'family')
            .filter(family__isnull=True)
            .exclude(status='ملغي')
            .prefetch_related(
                Prefetch(
                    'prtcps_set',
                    queryset=Prtcps.objects.select_related('student'),
                    to_attr='participants'
                )
            ),
            pk=self.kwargs['pk']
        )
        
        # For destroy action, if admin is the event creator, allow access immediately
        if self.action == 'destroy':
            if event.created_by and event.created_by.admin_id == admin.admin_id:
                return event
        
        # Apply role-based filtering for all actions
        if admin.role == 'مسؤول كلية':
            if event.faculty_id == admin.faculty_id or event.faculty_id is None:
                return event
        elif admin.role == 'مدير كلية':
            if event.faculty_id == admin.faculty_id and event.status != "منتظر":
                return event
        elif admin.role == 'مدير عام':
            if event.faculty_id is None and event.status != "منتظر":
                return event
        elif admin.role == 'مشرف النظام':
            return event
        elif admin.role == 'مدير ادارة':
            if event.dept_id == admin.dept_id:
                return event
        
        raise PermissionDenied("You don't have permission to access this event")

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
    @action(detail=False, methods=['get'], url_path=r'faculty')
    def get_events_by_faculty(self, request, faculty_id=None):
        admin = get_current_admin(request)
        
        if admin.role != 'مدير ادارة':
            raise PermissionDenied("ليس لديك صلاحية الوصول لهذا المورد")
        
        queryset = Events.objects.select_related(
            'created_by', 'faculty', 'dept', 'family'
        ).filter(
            family__isnull=True,
            dept_id=admin.dept_id, 
            faculty__isnull=False  
        ).order_by('-created_at')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="delete an event",
        responses={200: EventDetailSerializer}
    )
    def destroy(self, request, pk=None):
        event = self.get_object()
        admin = get_current_admin(request)
        
        # Authorization check: only the creator can delete
        if event.created_by.admin_id != admin.admin_id:
            raise PermissionDenied("لا يمكنك التعديل أو الحذف على نشاط لم تقم بإنشائه")
        
        if admin.role == 'مدير ادارة':
            if event.dept_id != admin.dept_id and event.faculty_id is not None:
                raise PermissionDenied("لا يمكنك حذف فعاليات من إدارة أخرى")
        elif admin.role == 'مسؤول كلية':
            if event.faculty_id and event.faculty_id != admin.faculty_id:
                raise PermissionDenied("لا يمكنك حذف فعاليات من كلية أخرى")
        
        def business_operation(admin, ip):
            event.active = False
            event.status = 'ملغي'
            event.save()
            return {
                "detail": "تم إلغاء الفعالية بنجاح",
                "event_id": event.event_id,
                "title": event.title,
                "status": event.status,
                "active": event.active
            }
        
        result = self.execute_admin_action(
            request=request,
            action_name=f"حذف نشاط: {event.title}",
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id
        )
        
        return Response(result, status=status.HTTP_200_OK)

# faculty admins & department managers 
@extend_schema(tags=["Event Management APIs"])
class EventManagementViewSet(AdminActionMixin, viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية', 'مدير ادارة']
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return EventCreateUpdateSerializer
        elif self.action == 'retrieve':
            return EventDetailSerializer
        elif self.action == 'upload_images':
            return EventImageUploadSerializer
        elif self.action in ['get_images', 'delete_image']:
            return EventDocsSerializer
        return EventListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_object(self):
        """
        Custom get_object that:
        1. Fetches event directly by pk (no role-based queryset filtering)
        2. Allows event creator full access
        3. For read-only actions, applies same view permissions as EventGetterViewSet
        4. For write actions, only allows creator
        """
        admin = get_current_admin(self.request)
        event = get_object_or_404(
            Events.objects.select_related('created_by', 'faculty', 'dept', 'family'),
            pk=self.kwargs['pk']
        )
        
        # If admin is the event creator, allow access immediately
        if event.created_by and event.created_by.admin_id == admin.admin_id:
            return event
        
        # For read-only actions like get_images, apply same view permissions as EventGetterViewSet
        read_only_actions = ['get_images']
        if self.action in read_only_actions:
            # Apply role-based view permissions
            if admin.role == 'مسؤول كلية':
                if event.faculty_id == admin.faculty_id or event.faculty_id is None:
                    return event
            elif admin.role == 'مدير كلية':
                if event.faculty_id == admin.faculty_id:
                    return event
            elif admin.role == 'مدير عام':
                if event.faculty_id is None:
                    return event
            elif admin.role == 'مدير ادارة':
                if event.dept_id == admin.dept_id:
                    return event
            elif admin.role == 'مشرف النظام':
                return event
            
            raise PermissionDenied("You don't have permission to access this event")
        
        # For write actions (partial_update, upload_images, delete_image)
        # Only the creator can perform these actions (already checked above)
        write_actions = ['partial_update', 'update', 'upload_images', 'delete_image']
        if self.action in write_actions:
            raise PermissionDenied("لا يمكنك التعديل أو الحذف على نشاط لم تقم بإنشائه")
        
        # Default fallback: apply original role-based check
        if admin.role == 'مدير ادارة':
            if event.faculty_id is not None:
                raise PermissionDenied("You don't have permission to access this event")
        else:
            if event.faculty_id != admin.faculty_id:
                raise PermissionDenied("You don't have permission to access this event")
        
        return event

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
        admin_payload = get_current_user_token_payload(request)
        
        if admin.role == 'مسؤول كلية':
            if 'selected_facs' in request.data and request.data.get('selected_facs'):
                raise PermissionDenied("Faculty admins cannot use the selected_facs field")
            
            requested_dept_id = request.data.get('dept')
            if not requested_dept_id:
                raise PermissionDenied("Faculty admins must specify a department (dept field)")
            
            dept_ids = admin_payload.get('dept_ids', [])
            
            if requested_dept_id not in dept_ids:
                raise PermissionDenied(
                    f"You can only create events in departments you manage. "
                    f"Your managed departments: {dept_ids}. "
                )
        
        elif admin.role == 'مدير ادارة':
            requested_dept_id = request.data.get('dept')
            if requested_dept_id != admin.dept_id:
                raise PermissionDenied(
                    f"You can only create events in your own department (ID: {admin.dept_id}). "
                    f"Requested department ID: {requested_dept_id}"
                )

        requested_plan_id = request.data.get('plan')
        if requested_plan_id:
            try: 
                plan = Plans.objects.get(plan_id=requested_plan_id)
                if admin.role == 'مدير ادارة' and plan.faculty is not None:
                    return Response(
                        {"detail": "you can only edit global plans"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                elif admin.role == 'مسؤول كلية':
                    if plan.faculty is None or plan.faculty.faculty_id != admin.faculty_id:
                        return Response(
                            {"detail": "you can only edit plans from your faculty"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except Plans.DoesNotExist:
                return Response(
                    {"detail": "Plan you selected doesnt exist"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        def business_operation(admin, ip):
            create_kwargs = {
                'created_by': admin,
            }
            
            if admin.role == 'مدير ادارة':
                create_kwargs['faculty_id'] = None
                create_kwargs['dept_id'] = admin.dept_id
            else:
                create_kwargs['faculty_id'] = admin.faculty_id
                create_kwargs['dept_id'] = request.data.get('dept')
            
            event = serializer.save(**create_kwargs)
            return event
        
        event = self.execute_admin_action(
            request=request,
            action_name=f"إنشاء نشاط",
            target_type='نشاط',
            business_operation=business_operation,
            event_id=None
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
        admin_payload = get_current_user_token_payload(request)
        
        event = self.get_object()
        
        # Authorization check: only the creator can update
        if event.created_by.admin_id != admin.admin_id:
            raise PermissionDenied("لا يمكنك التعديل أو الحذف على نشاط لم تقم بإنشائه")
        
        if admin.role == 'مسؤول كلية':
            if 'selected_facs' in request.data and request.data.get('selected_facs'):
                raise PermissionDenied("Faculty admins cannot use the selected_facs field")
            
            requested_dept_id = request.data.get('dept')
            if not requested_dept_id:
                raise PermissionDenied("Faculty admins must specify a department (dept field)")
            
            dept_ids = admin_payload.get('dept_ids', [])
            
            if requested_dept_id not in dept_ids or event.dept_id not in dept_ids:
                raise PermissionDenied(
                    f"You can only update events in departments you manage. "
                    f"Your managed departments: {dept_ids}. "
                )
        
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
        
        if event.plan:
            if admin.role == 'مسؤول كلية':
                if event.plan.faculty is None or event.plan.faculty.faculty_id != admin.faculty_id:
                    return Response(
                        {"detail": "You can only update events with plans from your faculty"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            elif admin.role == 'مدير ادارة':
                if event.plan.faculty is not None:
                    return Response(
                        {"detail": "You can only update events with global plans"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        requested_plan_id = request.data.get('plan')
        if requested_plan_id:
            try: 
                plan = Plans.objects.get(plan_id=requested_plan_id)
                if admin.role == 'مدير ادارة' and plan.faculty is not None:
                    return Response(
                        {"detail": "you can only edit global plans"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                elif admin.role == 'مسؤول كلية':
                    if plan.faculty is None or plan.faculty.faculty_id != admin.faculty_id:
                        return Response(
                            {"detail": "you can only edit plans from your faculty"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except Plans.DoesNotExist:
                return Response(
                    {"detail": "Plan you selected doesnt exist"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        def business_operation(admin, ip):
            updated_event = serializer.save()
            
            if admin.role == 'مدير ادارة':
                if updated_event.faculty_id is not None:
                    updated_event.faculty_id = None
                    updated_event.save(update_fields=['faculty_id'])
                
                if updated_event.dept_id != admin.dept_id:
                    updated_event.dept_id = admin.dept_id
                    updated_event.save(update_fields=['dept_id'])
            
            return updated_event
        
        updated_event = self.execute_admin_action(
            request=request,
            action_name=f"تحديث نشاط: {event.title}",
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id
        )
        
        detail_serializer = EventDetailSerializer(updated_event)
        return Response(detail_serializer.data)

    @extend_schema(
        description="Upload images for an event (only event creator)",
        request=EventImageUploadSerializer,
        responses={
            201: EventDocsSerializer(many=True),
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Permission denied - only event creator can upload"),
        }
    )
    @action(detail=True, methods=['post'], url_path='upload-images')
    @require_permission('create')
    def upload_images(self, request, pk=None):
        """
        Upload one or multiple images for an event
        Only the event creator can upload images
        """
        admin = get_current_admin(request)
        
        # Get event and verify permissions
        event = self.get_object()
        
        # Check if current admin is the event creator
        if event.created_by_id != admin.admin_id:
            raise PermissionDenied("Only the event creator can upload images for this event")
        
        # Validate uploaded files
        serializer = EventImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        images = serializer.validated_data['images']
        doc_type = serializer.validated_data.get('doc_type', 'event_image')
        
        def business_operation(admin, ip):
            uploaded_docs = []
            for image_file in images:
                # Generate file path
                import os
                from django.core.files.storage import default_storage
                
                # Create directory path
                upload_dir = f"uploads/events/{event.event_id}"
                file_path = os.path.join(upload_dir, image_file.name)
                
                # Save file using Django's storage system
                saved_path = default_storage.save(file_path, image_file)
                
                # Create database record
                doc = EventDocs.objects.create(
                    event=event,
                    doc_type=doc_type,
                    file_name=image_file.name,
                    file_path=saved_path,
                    mime_type=image_file.content_type,
                    file_size=image_file.size,
                    uploaded_at=timezone.now(),
                    uploaded_by=admin
                )
                uploaded_docs.append(doc)
            return uploaded_docs
        
        uploaded_docs = self.execute_admin_action(
            request=request,
            action_name=f"رفع {len(images)} صورة للنشاط: {event.title}",
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id
        )
        
        response_serializer = EventDocsSerializer(
            uploaded_docs, 
            many=True, 
            context={'request': request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        description="Get all images for an event",
        responses={200: EventDocsSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='images')
    @require_permission('read')
    def get_images(self, request, pk=None):
        """
        Retrieve all uploaded images for a specific event
        """
        event = self.get_object()
        docs = event.event_docs.all()
        
        def business_operation(admin, ip):
            return docs
        
        docs = self.execute_admin_action(
            request=request,
            action_name=f"عرض صور النشاط: {event.title}",
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id
        )
        
        serializer = EventDocsSerializer(docs, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        description="Delete a specific image from an event (only event creator)",
        responses={
            204: OpenApiResponse(description="Image deleted successfully"),
            403: OpenApiResponse(description="Permission denied - only event creator can delete"),
            404: OpenApiResponse(description="Image not found"),
        }
    )
    @action(detail=True, methods=['delete'], url_path='images/(?P<doc_id>[^/.]+)')
    @require_permission('delete')
    def delete_image(self, request, pk=None, doc_id=None):
        """
        Delete a specific image from an event
        Only the event creator can delete images
        """
        admin = get_current_admin(request)
        
        event = self.get_object()
        
        # Check if current admin is the event creator
        if event.created_by_id != admin.admin_id:
            raise PermissionDenied("Only the event creator can delete images for this event")
        
        try:
            doc = EventDocs.objects.get(doc_id=doc_id, event=event)
        except EventDocs.DoesNotExist:
            return Response(
                {"detail": "Image not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        def business_operation(admin, ip):
            # Delete the file from storage
            from django.core.files.storage import default_storage
            if doc.file_path:
                try:
                    default_storage.delete(doc.file_path)
                except Exception as e:
                    # Log but don't fail if file doesn't exist
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not delete file {doc.file_path}: {str(e)}")
            
            doc.delete()
            return None
        
        self.execute_admin_action(
            request=request,
            action_name=f"حذف صورة رقم {doc_id} من النشاط: {event.title}",
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)

# faculty head & general admin
@extend_schema(tags=["Event Management APIs"])
class EventARViewSet(AdminActionMixin, viewsets.GenericViewSet):
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
        event = self.get_object()

        if event.status == 'مقبول':
            return Response(
                {"detail": "Event is already approved"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if event.status != 'موافقة مبدئية': 
            return Response( 
                {"detail": "Event is not in 'موافقة مبدئية' status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        def business_operation(admin, ip):
            event.status = 'مقبول'
            event.save(update_fields=['status'])
            return event
        
        event = self.execute_admin_action(
            request=request,
            action_name=f"الموافقة على نشاط: {event.title}",
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id
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
        event = self.get_object() 

        if event.status == 'مرفوض':
            return Response(
                {"detail": "Event is already rejected"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if event.status != 'موافقة مبدئية': 
            return Response( 
                {"detail": "Event is not in 'موافقة مبدئية' status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        def business_operation(admin, ip):
            event.status = 'مرفوض'
            event.save(update_fields=['status'])
            return event
        
        event = self.execute_admin_action(
            request=request,
            action_name=f"رفض نشاط: {event.title}",
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id
        )
        
        serializer = EventDetailSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)


# faculty admins activating an event from a plan 
@extend_schema(tags=["Event Management APIs"])
class EventActivationViewSet(AdminActionMixin, viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية','مدير ادارة']
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
        description="Toggle the active attribute for an event (no request body needed)",
        responses={200: EventDetailSerializer},
    )
    @action(detail=True, methods=['post'], url_path='activate')
    def activate_event(self, request, pk=None):
        event = self.get_object()
        
        if event.status != 'مقبول':
            return Response(
                {"detail": "Event can only be activated when it is accepted"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        def business_operation(admin, ip):
            event.active = not event.active
            event.save(update_fields=['active'])
            return event
        
        event = self.execute_admin_action(
            request=request,
            action_name=f"{'تفعيل' if event.active else 'إلغاء تفعيل'} نشاط: {event.title}",
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id
        )
        
        detail_serializer = EventDetailSerializer(event)
        return Response(detail_serializer.data)