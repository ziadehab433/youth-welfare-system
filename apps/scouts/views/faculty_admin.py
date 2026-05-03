from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from ..models import Clans, ScoutMembers
from ..serializers import (
    ClanSerializer,
    ClanCreateSerializer,
    ClanDetailSerializer,
    GroupSerializer,
    GroupCreateSerializer,
    ScoutMemberListSerializer,
    ScoutReviewSerializer,
    ScoutChangeRoleSerializer,
    ScoutAddByNidSerializer,
)
from ..utils import (
    get_clan_stats,
    get_clan_structure,
    success_response,
    error_response,
    SCOUT_LOG_ACTIONS,
    SCOUT_TARGET_TYPE,
    STATUS_ACCEPTED,
    STATUS_REJECTED,
    MEMBER_ROLE,
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
    change_member_role as svc_change_member_role,
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
# Messages
# ============================================
MSG = {
    'clan_fetched': "تم جلب بيانات العشيرة بنجاح",
    'clan_created': "تم إنشاء العشيرة بنجاح",
    'clan_updated': "تم تعديل بيانات العشيرة بنجاح",
    'clan_exists': "هذه الكلية لديها عشيرة بالفعل",
    'structure_fetched': "تم جلب الهيكل الإداري بنجاح",
    'groups_fetched': "تم جلب الرهوط بنجاح",
    'group_created': "تم إنشاء الرهط بنجاح",
    'group_updated': "تم تعديل الرهط بنجاح",
    'group_deleted': "تم حذف الرهط بنجاح",
    'members_fetched': "تم جلب قائمة الأعضاء بنجاح",
    'invalid_data': "بيانات غير صحيحة",
    'already_in_group': "العضو موجود بالفعل في هذا الرهط",
}

# ============================================
# Shared OpenAPI Parameters
# ============================================
ALL_ROLES_ENUM = [r[0] for r in ScoutMembers.ROLE_CHOICES]

PARAM_MEMBER_STATUS_FILTER = OpenApiParameter(
    name='status',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    enum=['منتظر', 'مقبول', 'مرفوض'],
    description='فلترة حسب حالة العضو',
)

PARAM_MEMBER_ROLE_FILTER = OpenApiParameter(
    name='role',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    enum=ALL_ROLES_ENUM,
    description='فلترة حسب دور العضو',
)

PARAM_GROUP_ID_FILTER = OpenApiParameter(
    name='group_id',
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description='فلترة حسب الرهط',
)

PARAM_UNASSIGNED_FILTER = OpenApiParameter(
    name='unassigned',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    enum=['true', 'false'],
    description='عرض الأعضاء الغير موزعين فقط',
)


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
                error_response(MSG['clan_exists']),
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        data['faculty'] = admin.faculty_id

        serializer = ClanCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                error_response(MSG['invalid_data'], errors=serializer.errors),
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
        tags=["Scouts - Faculty Admin"],
        parameters=[
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='اسم العشيرة الجديد',
            ),
            OpenApiParameter(
                name='description',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='وصف العشيرة الجديد',
            ),
        ],
        request=None,
    )
    @action(detail=False, methods=['put'])
    @require_permission('update')
    def update_clan(self, request):
        """Update clan info (name, description only)"""
        admin = self.current_admin
        result = self._safe(lambda: get_clan_or_error(admin))
        if isinstance(result, Response):
            return result
        clan = result

        def _get(key):
            return request.query_params.get(key) or request.data.get(key)

        update_data = {}
        for key in ['name', 'description']:
            val = _get(key)
            if val is not None:
                update_data[key] = val

        if not update_data:
            return Response(
                error_response("يجب تحديد حقل واحد على الأقل للتعديل"),
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ClanSerializer(clan, data=update_data, partial=True)
        if not serializer.is_valid():
            return Response(
                error_response(MSG['invalid_data'], errors=serializer.errors),
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
                error_response(MSG['invalid_data'], errors=serializer.errors),
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
        tags=["Scouts - Faculty Admin"],
        parameters=[
            OpenApiParameter(
                name='group_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='رقم الرهط',
            ),
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='اسم الرهط الجديد',
            ),
            OpenApiParameter(
                name='display_order',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description='ترتيب العرض الجديد',
            ),
        ],
        request=None,
    )
    @action(detail=False, methods=['put'])
    @require_permission('update')
    def update_group(self, request):
        """Update group name or display order"""
        admin = self.current_admin

        def _load():
            clan = get_clan_or_error(admin)
            group_id = request.query_params.get('group_id') or request.data.get('group_id')
            group = get_group_or_error(group_id, clan)
            return clan, group

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        clan, group = result

        update_data = {}
        for key in ['name', 'display_order']:
            val = request.query_params.get(key) or request.data.get(key)
            if val is not None:
                update_data[key] = val

        serializer = GroupSerializer(group, data=update_data, partial=True)
        if not serializer.is_valid():
            return Response(
                error_response(MSG['invalid_data'], errors=serializer.errors),
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
        tags=["Scouts - Faculty Admin"],
        parameters=[
            OpenApiParameter(
                name='group_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='رقم الرهط المراد حذفه',
            ),
        ],
        request=None,
    )
    @action(detail=False, methods=['delete'])
    @require_permission('delete')
    def delete_group(self, request):
        """Delete a group — members become unassigned"""
        admin = self.current_admin

        def _load():
            clan = get_clan_or_error(admin)
            group_id = request.query_params.get('group_id') or request.data.get('group_id')
            group = get_group_or_error(group_id, clan)
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
                    'message': f"تم إلغاء توزيع {affected} عضو"
                }
            ),
            status=status.HTTP_200_OK
        )

    # ==========================================
    # Member Management
    # ==========================================

    @extend_schema(
        tags=["Scouts - Faculty Admin"],
        parameters=[
            PARAM_MEMBER_STATUS_FILTER,
            PARAM_MEMBER_ROLE_FILTER,
            PARAM_GROUP_ID_FILTER,
            PARAM_UNASSIGNED_FILTER,
        ],
    )
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
        tags=["Scouts - Faculty Admin"],
        parameters=[
            OpenApiParameter(
                name='member_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='رقم العضو',
            ),
            OpenApiParameter(
                name='action',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                enum=['قبول', 'رفض'],
                description='قبول أو رفض',
            ),
            OpenApiParameter(
                name='rejection_reason',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='سبب الرفض (مطلوب عند الرفض)',
            ),
        ],
        request=None,
    )
    @action(detail=False, methods=['post'])
    @require_permission('update')
    def review_member(self, request):
        """Approve or reject a pending join request"""
        admin = self.current_admin

        def _get(key):
            return request.query_params.get(key) or request.data.get(key)

        def _load():
            clan = get_clan_or_error(admin)
            member_id = _get('member_id')
            if not member_id:
                raise ScoutValidationError("يجب تحديد member_id")
            member = get_member_or_error(member_id, clan)
            return member

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        member = result

        raw_action = _get('action')
        action_map = {
            'قبول': 'approve',
            'رفض': 'reject',
            'approve': 'approve',
            'reject': 'reject',
        }
        action_type = action_map.get(raw_action)
        if not action_type:
            return Response(
                error_response("يجب اختيار 'قبول' أو 'رفض'"),
                status=status.HTTP_400_BAD_REQUEST
            )

        rejection_reason = _get('rejection_reason') or ''

        if action_type == 'reject' and not rejection_reason.strip():
            return Response(
                error_response("يجب كتابة سبب الرفض"),
                status=status.HTTP_400_BAD_REQUEST
            )

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
                    data=self._member_data(member, status=STATUS_ACCEPTED)
                ),
                status=status.HTTP_200_OK
            )

        return Response(
            success_response(
                f"تم رفض طلب {member.student.name}",
                data=self._member_data(
                    member, status=STATUS_REJECTED, reason=rejection_reason
                )
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        tags=["Scouts - Faculty Admin"],
        parameters=[
            OpenApiParameter(
                name='member_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='رقم العضو',
            ),
            OpenApiParameter(
                name='group_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='رقم الرهط',
            ),
        ],
        request=None,
    )
    @action(detail=False, methods=['post'])
    @require_permission('update')
    def assign_group(self, request):
        """Assign an accepted member to a group"""
        admin = self.current_admin

        def _get(key):
            return request.query_params.get(key) or request.data.get(key)

        def _load():
            clan = get_clan_or_error(admin)
            member_id = _get('member_id')
            group_id = _get('group_id')
            if not member_id:
                raise ScoutValidationError("يجب تحديد member_id")
            if not group_id:
                raise ScoutValidationError("يجب تحديد group_id")
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
        tags=["Scouts - Faculty Admin"],
        parameters=[
            OpenApiParameter(
                name='member_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='رقم العضو',
            ),
            OpenApiParameter(
                name='role',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                enum=ALL_ROLES_ENUM,
                description='الدور الجديد',
            ),
        ],
        request=None,
    )
    @action(detail=False, methods=['post'])
    @require_permission('update')
    def change_role(self, request):
        """Change an accepted member's role"""
        admin = self.current_admin

        def _get(key):
            return request.query_params.get(key) or request.data.get(key)

        def _load():
            clan = get_clan_or_error(admin)
            member_id = _get('member_id')
            if not member_id:
                raise ScoutValidationError("يجب تحديد member_id")
            member = get_accepted_member_or_error(member_id, clan)
            return clan, member

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        clan, member = result

        new_role = _get('role')
        if not new_role:
            return Response(
                error_response("يجب تحديد الدور الجديد"),
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ScoutChangeRoleSerializer(
            data={'role': new_role}, context={'member': member}
        )
        if not serializer.is_valid():
            return Response(
                error_response(MSG['invalid_data'], errors=serializer.errors),
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
                f"تم تغيير دور {member.student.name} بنجاح",
                data=self._member_data(
                    member, old_role=old_role, new_role=new_role
                )
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        tags=["Scouts - Faculty Admin"],
        parameters=[
            OpenApiParameter(
                name='member_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='رقم العضو',
            ),
            OpenApiParameter(
                name='group_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='رقم الرهط الجديد',
            ),
        ],
        request=None,
    )
    @action(detail=False, methods=['post'])
    @require_permission('update')
    def transfer_member(self, request):
        """Transfer member between groups — group leaders reset to عضو"""
        admin = self.current_admin

        def _get(key):
            return request.query_params.get(key) or request.data.get(key)

        def _load():
            clan = get_clan_or_error(admin)
            member_id = _get('member_id')
            group_id = _get('group_id')
            if not member_id:
                raise ScoutValidationError("يجب تحديد member_id")
            if not group_id:
                raise ScoutValidationError("يجب تحديد group_id")
            member = get_accepted_member_or_error(member_id, clan)
            new_group = get_group_or_error(group_id, clan)
            return member, new_group

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        member, new_group = result

        if member.group_id and member.group_id == new_group.group_id:
            return Response(
                error_response(MSG['already_in_group']),
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
                'new_role': MEMBER_ROLE,
                'note': f"تم إعادة الدور من {transfer_info['old_role']} إلى {MEMBER_ROLE} بسبب النقل",
            })

        return Response(
            success_response(
                f"تم نقل {member.student.name} من {old_group_name} إلى {new_group.name}",
                data=response_data
            ),
            status=status.HTTP_200_OK
        )

    @extend_schema(
        tags=["Scouts - Faculty Admin"],
        parameters=[
            OpenApiParameter(
                name='member_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='رقم العضو المراد إزالته',
            ),
        ],
        request=None,
    )
    @action(detail=False, methods=['delete'])
    @require_permission('delete')
    def remove_member(self, request):
        """Remove (kick) a member — permanent delete"""
        admin = self.current_admin

        def _get(key):
            return request.query_params.get(key) or request.data.get(key)

        def _load():
            clan = get_clan_or_error(admin)
            member_id = _get('member_id')
            if not member_id:
                raise ScoutValidationError("يجب تحديد member_id")
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
        tags=["Scouts - Faculty Admin"],
        parameters=[
            OpenApiParameter(
                name='nid',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description='الرقم القومي للطالب',
            ),
        ],
        request=None,
    )
    @action(detail=False, methods=['post'])
    @require_permission('create')
    def add_by_nid(self, request):
        """Add student directly by national ID — enters as accepted عضو"""
        admin = self.current_admin

        def _get(key):
            return request.query_params.get(key) or request.data.get(key)

        def _load():
            clan = get_clan_or_error(admin)
            nid = _get('nid')
            if not nid:
                raise ScoutValidationError("يجب تحديد الرقم القومي")
            student, existing = add_student_by_nid(nid, clan)
            return clan, student, existing

        result = self._safe(_load)
        if isinstance(result, Response):
            return result
        clan, student, existing = result

        if existing and existing.status == STATUS_REJECTED:
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
                        'status': STATUS_ACCEPTED,
                        'was_rejected': True,
                    }
                ),
                status=status.HTTP_201_CREATED
            )

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
                    'status': STATUS_ACCEPTED,
                    'was_rejected': False,
                }
            ),
            status=status.HTTP_201_CREATED
        )