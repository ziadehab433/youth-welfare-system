from rest_framework import viewsets, status
from apps.family.models import Students
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse
from apps.family.models import Families, FamilyMembers
from apps.family.services.family_service import FamilyService
from apps.event.models import Events
from apps.event.serializers import EventSerializer
from apps.accounts.permissions import IsRole, require_permission
from apps.accounts.utils import (
    get_current_admin,
    get_client_ip,
    log_data_access
)
from drf_spectacular.utils import extend_schema, OpenApiParameter 

from apps.family.serializers import (
    FamiliesListSerializer,
    FamiliesDetailSerializer,
    FamilyRequestListSerializer, 
    PreApproveFamilySerializer,
    FamilyFounderSerializer
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
        description="List all families for the current faculty",
        responses={200: FamiliesListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='families')
    @require_permission('read')
    def list_families(self, request):
        admin = get_current_admin(request)
        families = FamilyService.get_families_for_faculty(admin)
        return Response(FamiliesListSerializer(families, many=True).data)

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
                target_id=student.student_id,
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
                target_id=student.student_id,
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
        admin = get_current_admin(request)
        students = Students.objects.filter(
            faculty=admin.faculty_id,
            can_create_fam=True
        )

        return Response(FamilyFounderSerializer(students, many=True).data)


# ------------------------------------------------------------------
# Events Approval (Faculty Admin)
# ------------------------------------------------------------------
@extend_schema(tags=["Family Fac Admin APIs"])
class FacultyEventApprovalViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية']
    serializer_class = EventSerializer

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
        return Response(EventSerializer(events, many=True).data)

    @extend_schema(
        description="Get event details.",
        responses={200: EventSerializer}
    )
    def retrieve(self, request, pk=None):
        event = self.get_object()
        return Response(EventSerializer(event).data)

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
