import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse

from apps.family.models import Families, FamilyMembers, Students
from apps.accounts.permissions import IsRole, require_permission
from apps.accounts.utils import get_current_admin
from apps.accounts.mixins import AdminActionMixin

logger = logging.getLogger(__name__)

STATUS_APPROVED = 'مقبول'
ROLE_MEMBER = 'عضو'


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