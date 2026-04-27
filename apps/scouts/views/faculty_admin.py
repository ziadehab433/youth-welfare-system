from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from ..models import Clans
from ..serializers import (
    ClanSerializer,
    ClanCreateSerializer,
    ClanDetailSerializer,
    GroupSerializer,
    GroupCreateSerializer,
    GroupUpdateRequestSerializer,
    GroupDeleteRequestSerializer,
    ScoutMemberListSerializer,
    ScoutReviewSerializer,
    ScoutChangeRoleSerializer,
    ScoutAddByNidSerializer,
    ReviewMemberRequestSerializer,
    AssignGroupRequestSerializer,
    ChangeRoleRequestSerializer,
    TransferMemberRequestSerializer,
    RemoveMemberRequestSerializer,
)
from ..utils import (
    get_clan_stats,
    get_clan_structure,
    success_response,
    error_response,
    SCOUT_LOG_ACTIONS,
    SCOUT_TARGET_TYPE,
)
from ..services.faculty_services import (
    ScoutValidationError,
    get_clan_or_error,
    get_member_or_error,
    get_accepted_member_or_error,
    get_group_or_error,
    require_field,
    create_clan as svc_create_clan,
    update_clan as svc_update_clan,
    create_group as svc_create_group,
    update_group as svc_update_group,
    delete_group as svc_delete_group,
    get_filtered_members,
    review_member as svc_review_member,
    assign_member_to_group,
    validate_role_change,
    change_member_role,
    transfer_member as svc_transfer_member,
    remove_member as svc_remove_member,
    add_student_by_nid,
    reactivate_rejected_member,
    create_member_directly,
)
from apps.accounts.permissions import IsRole, require_permission
from apps.accounts.utils import get_current_admin
from apps.accounts.mixins import AdminActionMixin


# ============================================
# Success Messages
# ============================================
MSG = {
    'clan_fetched': "تم جلب بيانات العشيرة بنجاح",
    'clan_created': "تم إنشاء العشيرة بنجاح",
    'clan_updated': "تم تعديل بيانات العشيرة بنجاح",
    'structure_fetched': "تم جلب الهيكل الإداري بنجاح",
    'groups_fetched': "تم جلب الرهوط بنجاح",
    'group_created': "تم إنشاء الرهط بنجاح",
    'group_updated': "تم تعديل الرهط بنجاح",
    'group_deleted': "تم حذف الرهط بنجاح",
    'members_fetched': "تم جلب قائمة الأعضاء بنجاح",
}


@extend_schema(tags=["Scouts - Faculty Admin"])
class FacultyAdminScoutViewSet(AdminActionMixin, ViewSet):
    """Faculty admin scout management endpoints."""
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية']

    # ==========================================
    # Helpers
    # ==========================================

    @property
    def current_admin(self):
        return get_current_admin(self.request)

    def _error(self, e):
        return Response(error_response(e.message), status=e.status_code)

    def _safe(self, fn):
        """Execute fn, return result or error Response"""
        try:
            return fn()
        except ScoutValidationError as e:
            return self._error(e)

    def _log(self, request, action_name, business_fn, student_id=None):
        return self.execute_admin_action(
            request=request,
            action_name=action_name,
            target_type=SCOUT_TARGET_TYPE,
            business_operation=business_fn,
            student_id=student_id,
        )

    def _member_data(self, member, **extra):
        """Standard member response data"""
        data = {
            'member_id': member.scout_member_id,
            'student_name': member.student.name,
        }
        data.update(extra)
        return data

    # ==========================================
    # Clan Management
    # ==========================================

    @extend_schema(tags=["Scouts - Faculty Admin"])
    @action(detail=False, methods=['get'])
    @require_permission('read')
    def clan(self, request):
        """View clan with full details and stats"""
        admin = self.current_admin
        result = self._safe(lambda: get_clan_or_error(admin))
        if isinstance(result, Response):
            return result
        clan = result

        return Response(
            success_response(
                MSG['clan_fetched'],
                data={
                    'clan': ClanDetailSerializer(clan).data,
                    'stats': get_clan_stats(clan),
                }
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ClanCreateSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['post'])
    @require_permission('create')
    def create_clan(self, request):
        """Create a new clan for the faculty"""
        admin = self.current_admin

        if Clans.objects.filter(faculty_id=admin.faculty_id).exists():
            return Response(
                error_response("This faculty already has a clan"),
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        data['faculty'] = admin.faculty_id

        serializer = ClanCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                error_response("Invalid clan data", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        def business_fn(admin_obj, _):
            return svc_create_clan(serializer, admin_obj)

        clan = self._log(request, SCOUT_LOG_ACTIONS['create_clan'], business_fn)

        return Response(
            success_response(
                MSG['clan_created'],
                data=ClanSerializer(clan).data
            ),
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        request=ClanSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['put'])
    @require_permission('update')
    def update_clan(self, request):
        """Update clan info (name, description)"""
        admin = self.current_admin
        result = self._safe(lambda: get_clan_or_error(admin))
        if isinstance(result, Response):
            return result
        clan = result

        serializer = ClanSerializer(clan, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                error_response("Invalid update data", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        def business_fn(_, __):
            return svc_update_clan(serializer)

        self._log(request, SCOUT_LOG_ACTIONS['update_clan'], business_fn)

        return Response(
            success_response(MSG['clan_updated'], data=serializer.data),
            status=status.HTTP_200_OK
        )

    @extend_schema(tags=["Scouts - Faculty Admin"])
    @action(detail=False, methods=['get'])
    @require_permission('read')
    def structure(self, request):
        """View the full administrative hierarchy"""
        admin = self.current_admin
        result = self._safe(lambda: get_clan_or_error(admin))
        if isinstance(result, Response):
            return result
        clan = result

        return Response(
            success_response(
                MSG['structure_fetched'],
                data=get_clan_structure(clan)
            ),
            status=status.HTTP_200_OK
        )

    # ==========================================
    # Group Management
    # ==========================================

    @extend_schema(tags=["Scouts - Faculty Admin"])
    @action(detail=False, methods=['get'])
    @require_permission('read')
    def groups(self, request):
        """List all groups in the clan"""
        admin = self.current_admin
        result = self._safe(lambda: get_clan_or_error(admin))
        if isinstance(result, Response):
            return result
        clan = result

        groups = clan.groups.all().order_by('display_order')

        return Response(
            success_response(
                MSG['groups_fetched'],
                data=GroupSerializer(groups, many=True).data
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=GroupCreateSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['post'])
    @require_permission('create')
    def create_group(self, request):
        """Create a new group in the clan"""
        admin = self.current_admin
        result = self._safe(lambda: get_clan_or_error(admin))
        if isinstance(result, Response):
            return result
        clan = result

        data = request.data.copy()
        data['clan'] = clan.clan_id

        serializer = GroupCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                error_response("Invalid group data", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        def business_fn(_, __):
            return svc_create_group(serializer)

        group = self._log(
            request, SCOUT_LOG_ACTIONS['create_group'], business_fn
        )

        return Response(
            success_response(
                MSG['group_created'],
                data=GroupSerializer(group).data
            ),
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        request=GroupUpdateRequestSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['put'])
    @require_permission('update')
    def update_group(self, request):
        """Update group name or display order"""
        admin = self.current_admin

        def _load():
            clan = get_clan_or_error(admin)
            group = get_group_or_error(request.data.get('group_id'), clan)
            return clan, group

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        clan, group = result

        serializer = GroupSerializer(group, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                error_response("Invalid update data", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        def business_fn(_, __):
            return svc_update_group(serializer)

        self._log(request, SCOUT_LOG_ACTIONS['update_group'], business_fn)

        return Response(
            success_response(MSG['group_updated'], data=serializer.data),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=GroupDeleteRequestSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['post'])
    @require_permission('delete')
    def delete_group(self, request):
        """Delete a group — members become unassigned"""
        admin = self.current_admin

        def _load():
            clan = get_clan_or_error(admin)
            group = get_group_or_error(request.data.get('group_id'), clan)
            return clan, group

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        _, group = result

        affected = None

        def business_fn(_, __):
            nonlocal affected
            affected = svc_delete_group(group)

        self._log(request, SCOUT_LOG_ACTIONS['delete_group'], business_fn)

        return Response(
            success_response(
                MSG['group_deleted'],
                data={
                    'affected_members': affected,
                    'message': f"{affected} members became unassigned"
                }
            ),
            status=status.HTTP_200_OK
        )

    # ==========================================
    # Member Management
    # ==========================================

    @extend_schema(tags=["Scouts - Faculty Admin"])
    @action(detail=False, methods=['get'])
    @require_permission('read')
    def members(self, request):
        """List all members — filters: status, role, group_id, unassigned"""
        admin = self.current_admin
        result = self._safe(lambda: get_clan_or_error(admin))
        if isinstance(result, Response):
            return result
        clan = result

        members, total = get_filtered_members(clan, request.query_params)

        return Response(
            success_response(
                MSG['members_fetched'],
                data={
                    'count': total,
                    'members': ScoutMemberListSerializer(
                        members, many=True
                    ).data,
                }
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ReviewMemberRequestSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['post'])
    @require_permission('update')
    def review_member(self, request):
        """Approve or reject a pending join request"""
        admin = self.current_admin

        def _load():
            clan = get_clan_or_error(admin)
            member_id = require_field(request, 'member_id')
            member = get_member_or_error(member_id, clan)
            return member

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        member = result

        serializer = ScoutReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                error_response("Invalid review data", errors=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        action_type = serializer.validated_data['action']
        rejection_reason = serializer.validated_data.get('rejection_reason')

        def business_fn(admin_obj, _):
            svc_review_member(
                member, action_type, rejection_reason, admin_obj.admin_id
            )

        log_key = (
            'approve_member' if action_type == 'approve' else 'reject_member'
        )

        review_result = self._safe(
            lambda: self._log(
                request, SCOUT_LOG_ACTIONS[log_key],
                business_fn, member.student_id
            )
        )
        if isinstance(review_result, Response):
            return review_result

        if action_type == 'approve':
            return Response(
                success_response(
                    f"تم قبول {member.student.name} في العشيرة بنجاح",
                    data=self._member_data(member, status='مقبول')
                ),
                status=status.HTTP_200_OK
            )

        return Response(
            success_response(
                f"تم رفض طلب {member.student.name}",
                data=self._member_data(
                    member, status='مرفوض', reason=rejection_reason
                )
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=AssignGroupRequestSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['post'])
    @require_permission('update')
    def assign_group(self, request):
        """Assign an accepted member to a group"""
        admin = self.current_admin

        def _load():
            clan = get_clan_or_error(admin)
            member_id = require_field(request, 'member_id')
            group_id = require_field(request, 'group_id')
            member = get_accepted_member_or_error(member_id, clan)
            group = get_group_or_error(group_id, clan)
            return member, group

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        member, group = result

        def business_fn(_, __):
            assign_member_to_group(member, group)

        self._log(
            request, SCOUT_LOG_ACTIONS['assign_group'],
            business_fn, member.student_id
        )

        return Response(
            success_response(
                f"تم توزيع {member.student.name} على رهط {group.name}",
                data=self._member_data(
                    member,
                    group_id=group.group_id,
                    group_name=group.name,
                )
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ChangeRoleRequestSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['post'])
    @require_permission('update')
    def change_role(self, request):
        """Change an accepted member's role"""
        admin = self.current_admin

        def _load():
            clan = get_clan_or_error(admin)
            member_id = require_field(request, 'member_id')
            member = get_accepted_member_or_error(member_id, clan)
            return clan, member

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        clan, member = result

        serializer = ScoutChangeRoleSerializer(
            data=request.data, context={'member': member}
        )
        if not serializer.is_valid():
            return Response(
                error_response(
                    "Invalid role change data", errors=serializer.errors
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        new_role = serializer.validated_data['role']

        validation = self._safe(
            lambda: validate_role_change(member, new_role, clan)
        )
        if isinstance(validation, Response):
            return validation

        old_role = member.role

        def business_fn(_, __):
            change_member_role(member, new_role)

        self._log(
            request, SCOUT_LOG_ACTIONS['change_role'],
            business_fn, member.student_id
        )

        return Response(
            success_response(
                f"تم تغيير دور {member.student.name} بنجاح",
                data=self._member_data(
                    member, old_role=old_role, new_role=new_role
                )
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=TransferMemberRequestSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['post'])
    @require_permission('update')
    def transfer_member(self, request):
        """Transfer member between groups — group leaders reset to MEMBER"""
        admin = self.current_admin

        def _load():
            clan = get_clan_or_error(admin)
            member_id = require_field(request, 'member_id')
            group_id = require_field(request, 'group_id')
            member = get_accepted_member_or_error(member_id, clan)
            new_group = get_group_or_error(group_id, clan)
            return member, new_group

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        member, new_group = result

        if member.group_id and member.group_id == new_group.group_id:
            return Response(
                error_response("Member is already in this group"),
                status=status.HTTP_400_BAD_REQUEST
            )

        old_group_name = member.group.name if member.group else "غير محدد"
        transfer_info = {}

        def business_fn(_, __):
            nonlocal transfer_info
            role_was_reset, old_role = svc_transfer_member(member, new_group)
            transfer_info = {
                'role_was_reset': role_was_reset,
                'old_role': old_role,
            }

        self._log(
            request, SCOUT_LOG_ACTIONS['transfer_member'],
            business_fn, member.student_id
        )

        response_data = self._member_data(
            member,
            from_group=old_group_name,
            to_group=new_group.name,
        )

        if transfer_info.get('role_was_reset'):
            response_data.update({
                'role_reset': True,
                'old_role': transfer_info['old_role'],
                'new_role': 'MEMBER',
                'note': (
                    f"Role reset from {transfer_info['old_role']} "
                    f"to MEMBER due to transfer"
                ),
            })

        return Response(
            success_response(
                f"تم نقل {member.student.name} "
                f"من {old_group_name} إلى {new_group.name}",
                data=response_data
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=RemoveMemberRequestSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['post'])
    @require_permission('delete')
    def remove_member(self, request):
        """Remove (kick) a member — permanent delete"""
        admin = self.current_admin

        def _load():
            clan = get_clan_or_error(admin)
            member_id = require_field(request, 'member_id')
            return get_member_or_error(member_id, clan)

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        member = result

        removal = {}

        def business_fn(_, __):
            nonlocal removal
            removal = svc_remove_member(member)

        self._log(
            request, SCOUT_LOG_ACTIONS['remove_member'],
            business_fn, member.student_id
        )

        return Response(
            success_response(
                f"تم إزالة {removal['name']} من العشيرة نهائياً",
                data={
                    'removed_member': removal['name'],
                    'was_role': removal['role'],
                    'can_reapply': True,
                }
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ScoutAddByNidSerializer,
        tags=["Scouts - Faculty Admin"],
    )
    @action(detail=False, methods=['post'])
    @require_permission('create')
    def add_by_nid(self, request):
        """Add student directly by national ID — enters as accepted MEMBER"""
        admin = self.current_admin

        def _load():
            clan = get_clan_or_error(admin)
            nid = require_field(request, 'nid')
            student, existing = add_student_by_nid(nid, clan)
            return clan, student, existing

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        clan, student, existing = result

        # Re-activate rejected
        if existing and existing.status == 'مرفوض':
            def business_fn(admin_obj, _):
                reactivate_rejected_member(existing, admin_obj.admin_id)

            self._log(
                request, SCOUT_LOG_ACTIONS['add_by_nid'],
                business_fn, student.student_id
            )

            return Response(
                success_response(
                    f"تم إعادة قبول {student.name} في العشيرة",
                    data={
                        'student_name': student.name,
                        'status': 'مقبول',
                        'was_rejected': True,
                    }
                ),
                status=status.HTTP_201_CREATED
            )

        # New member
        def business_fn(admin_obj, _):
            create_member_directly(student, clan, admin_obj.admin_id)

        self._log(
            request, SCOUT_LOG_ACTIONS['add_by_nid'],
            business_fn, student.student_id
        )

        return Response(
            success_response(
                f"تم إضافة {student.name} إلى العشيرة كعضو مقبول",
                data={
                    'student_name': student.name,
                    'status': 'مقبول',
                    'was_rejected': False,
                }
            ),
            status=status.HTTP_201_CREATED
        )