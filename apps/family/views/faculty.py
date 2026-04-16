import logging
from rest_framework import viewsets, status, serializers
from rest_framework.exceptions import ValidationError
from django.db.models import Count
from django.http import FileResponse
from django.utils import timezone 
from django.template.loader import render_to_string
from io import BytesIO
from django.db import DatabaseError, transaction
from apps.family.models import Students, FamilyAdmins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse
from apps.family.models import Families, FamilyMembers
from apps.family.services.family_service import FamilyService
from apps.event.models import Events
from apps.event.serializers import EventSerializer
from apps.accounts.permissions import IsRole, require_permission
from apps.accounts.utils import get_current_admin
from apps.accounts.mixins import AdminActionMixin
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from apps.event.models import Prtcps
from apps.event.export.utils import generate_pdf_sync
from apps.family.serializers import (
    EventDetailSerializer,
    FamiliesListSerializer,
    FamiliesDetailSerializer,
    FamilyRequestListSerializer,
    PreApproveFamilySerializer,
    FamilyFounderSerializer,
    CreateFamilyRequestSerializer,
    CreateEnvFamilyRequestSerializer,
    FamilyRequestDetailSerializer
)

logger = logging.getLogger(__name__)

# Status constants
STATUS_PENDING = 'منتظر'
STATUS_PRE_APPROVED = 'موافقة مبدئية'
STATUS_APPROVED = 'مقبول'
STATUS_REJECTED = 'مرفوض'

ROLE_MEMBER = 'عضو'
# ------------------------------------------------------------------
# Families (Faculty Admin)
# ------------------------------------------------------------------
@extend_schema(tags=["Family Fac Admin APIs"])
class FamilyFacultyAdminViewSet(AdminActionMixin, viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية']
    queryset = Families.objects.all()
    serializer_class = FamiliesListSerializer
    @extend_schema(
        description="List all approved families for the current faculty",
        responses={200: FamiliesListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='families')
    @require_permission('read')
    def list_families(self, request):
        admin = get_current_admin(request)
        families = FamilyService.get_families_for_faculty(admin)
        approved_families = families.filter(status=STATUS_APPROVED)
        return Response(FamiliesListSerializer(approved_families, many=True).data)
    @extend_schema(
        description="Retrieve details of a specific family",
        responses={200: FamiliesDetailSerializer}
    )
    @action(detail=True, methods=['get'], url_path='details')
    @require_permission('read')
    def get_family(self, request, pk=None):
        admin = get_current_admin(request)
        family = FamilyService.get_family_detail(pk, admin)
        return Response(FamiliesDetailSerializer(family).data)

    @extend_schema(
        description="Fetch ONLY pending family creation requests for the current faculty.",
        responses={200: FamilyRequestListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='pending_requests')
    @require_permission('read')
    def list_requests(self, request):
        admin = get_current_admin(request)
        family_requests = Families.objects.filter(
            faculty_id=admin.faculty_id,
            status=STATUS_PENDING
        ).order_by('-created_at')
        return Response(FamilyRequestListSerializer(family_requests, many=True).data)
    @extend_schema(
        description="Approve request initially, setting the minimum members limit and closing date for joining.",
        request=PreApproveFamilySerializer,  
        responses={
            200: OpenApiResponse(description="Family request pre-approved successfully"),
            400: OpenApiResponse(description="Invalid data or status")
        }
    )
    @action(detail=True, methods=['post'], url_path='pre-approve')
    @require_permission('update')
    def pre_approve_request(self, request, pk=None):
        admin = get_current_admin(request)
        family = get_object_or_404(Families, pk=pk, faculty_id=admin.faculty_id)
        
        if family.status != STATUS_PENDING:
            return Response(
                {"error": "لا يمكن إعطاء موافقة مبدئية. حالة الطلب يجب أن تكون 'منتظر'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PreApproveFamilySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        def business_operation(admin, ip):
            family.status = STATUS_PRE_APPROVED
            family.min_limit = serializer.validated_data['min_limit']
            family.closing_date = serializer.validated_data['closing_date']
            family.save()
            return {"message": "تم منح الموافقة المبدئية وتحديث شروط الانضمام بنجاح"}
        
        result = self.execute_admin_action(
            request=request,
            action_name='موافقة مبدئية وتحديد الشروط',
            target_type='اسر',
            business_operation=business_operation,
            family_id=family.family_id
        )
        
        return Response(result, status=status.HTTP_200_OK)
    @extend_schema(
        description="Reject a pending family creation request.",
        request=None,
        responses={
            200: OpenApiResponse(description="Family request rejected successfully"),
            400: OpenApiResponse(description="Invalid status for rejection"),
            404: OpenApiResponse(description="Family request not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='reject')
    @require_permission('update') 
    def reject_request(self, request, pk=None):
        """
        POST /api/family/faculty/{id}/reject/
        """
        admin = get_current_admin(request)
        family = get_object_or_404(Families, pk=pk, faculty_id=admin.faculty_id)
        
        if family.status not in [STATUS_PENDING, STATUS_PRE_APPROVED]:
            return Response(
                {"error": "لا يمكن رفض طلب في هذه الحالة. يجب أن تكون الحالة 'منتظر' أو 'موافقة مبدئية'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        def business_operation(admin, ip):
            family.status = STATUS_REJECTED
            family.save()
            return {"message": "تم رفض طلب إنشاء الأسرة"}
        
        result = self.execute_admin_action(
            request=request,
            action_name='رفض طلب إنشاء أسرة',
            target_type='اسر',
            business_operation=business_operation,
            family_id=family.family_id
        )
        
        return Response(result, status=status.HTTP_200_OK)

    def _set_family_creation_permission(self, request, nid, grant=True):
        """Helper method to grant or revoke family creation permission."""
        try:
            student = Students.objects.get(nid=nid)
        except Students.DoesNotExist:
            return Response(
                {"error": "لم يتم العثور على طالب"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        current_permission = student.can_create_fam
        if grant and current_permission:
            return Response(
                {"error": "الطالب لديه بالفعل صلاحية إنشاء أسرة"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not grant and not current_permission:
            return Response(
                {"error": "الطالب لا يملك صلاحية إنشاء أسرة حالياً"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action_name = 'منح صلاحية إنشاء أسرة للطالب' if grant else 'سحب صلاحية إنشاء أسرة من الطالب'
        
        def business_operation(admin, ip):
            student.can_create_fam = grant
            student.save()
            return {
                "message": "تم منح صلاحية إنشاء الأسرة للطالب بنجاح" if grant else "تم سحب صلاحية إنشاء الأسرة من الطالب بنجاح",
                "student": {
                    "nid": student.nid,
                    "name": student.name,
                    "can_create_fam": student.can_create_fam
                }
            }
        
        result = self.execute_admin_action(
            request=request,
            action_name=action_name,
            target_type='طالب',
            business_operation=business_operation,
            student_id=student.student_id
        )
        
        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(
        description="Grant family creation permission to a student by their NID",
        request=None,
        responses={
            200: OpenApiResponse(description="Student granted family creation permission"),
            404: OpenApiResponse(description="Student not found"),
            400: OpenApiResponse(description="Student already has permission")
        }
    )
    @action(detail=False, methods=['post'], url_path='family-founder/(?P<nid>[^/.]+)/add')
    @require_permission('update')
    def grant_family_creation_permission(self, request, nid=None):
        return self._set_family_creation_permission(request, nid, grant=True)

    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="Revoke family creation permission from a student by their NID",
        request=None,
        responses={
            200: OpenApiResponse(description="Student family creation permission revoked"),
            404: OpenApiResponse(description="Student not found"),
            400: OpenApiResponse(description="Student already doesn't have permission")
        }
    )
    @action(detail=False, methods=['delete'], url_path='family-founder/(?P<nid>[^/.]+)/remove')
    @require_permission('update')
    def revoke_family_creation_permission(self, request, nid=None):
        return self._set_family_creation_permission(request, nid, grant=False)

    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="List all students with family creation permission in the faculty",
        responses={200: FamilyFounderSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='family-founders')
    def get_family_founders(self, request):
        admin = get_current_admin(request)
        students = Students.objects.filter(
            faculty=admin.faculty_id,
            can_create_fam=True
        )

        return Response(FamilyFounderSerializer(students, many=True).data)
    
    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="Create a new environment family with detailed configuration",
        request=CreateFamilyRequestSerializer,
        responses={
            201: FamilyRequestDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            409: OpenApiResponse(description="Conflict error"),
            500: OpenApiResponse(description="Server error")
        }
    )
    @action(detail=False, methods=['post'], url_path='environment-family')
    def create_environment_family(self, request):
        try:
            admin = get_current_admin(request)

            serializer = CreateEnvFamilyRequestSerializer(
                data=request.data,
                context={'creation_source': 'faculty_admin'}
            )
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            with transaction.atomic():
                family = FamilyService.create_family_request(
                    request_data=validated_data,
                    created_by_student=False,
                    user_id=admin.admin_id
                )
                family.status = STATUS_APPROVED
                family.save(update_fields=["status"])
            
            response_serializer = FamilyRequestDetailSerializer(
                family, 
                context={'created_by_student': False}
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)

            # Check for conflict errors
            if any(keyword in error_msg for keyword in [
                "مسؤول بالفعل",
                "طلب أسرة قيد الانتظار",
                "مكلفين بأدوار"
            ]):
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_409_CONFLICT
                )

            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"Error creating environment family: {str(e)}")
            return Response(
                {'error': f'خطأ غير متوقع: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _calculate_gender_distribution(self, family_id):
        """Calculate gender distribution for family members."""
        results = FamilyMembers.objects.filter(
            family_id=family_id
        ).values('student__gender').annotate(
            count=Count('student_id')
        ).order_by('student__gender')

        distribution = {'F': 0, 'M': 0, 'total': 0}
        for result in results:
            gender = result['student__gender']
            count = result['count']
            if gender in ['F', 'M']:
                distribution[gender] = count
                distribution['total'] += count
        
        return distribution

    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="Export family report as PDF",
        responses={
            200: OpenApiResponse(description="PDF file download"),
            403: OpenApiResponse(description="Access denied"),
            404: OpenApiResponse(description="Family not found"),
            500: OpenApiResponse(description="Server error")
        }
    )
    @action(detail=False, methods=['get'], url_path=r'(?P<family_id>\d+)/export')
    @require_permission('read')
    def export(self, request, family_id=None):
        admin = get_current_admin(request)
        try:
            family = Families.objects.select_related('faculty').get(family_id=family_id)
            if admin.faculty and family.faculty_id != admin.faculty.faculty_id:
                return Response({'detail': 'Access denied to this family'}, status=403)

            distribution = self._calculate_gender_distribution(family_id)

            data = {
                'distribution': distribution,
                'family_admins': FamilyAdmins.objects.filter(family=family_id),
                'family_members': FamilyMembers.objects.select_related('student').filter(family_id=family_id),
                'family': family
            }

        except Families.DoesNotExist:
            return Response({'detail': 'Family not found'}, status=404)
        except DatabaseError:
            logger.exception("Database error while fetching family data")
            return Response({'detail': 'Database error while fetching data'}, status=500)

        try:
            html_content = render_to_string("api/family-report.html", {"data": data})
            pdf_bytes = generate_pdf_sync(
                html_content,
                margins={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"}
            )
            buffer = BytesIO(pdf_bytes)
        except Exception as e:
            logger.exception(f"PDF generation error: {str(e)}")
            return Response({'detail': 'Could not generate PDF'}, status=500)

        filename = f"family_report_{family_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response = FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf'
        )
        response['Content-Length'] = len(pdf_bytes)
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
# ------------------------------------------------------------------
# Events Approval (Faculty Admin)
# ------------------------------------------------------------------
@extend_schema(tags=["Family Fac Admin APIs"])
class FacultyEventApprovalViewSet(AdminActionMixin, viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventDetailSerializer
        return EventSerializer

    def get_queryset(self):
        admin = get_current_admin(self.request)
        return Events.objects.filter(
            faculty_id=admin.faculty_id  
        ).exclude(
            family__type='مركزية'        
        )

    @extend_schema(
        description="List pending events for families within this faculty.",
        responses={200: EventSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        events = self.get_queryset().filter(status=STATUS_PENDING)
        return Response(self.get_serializer(events, many=True).data)
    
    @extend_schema(
        description="Get event details including registered members.",
        responses={200: EventDetailSerializer}
    )
    def retrieve(self, request, pk=None):
        event = self.get_object()
        return Response(self.get_serializer(event).data)

    def _set_event_status(self, request, pk, new_status, action_name):
        """Helper method to approve or reject an event."""
        event = self.get_object()
        
        if event.status != STATUS_PENDING:
            return Response(
                {"error": "This event is not pending approval"},
                status=status.HTTP_400_BAD_REQUEST
            )

        def business_operation(admin, ip):
            event.status = new_status
            event.save()
            status_msg = "Event approved successfully" if new_status == STATUS_APPROVED else "Event rejected successfully"
            return {"message": status_msg}
        
        result = self.execute_admin_action(
            request=request,
            action_name=action_name,
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id
        )

        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(
        description="Approve an event for a faculty family.",
        request=None,
        responses={200: OpenApiResponse(description="Event approved")}
    )
    @action(detail=True, methods=['post'], url_path='approve')
    @require_permission('update')
    def approve(self, request, pk=None):
        return self._set_event_status(
            request, pk, STATUS_APPROVED,
            f"الموافقة على نشاط"
        )

    @extend_schema(
        description="Reject an event for a faculty family.",
        request=None,
        responses={200: OpenApiResponse(description="Event rejected")}
    )
    @action(detail=True, methods=['post'], url_path='reject')
    @require_permission('update')
    def reject(self, request, pk=None):
        return self._set_event_status(
            request, pk, STATUS_REJECTED,
            f"رفض نشاط"
        ) 
    @extend_schema(
        description="List accepted events for a specific family within this faculty.",
        parameters=[
            OpenApiParameter(name='family_id', required=True, type=OpenApiTypes.INT),
        ],
        responses={
            200: EventSerializer(many=True),
            400: OpenApiResponse(description="Invalid Family ID"),
            404: OpenApiResponse(description="Family not found or invalid")
        }
    )
    @action(detail=False, methods=['get'], url_path='by-family')
    def list_accepted_events_by_family(self, request):
        family_id = request.query_params.get('family_id')
        admin = get_current_admin(request)

        try:
            family_id = int(family_id)
        except (TypeError, ValueError):
            return Response(
                {"error": "family_id must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        family_is_valid = Families.objects.filter(
            family_id=family_id, 
            faculty_id=admin.faculty_id, 
        ).exists()

        if not family_is_valid:
            return Response(
                {"error": "Family not found or does not belong to your faculty."},
                status=status.HTTP_404_NOT_FOUND
            )

        events = self.get_queryset().filter(family_id=family_id, status=STATUS_APPROVED)
        return Response(self.get_serializer(events, many=True).data)
    def _validate_event_editable(self, event):
        """Validate that event is in approved status for participant management."""
        if event.status != STATUS_APPROVED:
            raise serializers.ValidationError(
                {"error": "Cannot manage participants. The event must be 'مقبول' first."}
            )

    @extend_schema(
        description="Approve ALL pending participants.",
        request=None,
        responses={
            200: OpenApiResponse(description="Approved successfully"),
            400: OpenApiResponse(description="Event not in correct status")
        }
    )
    @action(detail=True, methods=['post'], url_path='approve-all-participants')
    @require_permission('update')
    def approve_all_participants(self, request, pk=None):
        with transaction.atomic():
            event = self.get_object()
            self._validate_event_editable(event)
            
            def business_operation(admin, ip):
                participants_qs = Prtcps.objects.select_for_update().filter(
                    event=event, 
                    status=STATUS_PENDING
                )
                updated_count = participants_qs.update(status=STATUS_APPROVED)
                return {"message": f"Successfully approved {updated_count} participants."}
            
            result = self.execute_admin_action(
                request=request,
                action_name=f"قبول جماعي للمشاركين في النشاط: {event.title}",
                target_type='نشاط',
                business_operation=business_operation,
                event_id=event.event_id
            )
        
        return Response(result, status=status.HTTP_200_OK)
    def _set_participant_status(self, request, pk, student_id, new_status, action_name):
        """Helper method to approve or reject a participant."""
        event = self.get_object()
        self._validate_event_editable(event)

        student_id = int(student_id)

        try:
            student = Students.objects.only('faculty_id').get(student_id=student_id)
        except Students.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if student.faculty_id != event.faculty_id:
            return Response(
                {"error": "Student does not belong to the event's faculty"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            with transaction.atomic():
                def business_operation(admin, ip):
                    updated = Prtcps.objects.select_for_update().filter(
                        event=event,
                        student_id=student_id
                    ).update(status=new_status)

                    if updated == 0:
                        raise ValidationError("Student not found in this event")
                    
                    status_msg = "Participant approved successfully" if new_status == STATUS_APPROVED else "Participant rejected successfully"
                    return {"message": status_msg}
                
                result = self.execute_admin_action(
                    request=request,
                    action_name=action_name,
                    target_type='نشاط',
                    business_operation=business_operation,
                    event_id=event.event_id
                )
            return Response(result, status=status.HTTP_200_OK)
        except ValidationError as e:
            error_msg = e.detail if hasattr(e, "detail") else str(e)
            return Response(
                {"error": error_msg},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        description="Approve a specific participant.",
        request=None,
        parameters=[
            OpenApiParameter(
                name='student_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(description="Participant approved"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Participant not found")
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path=r'participants/(?P<student_id>\d+)/approve'
    )
    @require_permission('update')
    def approve_participant(self, request, pk=None, student_id=None):
        return self._set_participant_status(
            request, pk, student_id, STATUS_APPROVED,
            f"قبول الطالب رقم {student_id} في النشاط"
        )

    @extend_schema(
        description="Reject a specific participant.",
        request=None,
        parameters=[
            OpenApiParameter(
                name='student_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(description="Participant rejected"),
            404: OpenApiResponse(description="Participant not found")
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path=r'participants/(?P<student_id>\d+)/reject'
    )
    @require_permission('update')
    def reject_participant(self, request, pk=None, student_id=None):
        return self._set_participant_status(
            request, pk, student_id, STATUS_REJECTED,
            f"رفض الطالب رقم {student_id} من النشاط"
        )
# ------------------------------------------------------------------
# Family Members (Faculty Admin)
# ------------------------------------------------------------------
@extend_schema(tags=["Family Fac Admin APIs"])
class FamilyMembersViewSet(AdminActionMixin, viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية']
    queryset = FamilyMembers.objects.all()
    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="Remove a member from a specific family",
        responses={
            200: OpenApiResponse(description="Member removed successfully"),
            404: OpenApiResponse(description="Member not found")
        }
    )
    @action(
        detail=False,
        methods=['delete'],
        url_path=r'families/(?P<family_id>\d+)/members/(?P<member_id>\d+)'
    )
    @require_permission('delete')
    def remove_member(self, request, family_id=None, member_id=None):
        family = get_object_or_404(Families, pk=family_id)
        member = get_object_or_404(
            FamilyMembers,
            family=family,
            student_id=member_id
        )
        
        def business_operation(admin, ip):
            member.delete()
            return {"message": "Member removed successfully"}
        
        result = self.execute_admin_action(
            request=request,
            action_name='حذف عضو من أسرة',
            target_type='اسر',
            business_operation=business_operation,
            family_id=family_id
        )
        
        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="Add a student to a family using their national ID.",
        responses={
            201: OpenApiResponse(description="Student added successfully"),
            400: OpenApiResponse(description="Invalid data or family not approved"),
            404: OpenApiResponse(description="Student or family not found"),
            403: OpenApiResponse(description="Faculty mismatch")
        }
    )
    @action(
        detail=False, 
        methods=['post'], 
        url_path=r'families/(?P<family_id>\d+)/add-member/(?P<nid>\d+)'
    )
    @require_permission('update')
    def add_member_by_nid_direct(self, request, family_id=None, nid=None):
        admin = get_current_admin(request)
        
        family = get_object_or_404(
            Families, 
            pk=family_id, 
            faculty_id=admin.faculty_id,
            status=STATUS_APPROVED
        )
        
        try:
            student = Students.objects.get(nid=nid)
        except Students.DoesNotExist:
            return Response(
                {"error": "Student with this national ID not found in the system"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        if student.faculty_id != admin.faculty_id:
            return Response(
                {"error": "Student from another faculty cannot be added to this family"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        if FamilyMembers.objects.filter(family=family, student=student).exists():
            return Response(
                {"error": "Student is already a member of this family"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        def business_operation(admin, ip):
            FamilyMembers.objects.create(
                family=family,
                student=student,
                role=ROLE_MEMBER,
                status=STATUS_APPROVED
            )
            return {
                "message": f"Student {student.name} added successfully to family {family.name}",
                "student_id": student.student_id
            }
        
        result = self.execute_admin_action(
            request=request,
            action_name='Add member to family (direct approval)',
            target_type='اسر',
            business_operation=business_operation,
            family_id=family_id
        )
        
        return Response(result, status=status.HTTP_201_CREATED)
