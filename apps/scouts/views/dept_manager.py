from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from ..serializers import (
    ClanOverviewSerializer,
    ClanDetailSerializer,
    GroupSerializer,
    ScoutMemberListSerializer,
    ScoutChangeRoleSerializer,
)
from ..utils import (
    get_clan_stats,
    get_clan_structure,
    success_response,
    error_response,
    SCOUT_LOG_ACTIONS,
    SCOUT_TARGET_TYPE,
)
from ..services.dept_manager_services import (
    ScoutValidationError,
    get_clan_or_error,
    get_member_or_error,
    get_accepted_member_or_error,
    require_field,
    get_all_clans,
    filter_serialized_clans,
    build_clans_summary,
    get_filtered_members,
    get_clan_groups,
    validate_clan_status,
    change_clan_status as svc_change_clan_status,
    validate_role_change,
    change_member_role as svc_change_member_role,
    remove_member as svc_remove_member,
)
from apps.accounts.permissions import IsRole, require_permission
from apps.accounts.utils import get_current_admin
from apps.accounts.mixins import AdminActionMixin


# ============================================
# Messages
# ============================================
MSG = {
    'clans_fetched': "تم جلب بيانات جميع العشائر بنجاح",
    'clan_fetched': "تم جلب بيانات العشيرة بنجاح",
    'members_fetched': "تم جلب قائمة الأعضاء بنجاح",
    'groups_fetched': "تم جلب رهوط العشيرة بنجاح",
    'structure_fetched': "تم جلب الهيكل الإداري بنجاح",
    'status_changed': "تم تغيير حالة العشيرة بنجاح",
    'role_changed': "تم تغيير دور العضو بنجاح",
    'member_removed': "تم إزالة العضو من العشيرة بنجاح",
}


@extend_schema(tags=["Dept Manager Scouts"])
class DeptManagerScoutViewSet(AdminActionMixin, ViewSet):
    """Dept manager scout management endpoints."""
    permission_classes = [IsRole]
    allowed_roles = ['مدير ادارة']

    # ==========================================
    # Helpers
    # ==========================================

    @property
    def current_admin(self):
        return get_current_admin(self.request)

    def _error(self, e):
        return Response(error_response(e.message), status=e.status_code)

    def _safe(self, fn):
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

    # ==========================================
    # Read-Only Monitoring (5)
    # ==========================================

    @extend_schema(tags=["Dept Manager Scouts"])
    @action(detail=False, methods=['get'])
    @require_permission('read')
    def clans(self, request):
        """List all clans with summary and filters"""
        clans = get_all_clans(request.query_params)
        serializer = ClanOverviewSerializer(clans, many=True)
        all_data = serializer.data

        summary = build_clans_summary(all_data)

        filtered_data = filter_serialized_clans(
            all_data, request.query_params
        )

        return Response(
            success_response(
                MSG['clans_fetched'],
                data={
                    'summary': summary,
                    'clans': filtered_data,
                }
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(tags=["Dept Manager Scouts"])
    @action(detail=False, methods=['get'])
    @require_permission('read')
    def clan_detail(self, request):
        """View full details of a specific clan"""
        result = self._safe(
            lambda: get_clan_or_error(
                request.query_params.get('clan_id')
            )
        )
        if isinstance(result, Response):
            return result
        clan = result

        return Response(
            success_response(
                MSG['clan_fetched'],
                data={
                    'clan': ClanDetailSerializer(clan).data,
                    'stats': get_clan_stats(clan),
                    'structure': get_clan_structure(clan),
                }
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(tags=["Dept Manager Scouts"])
    @action(detail=False, methods=['get'])
    @require_permission('read')
    def clan_members(self, request):
        """View all members of a specific clan with filters"""
        result = self._safe(
            lambda: get_clan_or_error(
                request.query_params.get('clan_id')
            )
        )
        if isinstance(result, Response):
            return result
        clan = result

        members = get_filtered_members(clan, request.query_params)

        return Response(
            success_response(
                MSG['members_fetched'],
                data=ScoutMemberListSerializer(members, many=True).data
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(tags=["Dept Manager Scouts"])
    @action(detail=False, methods=['get'])
    @require_permission('read')
    def clan_groups(self, request):
        """View all groups of a specific clan"""
        result = self._safe(
            lambda: get_clan_or_error(
                request.query_params.get('clan_id')
            )
        )
        if isinstance(result, Response):
            return result
        clan = result

        groups = get_clan_groups(clan)

        return Response(
            success_response(
                MSG['groups_fetched'],
                data=GroupSerializer(groups, many=True).data
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(tags=["Dept Manager Scouts"])
    @action(detail=False, methods=['get'])
    @require_permission('read')
    def clan_structure(self, request):
        """View the full administrative hierarchy of a clan"""
        result = self._safe(
            lambda: get_clan_or_error(
                request.query_params.get('clan_id')
            )
        )
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
    # Administrative Interventions (3)
    # ==========================================

    @extend_schema(tags=["Dept Manager Scouts"])
    @action(detail=False, methods=['post'])
    @require_permission('update')
    def change_clan_status(self, request):
        """Activate or deactivate a clan"""

        def _load():
            clan = get_clan_or_error(request.data.get('clan_id'))
            new_status = request.data.get('status')
            validate_clan_status(new_status)
            return clan, new_status

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        clan, new_status = result

        old_status = clan.status

        def business_fn(_, __):
            svc_change_clan_status(clan, new_status)

        self._log(
            request, SCOUT_LOG_ACTIONS['change_clan_status'], business_fn
        )

        return Response(
            success_response(
                MSG['status_changed'],
                data={
                    'clan_id': clan.clan_id,
                    'clan_name': clan.name,
                    'old_status': old_status,
                    'new_status': new_status,
                }
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(tags=["Dept Manager Scouts"])
    @action(detail=False, methods=['post'])
    @require_permission('update')
    def change_member_role(self, request):
        """Change a member's role (intervention)"""

        def _load():
            clan = get_clan_or_error(request.data.get('clan_id'))
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
                    "بيانات تغيير الدور غير صحيحة",
                    errors=serializer.errors
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
            svc_change_member_role(member, new_role)

        self._log(
            request, SCOUT_LOG_ACTIONS['change_role'],
            business_fn, member.student_id
        )

        return Response(
            success_response(
                MSG['role_changed'],
                data={
                    'member_id': member.scout_member_id,
                    'member_name': member.student.name,
                    'old_role': old_role,
                    'new_role': new_role,
                }
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(tags=["Dept Manager Scouts"])
    @action(detail=False, methods=['post'])
    @require_permission('delete')
    def remove_member(self, request):
        """Remove a member from a clan (permanent delete)"""

        def _load():
            clan = get_clan_or_error(request.data.get('clan_id'))
            member_id = require_field(request, 'member_id')
            member = get_member_or_error(member_id, clan)
            return member

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