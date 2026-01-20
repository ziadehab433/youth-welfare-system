from pytz import timezone
from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from apps.family.models import Families, FamilyMembers, Students
from apps.family.models import FamilyMembers
from apps.accounts.permissions import IsRole
from apps.family.serializers import FamiliesListSerializer, FamiliesDetailSerializer
from rest_framework.decorators import action
from drf_spectacular.utils import OpenApiResponse
from apps.accounts.utils import get_client_ip, log_data_access
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.db import transaction
from django.db.models import Count, Q
from apps.accounts.utils import get_current_admin 
from django.db import transaction
from django.utils import timezone
@extend_schema(tags=["Family Super_Dept"])
class SuperDeptFamilyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Families.objects.all()
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['مدير ادارة', 'مشرف النظام']
    def get_serializer_class(self):
        if self.action == 'retrieve':
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
        operation_id="list_families_filtered",
        description="Fetch families filtered by Type (e.g., specialized) and Faculty ID.",
        parameters=[
            OpenApiParameter(
                name='type', 
                description='Family Type', 
                required=False, 
                type=str,
                enum=['مركزية', 'نوعية', 'اصدقاء البيئة'] 
            ),
            OpenApiParameter(
                name='faculty', 
                description='Faculty ID (e.g., for specialized families)', 
                required=False, 
                type=int
            ),
        ],
        responses={200: FamiliesListSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    @extend_schema(
        operation_id="get_family_details_with_events",
        description="Fetch all details for a specific family, INCLUDING its events history.",
        responses={200: FamiliesDetailSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    @extend_schema(
        description="Reject the family request (changes status to 'مرفوض').",
        request=None,
        responses={
            200: OpenApiResponse(description="Family rejected successfully"),
            400: OpenApiResponse(description="Cannot reject family in current status")
        }
    )
    @action(detail=True, methods=['patch'], url_path='reject')
    def reject_family(self, request, pk=None):
        family = self.get_object()
        if family.status not in ['منتظر', 'موافقة مبدئية']:
            return Response(
                {"error": "لا يمكن رفض الطلب. الحالة الحالية لا تسمح بذلك."},
                status=status.HTTP_400_BAD_REQUEST
            )
        family.status = 'مرفوض'
        family.save()
        log_data_access(
            actor_id=request.user.admin_id,
            actor_type=request.user.role,
            action='رفض الأسرة (إدارة مركزية)',
            target_type='اسر',
            family_id=family.family_id,
            ip_address=get_client_ip(request)
        )

        return Response({"message": "تم رفض الأسرة بنجاح"}, status=status.HTTP_200_OK)
    @extend_schema(
        description="Approve the family creation request and convert it to an active family (Status: 'مقبول').",
        request=None,
        responses={
            200: OpenApiResponse(description="Family finally approved and active"),
            400: OpenApiResponse(description="Invalid status for final approval")
        }
    )

# ----------------------------------------------------------------
# Security Approval Actions
# ----------------------------------------------------------------
    @extend_schema(
        description="Security approve a family member",
        responses={
            200: OpenApiResponse(description="Member approved successfully"),
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Member not found"),
        }
    )
    @action(detail=True, methods=['patch'], url_path=r'members/(?P<student_id>\d+)/approve')
    def approve_family_member(self, request, pk=None, student_id=None):
        family = self.get_object()

        if family.status != 'موافقة مبدئية':
            return Response(
                {"error": "Security review unavailable. Family status must be 'Initial Approval'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        member = FamilyMembers.objects.filter(family=family, student_id=student_id).first()
        if not member:
            return Response({"error": "Member not found in this family."}, status=status.HTTP_404_NOT_FOUND)

        if member.status == 'مقبول':
            return Response({"message": "Member is already approved."}, status=status.HTTP_200_OK)

        if member.status == 'مرفوض':
            return Response(
                {"error": "Cannot approve a previously rejected member."},
                status=status.HTTP_400_BAD_REQUEST
            )

        student = Students.objects.filter(student_id=student_id).first()
        if student and student.faculty_id != family.faculty_id:
            return Response(
                {"error": "Student does not belong to the family's faculty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            FamilyMembers.objects.filter(family=family, student_id=student_id).update(status='مقبول')

        return Response(
            {
                "message": "Member security approved successfully.",
                "member_id": student_id,
                "family_id": family.family_id
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        description="Security reject a family member",
        responses={
            200: OpenApiResponse(description="Member rejected successfully"),
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Member not found"),
        }
    )
    @action(detail=True, methods=['patch'], url_path=r'members/(?P<student_id>\d+)/reject')
    def reject_family_member(self, request, pk=None, student_id=None):
        family = self.get_object()

        if family.status != 'موافقة مبدئية':
            return Response(
                {"error": "Security review unavailable. Family status must be 'Initial Approval'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        member = FamilyMembers.objects.filter(family=family, student_id=student_id).first()
        if not member:
            return Response({"error": "Member not found in this family."}, status=status.HTTP_404_NOT_FOUND)

        if member.status == 'مرفوض':
            return Response({"message": "Member is already rejected."}, status=status.HTTP_200_OK)

        if member.status == 'مقبول':
            return Response(
                {"error": "Cannot reject an already approved member."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            FamilyMembers.objects.filter(family=family, student_id=student_id).update(status='مرفوض')

        return Response(
            {
                "message": "Member security rejected successfully.",
                "member_id": student_id,
                "family_id": family.family_id
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        description="Final approval for family activation",
        responses={
            200: OpenApiResponse(description="Family activated successfully"),
            400: OpenApiResponse(description="Validation failed"),
        }
    )
    @action(detail=True, methods=['post'], url_path='final_approve')
    def final_approve(self, request, pk=None):
        family = self.get_object()

        if family.status != 'موافقة مبدئية':
            return Response(
                {"error": "Initial approval is required first before final activation."},
                status=status.HTTP_400_BAD_REQUEST
            )

        pending_count = FamilyMembers.objects.filter(
            family=family,
            status='منتظر'
        ).count()

        if pending_count > 0:
            return Response(
                {
                    "error": "Cannot activate. There are members still pending review.",
                    "pending_members_count": pending_count
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        accepted_count = FamilyMembers.objects.filter(
            family=family,
            status='مقبول'
        ).count()

        if accepted_count < family.min_limit:
            rejected_count = FamilyMembers.objects.filter(
                family=family,
                status='مرفوض'
            ).count()

            return Response(
                {
                    "error": "Insufficient number of accepted members to activate the family.",
                    "accepted_members": accepted_count,
                    "rejected_members": rejected_count,
                    "required_minimum": family.min_limit
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        has_leader = FamilyMembers.objects.filter(
            family=family,
            status='مقبول',
            role='أخ أكبر'  
        ).exists()

        if not has_leader:
            return Response(
                {"error": "A security-approved family leader is required (Role: أخ أكبر)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            family.status = 'مقبول'
            family.approved_by = get_current_admin(request)
            family.final_approved_at = timezone.now()
            family.save()

        return Response(
            {
                "message": "Family activated successfully.",
                "family_id": family.family_id,
                "accepted_members": accepted_count,
                "approved_by": get_current_admin(request).name,
                "approval_date": family.final_approved_at.isoformat()
            },
            status=status.HTTP_200_OK
        )