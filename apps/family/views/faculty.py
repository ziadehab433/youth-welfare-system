from jsonschema import ValidationError
from rest_framework import viewsets, status, serializers
from django.db.models import Count
from django.http import HttpResponse
from django.template.loader import render_to_string
import asyncio
from django.db import DatabaseError
from django.db import transaction
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
from django.db import transaction

from apps.accounts.utils import (
    get_current_admin,
    get_client_ip,
    get_current_student,
    log_data_access
)
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from apps.event.models import Prtcps
from apps.solidarity.utils import handle_report_data, html_to_pdf_buffer
from apps.family.serializers import (
    EventDetailSerializer,
    FamiliesListSerializer,
    FamiliesDetailSerializer,
    FamilyRequestListSerializer,
    PreApproveFamilySerializer,
    FamilyFounderSerializer,
    CreateFamilyRequestSerializer,
    FamilyRequestDetailSerializer
)
# ------------------------------------------------------------------
# Families (Faculty Admin)
# ------------------------------------------------------------------
@extend_schema(tags=["Family Fac Admin APIs"])
class FamilyFacultyAdminViewSet(viewsets.GenericViewSet):
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
        approved_families = families.filter(status='مقبول')
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
        description="Fetch ONLY pending ('منتظر') family creation requests for the current faculty.",
        responses={200: FamilyRequestListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='pending_requests')
    @require_permission('read')
    def list_requests(self, request):
        admin = get_current_admin(request)
        requests = Families.objects.filter(
            faculty_id=admin.faculty_id,
            status="منتظر"  
        ).order_by('-created_at')
        return Response(FamilyRequestListSerializer(requests, many=True).data)
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
        with transaction.atomic():
            admin = get_current_admin(request)
            family = get_object_or_404(Families, pk=pk, faculty_id=admin.faculty_id)
            if family.status != 'منتظر':
                return Response(
                    {"error": "لا يمكن إعطاء موافقة مبدئية. حالة الطلب يجب أن تكون 'منتظر'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = PreApproveFamilySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            family.status = 'موافقة مبدئية'
            family.min_limit = serializer.validated_data['min_limit']
            family.closing_date = serializer.validated_data['closing_date']
            family.save()
            log_data_access(
                actor_id=admin.admin_id,
                actor_type=admin.role,
                action='موافقة مبدئية وتحديد الشروط',
                target_type='اسر',
                family_id=family.family_id,
                ip_address=get_client_ip(request)
            )
            return Response(
                {"message": "تم منح الموافقة المبدئية وتحديث شروط الانضمام بنجاح"}, 
                status=status.HTTP_200_OK
            )
    @extend_schema(
        description="Reject a pending family creation request.",
        request=None,
        responses={
            200: OpenApiResponse(description="Family request rejected successfully"),
            404: OpenApiResponse(description="Family request not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='reject')
    @require_permission('update') 
    def reject_request(self, request, pk=None):
        with transaction.atomic():
            """
            POST /api/family/faculty/{id}/reject/
            """
            admin = get_current_admin(request)
            family = get_object_or_404(Families, pk=pk, faculty_id=admin.faculty_id)
            family.status = 'مرفوض'
            family.save()
            log_data_access(
                actor_id=admin.admin_id,
                actor_type=admin.role,
                action='رفض طلب إنشاء أسرة',
                target_type='اسر',
                family_id=family.family_id,
                ip_address=get_client_ip(request)
            )

            return Response(
                {"message": "تم رفض طلب إنشاء الأسرة"}, 
                status=status.HTTP_200_OK
            )

    @extend_schema(
        description="Grant family creation permission to a student by their NID",
        request=None,
        responses={ 200: OpenApiResponse(description="Student granted family creation permission"), 404: OpenApiResponse(description="Student not found"), 400: OpenApiResponse(description="Student already has permission") })
    @action(detail=False, methods=['post'], url_path='family-founder/(?P<nid>[^/.]+)/add')
    @require_permission('update')
    def grant_family_creation_permission(self, request, nid=None):
        admin = get_current_admin(request)
        
        try:
            with transaction.atomic():  # Begin transaction
                student = Students.objects.get(nid=nid)
                
                if student.can_create_fam:
                    return Response(
                        {"error": "الطالب لديه بالفعل صلاحية إنشاء أسرة"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                student.can_create_fam = True
                student.save()
                
                # might move this into its own func 
                log_data_access(
                    actor_id=admin.admin_id,
                    actor_type=admin.role,
                    action='منح صلاحية إنشاء أسرة للطالب',
                    target_type='طالب',
                    student_id=student.student_id,
                    ip_address=get_client_ip(request)
                )
                
                return Response(
                    {
                        "message": "تم منح صلاحية إنشاء الأسرة للطالب بنجاح",
                        "student": {
                            "nid": student.nid,
                            "name": f"{student.name}",  
                            "can_create_fam": student.can_create_fam
                        }
                    },
                    status=status.HTTP_200_OK
                )
            
        except Students.DoesNotExist:
            return Response(
                {"error": "لم يتم العثور على طالب"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"حدث خطأ: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="Revoke family creation permission from a student by their NID",
        request=None,
        responses={ 200: OpenApiResponse(description="Student family creation permission revoked"), 404: OpenApiResponse(description="Student not found"), 400: OpenApiResponse(description="Student already doesn't have permission") }
    )
    @action(detail=False, methods=['delete'], url_path='family-founder/(?P<nid>[^/.]+)/remove')
    @require_permission('update')
    def revoke_family_creation_permission(self, request, nid=None):
        admin = get_current_admin(request)
        
        try:
            with transaction.atomic():
                student = Students.objects.get(nid=nid)
                
                if not student.can_create_fam:
                    return Response(
                        {"error": "الطالب لا يملك صلاحية إنشاء أسرة حالياً"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                student.can_create_fam = False
                student.save()
                
                log_data_access(
                    actor_id=admin.admin_id,
                    actor_type=admin.role,
                    action='سحب صلاحية إنشاء أسرة من الطالب',
                    target_type='طالب',
                    student_id=student.student_id,
                    ip_address=get_client_ip(request)
                )
                
                return Response(
                    {
                        "message": "تم سحب صلاحية إنشاء الأسرة من الطالب بنجاح",
                        "student": {
                            "nid": student.nid,
                            "name": f"{student.name}",
                            "can_create_fam": student.can_create_fam
                        }
                    },
                    status=status.HTTP_200_OK
                )
            
        except Students.DoesNotExist:
            return Response(
                {"error": "لم يتم العثور على طالب"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"حدث خطأ: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="List all students with family creation permission in the faculty",
        responses={200: FamilyFounderSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='family-founders')
    def get_family_founders(self, request):
        admin = self.get_current_admin(request)
        students = Students.objects.filter(
            faculty=admin.faculty_id,
            can_create_fam=True
        )

        return Response(FamilyFounderSerializer(students, many=True).data)
    
    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="Create a new envronment family with detailed configuration",
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
            student = get_current_student(request)

            # Validate request data
            serializer = CreateFamilyRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            # Create family request
            family = FamilyService.create_family_request(
                request_data=validated_data,
                created_by_student=student
            )

            # Serialize and return the created family
            response_serializer = FamilyRequestDetailSerializer(family, created_by_student=False)
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
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'خطأ غير متوقع: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="pdf",
        responses={
            200: OpenApiResponse(
                description="PDF file download",
            )
        }
    )
    @action(detail=False, methods=['get'], url_path=r'(?P<family_id>\d+)/export')
    @require_permission('read')
    def export(self, request, family_id=None):
        admin = get_current_admin(request)
        data = {}


        try:
            family = Families.objects.select_related('faculty').get(family_id=family_id)
            if admin.faculty and family.faculty_id != admin.faculty.faculty_id:
                return Response({'detail': 'Access denied to this family'}, status=403)

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

            class DataObject:
                def __init__(self):
                    self.distribution = distribution
                    self.family_admins = FamilyAdmins.objects.filter(family=family_id)
                    self.family_members = FamilyMembers.objects.select_related( 'student').filter(family_id=family_id)
                    self.family = family
            data = DataObject()

        except DatabaseError:
            return Response({'detail': 'database error while fetching data'}, status=500)

        html_content = render_to_string("api/family-report.html", { "data": data })

        try:
            buffer = asyncio.new_event_loop().run_until_complete(
                html_to_pdf_buffer(html_content)
            )
        except Exception:
            return Response({'detail': 'could not generate pdf'}, status=500)
        
        response = HttpResponse( 
            buffer,
            content_type='application/pdf'
        )

        response['Content-Disposition'] = f'attachment; filename="generated_pdf.pdf"'
        
        return response


# ------------------------------------------------------------------
# Events Approval (Faculty Admin)
# ------------------------------------------------------------------
@extend_schema(tags=["Family Fac Admin APIs"])
class FacultyEventApprovalViewSet(viewsets.GenericViewSet):
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
        events = self.get_queryset().filter(status="منتظر")
        return Response(self.get_serializer(events, many=True).data)
    
    @extend_schema(
        description="Get event details including registered members.",
        responses={200: EventDetailSerializer}
    )

    def retrieve(self, request, pk=None):
        event = self.get_object()
        return Response(self.get_serializer(event).data)
    @extend_schema(
        description="Approve an event for a faculty family.",
        request=None,
        responses={200: OpenApiResponse(description="Event approved")}
    )
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        event = self.get_object()
        if event.status != 'منتظر':
             return Response({"error": "This event is not pending approval"}, status=status.HTTP_400_BAD_REQUEST)

        event.status = "مقبول"
        event.save()
        return Response({"message": "Event approved"}, status=status.HTTP_200_OK)

    @extend_schema(
        description="Reject an event for a faculty family.",
        request=None,
        responses={200: OpenApiResponse(description="Event rejected")}
    )
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        event = self.get_object()

        if event.status != 'منتظر':
             return Response({"error": "This event is not pending approval"}, status=status.HTTP_400_BAD_REQUEST)

        event.status = "مرفوض"
        event.save()
        return Response({"message": "Event rejected"}, status=status.HTTP_200_OK)
    # ----------------------------------------------------------------
    # List Accepted Events by Family
    # ----------------------------------------------------------------
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
        raw_family_id = request.query_params.get('family_id')
        admin = get_current_admin(request)

        try:
            family_id = int(raw_family_id)
        except (TypeError, ValueError):
            return Response({"error": "family_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
        family_is_valid = Families.objects.filter(
            family_id=family_id, 
            faculty_id=admin.faculty_id, 
        ).exists()

        if not family_is_valid:
            return Response(
                {"error": "Family not found, is not 'نوعية', or does not belong to your faculty."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        events = self.get_queryset().filter(family_id=family_id, status='مقبول')
        return Response(self.get_serializer(events, many=True).data)
    # ----------------------------------------------------------------
    # Manage Event Participants 
    # ----------------------------------------------------------------
    def _validate_event_editable(self, event):
        if event.status != 'مقبول':
            raise serializers.ValidationError(
                {"error": "Cannot manage participants. The event must be 'مقبول' first."}
            )

    @extend_schema(
        description="Approve ALL pending participants.",
        request=None,
        responses={200: OpenApiResponse(description="Approved successfully"), 400: OpenApiResponse}
    )
    @action(detail=True, methods=['post'], url_path='approve-all-participants')
    def approve_all_participants(self, request, pk=None):
        event = self.get_object()
        self._validate_event_editable(event)
        with transaction.atomic():
            participants_qs = Prtcps.objects.select_for_update().filter(
                event=event, 
                status='منتظر'
            )
            updated_count = participants_qs.update(status='مقبول')
        
        return Response(
            {"message": f"Successfully approved {updated_count} participants."}, 
            status=status.HTTP_200_OK
        )
    @extend_schema(
        description="Approve a specific participant.",
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
    def approve_participant(self, request, pk=None, student_id=None):
        event = self.get_object()
        self._validate_event_editable(event)

        student_id = int(student_id)

        student_faculty_id = Students.objects.filter(
            student_id=student_id
        ).values_list('faculty_id', flat=True).first()

        if student_faculty_id != event.faculty_id:
            return Response(
                {"error": "Student does not belong to the event's faculty"},
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            updated = Prtcps.objects.select_for_update().filter(
                event=event,
                student_id=student_id
            ).update(status='مقبول')

        if updated == 0:
            return Response(
                {"error": "Student not found in this event"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"message": "Participant approved successfully"},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        description="Reject a specific participant.",
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
    def reject_participant(self, request, pk=None, student_id=None):
        event = self.get_object()
        self._validate_event_editable(event)

        student_id = int(student_id)

        with transaction.atomic():
            updated = Prtcps.objects.select_for_update().filter(
                event=event,
                student_id=student_id
            ).update(status='مرفوض')

        if updated == 0:
            return Response(
                {"error": "Student not found in this event"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            {"message": "Participant rejected successfully"},
            status=status.HTTP_200_OK
        )
# ------------------------------------------------------------------
# Family Members (Faculty Admin)
# ------------------------------------------------------------------
@extend_schema(tags=["Family Fac Admin APIs"])
class FamilyMembersViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية']
    queryset = FamilyMembers.objects.all()
    @extend_schema(
        tags=["Family Fac Admin APIs"],
        description="Remove a member from a specific family",
        responses={204: OpenApiResponse(description="Member removed")}
    )
    @action(
        detail=False,
        methods=['delete'],
        url_path=r'families/(?P<family_id>\d+)/members/(?P<member_id>\d+)'
    )
    @require_permission('delete')
    def remove_member(self, request, family_id=None, member_id=None):
        with transaction.atomic():
            admin = get_current_admin(request)

            family = get_object_or_404(Families, pk=family_id)
            member = get_object_or_404(
                FamilyMembers,
                family=family,
                student_id=member_id
            )
            member.delete()
            log_data_access(
                actor_id=admin.admin_id,
                actor_type=admin.role,
                action='حذف عضو من أسرة',
                target_type='اسر',
                family_id=family_id,
                ip_address=get_client_ip(request)
            )
            return Response(
                {"message": "Member removed successfully"},
                status=status.HTTP_200_OK
            )
