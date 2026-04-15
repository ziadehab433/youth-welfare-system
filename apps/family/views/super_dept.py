from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.db.models import Count, F, Q
from django.db import transaction
from django.utils import timezone
from apps.family.models import Families, FamilyMembers, Students
from apps.accounts.permissions import IsRole
from apps.family.serializers import FamiliesListSerializer, FamiliesDetailSerializer
from apps.accounts.mixins import AdminActionMixin


@extend_schema(tags=["Family Super_Dept"])
class SuperDeptFamilyViewSet(AdminActionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Families.objects.all()
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['مدير ادارة', 'مشرف النظام']

    # ----------------------------------------------------------------
    # Status Constants
    # ----------------------------------------------------------------
    FAMILY_STATUS_PENDING = 'منتظر'
    FAMILY_STATUS_INITIAL = 'موافقة مبدئية'
    FAMILY_STATUS_ACTIVE = 'مقبول'
    FAMILY_STATUS_REJECTED = 'مرفوض'
    MEMBER_STATUS_PENDING = 'منتظر'
    MEMBER_STATUS_APPROVED = 'مقبول'
    MEMBER_STATUS_REJECTED = 'مرفوض'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FamiliesDetailSerializer
        return FamiliesListSerializer

    def get_queryset(self):
        queryset = Families.objects.annotate(
            members_count=Count('family_members')
        )
        filters = {}
        status_param = self.request.query_params.get('status')
        if status_param:
            filters['status'] = status_param
        family_type = self.request.query_params.get('type')
        if family_type:
            filters['type'] = family_type
        faculty_id = self.request.query_params.get('faculty')
        if faculty_id:
            filters['faculty_id'] = faculty_id
        if filters:
            queryset = queryset.filter(**filters)
        if self.request.query_params.get('ready') == 'true':
            queryset = queryset.filter(
                status=self.FAMILY_STATUS_INITIAL,
                members_count__gte=F('min_limit')
            )
        return queryset.order_by('-created_at')
    # ----------------------------------------------------------------
    # Read Actions
    # ----------------------------------------------------------------
    @extend_schema(
        operation_id="list_families_filtered",
        description="Fetch families with full filtering capabilities.",
        parameters=[
            OpenApiParameter(name='status', description='Filter by status', required=False, type=str,
                             enum=['منتظر', 'موافقة مبدئية', 'مقبول', 'مرفوض']),
            OpenApiParameter(name='type', description='Family Type', required=False, type=str),
            OpenApiParameter(name='faculty', description='Faculty ID', required=False, type=int),
            OpenApiParameter(name='ready', description='Show only families ready for final approval',
                             required=False, type=bool),
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
    # ----------------------------------------------------------------
    # Family-Level Actions
    # ----------------------------------------------------------------
    @extend_schema(
        description="Reject the family request (changes status to 'مرفوض').",
        request=None,
        responses={
            200: OpenApiResponse(description="Family rejected successfully"),
            400: OpenApiResponse(description="Cannot reject family in current status"),
        }
    )
    @action(detail=True, methods=['patch'], url_path='reject')
    def reject_family(self, request, pk=None):
        with transaction.atomic():
            family = Families.objects.select_for_update().get(pk=pk)
            if family.status not in [self.FAMILY_STATUS_PENDING, self.FAMILY_STATUS_INITIAL]:
                return Response(
                    {"error": "لا يمكن رفض الطلب. الحالة الحالية لا تسمح بذلك."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            def business_operation(admin, ip):
                family.status = self.FAMILY_STATUS_REJECTED
                family.save()
                return {"message": "تم رفض الأسرة بنجاح"}

            result = self.execute_admin_action(
                request=request,
                action_name='رفض الأسرة (إدارة مركزية)',
                target_type='اسر',
                business_operation=business_operation,
                family_id=family.family_id
            )
            return Response(result, status=status.HTTP_200_OK)
    # ----------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------
    def _get_member_or_error(self, family, student_id):
        member = FamilyMembers.objects.filter(family=family, student_id=student_id).first()
        if not member:
            return None, Response(
                {"error": "Member not found in this family."},
                status=status.HTTP_404_NOT_FOUND
            )
        return member, None

    def _validate_family_for_security_review(self, family):
        if family.status not in [self.FAMILY_STATUS_INITIAL, self.FAMILY_STATUS_ACTIVE]:
            return Response(
                {"error": "Security review unavailable. Family status must be 'Initial Approval' or 'Active'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return None
    # ----------------------------------------------------------------
    # Member-Level Actions (Security Review)
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
        with transaction.atomic():
            family = Families.objects.select_for_update().get(pk=pk)
            if error := self._validate_family_for_security_review(family):
                return error

            member, error = self._get_member_or_error(family, student_id)
            if error:
                return error

            if member.status == self.MEMBER_STATUS_APPROVED:
                return Response({"message": "Member is already approved."}, status=status.HTTP_200_OK)
            if member.status == self.MEMBER_STATUS_REJECTED:
                return Response(
                    {"error": "Cannot approve a previously rejected member."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            student = Students.objects.filter(student_id=student_id).first()
            if family.type == 'نوعية':
                if not student:
                    return Response({"error": "الطالب غير موجود في سجلات الكلية."}, status=status.HTTP_400_BAD_REQUEST)
                if student.faculty_id != family.faculty_id:
                    return Response({"error": "الطالب لا ينتمي لكلية الأسرة."}, status=status.HTTP_400_BAD_REQUEST)

            def business_operation(admin, ip):
                FamilyMembers.objects.filter(family=family, student_id=student_id).update(status=self.MEMBER_STATUS_APPROVED)
                return {
                    "message": "Member security approved successfully.",
                    "member_id": student_id,
                    "family_id": family.family_id,
                }

            result = self.execute_admin_action(
                request=request,
                action_name=f'الموافقة على عضو الأسرة (رقم: {student_id})',
                target_type='اسر',
                business_operation=business_operation,
                family_id=family.family_id
            )
            return Response(result, status=status.HTTP_200_OK)

    @extend_schema(
        description="Security reject a family member",
        request=None,
        responses={
            200: OpenApiResponse(description="Member rejected successfully"),
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Member not found"),
        }
    )
    @action(detail=True, methods=['patch'], url_path=r'members/(?P<student_id>\d+)/reject')
    def reject_family_member(self, request, pk=None, student_id=None):
        with transaction.atomic():
            family = Families.objects.select_for_update().get(pk=pk)
            if error := self._validate_family_for_security_review(family):
                return error

            member, error = self._get_member_or_error(family, student_id)
            if error:
                return error

            if member.status == self.MEMBER_STATUS_REJECTED:
                return Response({"message": "Member is already rejected."}, status=status.HTTP_200_OK)
            if member.status == self.MEMBER_STATUS_APPROVED:
                return Response(
                    {"error": "Cannot reject an already approved member."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            def business_operation(admin, ip):
                FamilyMembers.objects.filter(family=family, student_id=student_id).update(status=self.MEMBER_STATUS_REJECTED)
                return {
                    "message": "Member security rejected successfully.",
                    "member_id": student_id,
                    "family_id": family.family_id,
                }

            result = self.execute_admin_action(
                request=request,
                action_name=f'رفض عضو الأسرة (رقم: {student_id})',
                target_type='اسر',
                business_operation=business_operation,
                family_id=family.family_id
            )
            return Response(result, status=status.HTTP_200_OK)
    # ----------------------------------------------------------------
    # Final Approval
    # ----------------------------------------------------------------
    @extend_schema(
        description="Final approval for family activation",
        request=None,
        responses={
            200: OpenApiResponse(description="Family activated successfully"),
            400: OpenApiResponse(description="Validation failed"),
        }
    )
    @action(detail=True, methods=['post'], url_path='final_approve')
    def final_approve(self, request, pk=None):
        with transaction.atomic():
            family = Families.objects.select_for_update().get(pk=pk)
            if family.status != self.FAMILY_STATUS_INITIAL:
                return Response(
                    {"error": "Initial approval is required first before final activation."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            agg = FamilyMembers.objects.filter(family=family).aggregate(
                pending=Count('pk', filter=Q(status=self.MEMBER_STATUS_PENDING)),
                accepted=Count('pk', filter=Q(status=self.MEMBER_STATUS_APPROVED)),
                rejected=Count('pk', filter=Q(status=self.MEMBER_STATUS_REJECTED))
            )
            pending_count = agg['pending']
            accepted_count = agg['accepted']
            rejected_count = agg['rejected']

            if pending_count > 0:
                return Response(
                    {
                        "error": "Cannot activate. There are members still pending review.",
                        "pending_members_count": pending_count,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            if accepted_count < family.min_limit:
                return Response(
                    {
                        "error": "Insufficient number of accepted members to activate the family.",
                        "accepted_members": accepted_count,
                        "rejected_members": rejected_count,
                        "required_minimum": family.min_limit,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            has_leader = FamilyMembers.objects.filter(
                family=family, status=self.MEMBER_STATUS_APPROVED, role='أخ أكبر'
            ).exists()
            if not has_leader:
                return Response(
                    {"error": "A security-approved family leader is required (Role: أخ أكبر)."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            def business_operation(admin, ip, _accepted_count=accepted_count):
                family.status = self.FAMILY_STATUS_ACTIVE
                family.approved_by = admin
                family.final_approved_at = timezone.now()
                family.save()
                return {
                    "message": "Family activated successfully.",
                    "family_id": family.family_id,
                    "accepted_members": _accepted_count,
                    "approved_by": admin.name,
                    "approval_date": family.final_approved_at.isoformat(),
                }

            result = self.execute_admin_action(
                request=request,
                action_name=f'الموافقة النهائية على الأسرة: {family.name}',
                target_type='اسر',
                business_operation=business_operation,
                family_id=family.family_id
            )
            return Response(result, status=status.HTTP_200_OK)
    # ----------------------------------------------------------------
    # Undo Helpers
    # ----------------------------------------------------------------
    def _undo_member_status(self, request, student_id, from_status, action_name, error_message, family):
        member, error = self._get_member_or_error(family, student_id)
        if error:
            return error

        if member.status != from_status:
            return Response(
                {"error": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )

        def business_operation(admin, ip):
            FamilyMembers.objects.filter(family=family, student_id=student_id).update(status=self.MEMBER_STATUS_PENDING)
            return {
                "message": "Member returned to pending list.",
                "member_id": student_id,
                "family_id": family.family_id,
            }

        result = self.execute_admin_action(
            request=request,
            action_name=action_name,
            target_type='اسر',
            business_operation=business_operation,
            family_id=family.family_id
        )
        return Response(result, status=status.HTTP_200_OK)
    # ----------------------------------------------------------------
    # Undo Actions
    # ----------------------------------------------------------------
    @extend_schema(
        description="Undo approval (return member to 'Pending' status) - Only allowed before final family activation.",
        request=None,
        responses={
            200: OpenApiResponse(description="Approval undone successfully"),
            400: OpenApiResponse(description="Cannot undo (family is active or member is not approved)"),
            404: OpenApiResponse(description="Member not found"),
        }
    )
    @action(detail=True, methods=['patch'], url_path=r'members/(?P<student_id>\d+)/undo-approve')
    def undo_approve_member(self, request, pk=None, student_id=None):
        with transaction.atomic():
            family = Families.objects.select_for_update().get(pk=pk)
            if family.status == self.FAMILY_STATUS_ACTIVE:
                return Response(
                    {"error": "Cannot undo approval because the family is fully activated. Use 'Remove Member' action instead."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return self._undo_member_status(
                request=request,
                student_id=student_id,
                from_status=self.MEMBER_STATUS_APPROVED,
                action_name=f'إلغاء موافقة على عضو الأسرة (رقم: {student_id})',
                error_message="Cannot undo approval. Member is not in 'Approved' status.",
                family=family
            )

    @extend_schema(
        description="Undo rejection (return member to 'Pending' status).",
        request=None,
        responses={
            200: OpenApiResponse(description="Rejection undone successfully"),
            400: OpenApiResponse(description="Member is not rejected"),
            404: OpenApiResponse(description="Member not found"),
        }
    )
    @action(detail=True, methods=['patch'], url_path=r'members/(?P<student_id>\d+)/undo-reject')
    def undo_reject_member(self, request, pk=None, student_id=None):
        with transaction.atomic():
            family = Families.objects.select_for_update().get(pk=pk)
            return self._undo_member_status(
                request=request,
                student_id=student_id,
                from_status=self.MEMBER_STATUS_REJECTED,
                action_name=f'إلغاء رفض عضو الأسرة (رقم: {student_id})',
                error_message="Cannot undo rejection. Member is not in 'Rejected' status.",
                family=family
            )