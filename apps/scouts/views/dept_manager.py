from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from drf_spectacular.utils import extend_schema

from ..models import Clans, ClanGroups, ScoutMembers
from ..serializers import (
    ClanOverviewSerializer,
    ClanDetailSerializer,
    GroupSerializer,
    ScoutMemberListSerializer,
    ScoutChangeRoleSerializer,
)
from ..utils import (
    is_dept_manager,
    get_clan_or_404,
    get_member_or_404,
    validate_member_belongs_to_clan,
    validate_member_is_accepted,
    validate_single_leadership_role,
    validate_unique_role,
    get_clan_stats,
    get_clan_structure,
    success_response,
    error_response,
    SCOUT_LOG_ACTIONS,
    SCOUT_TARGET_TYPE,
)
from apps.accounts.mixins import AdminActionMixin

@extend_schema(tags=["Dept Manager Scouts"])
class DeptManagerScoutViewSet(ViewSet, AdminActionMixin):
    """
    Dept manager scout endpoints with logging.
    """

    # ==========================================
    # Read-Only Monitoring
    # ==========================================

    # GET /scouts/dept/clans/
    @action(detail=False, methods=['get'])
    def clans(self, request):
        """List all clans with monitoring data and summary"""
        try:
            admin = request.user_data
            is_dept_manager(admin)

            clans = Clans.objects.select_related(
                'faculty'
            ).all().order_by('name')

            filter_status = request.query_params.get('status')
            if filter_status:
                clans = clans.filter(status=filter_status)

            serializer = ClanOverviewSerializer(clans, many=True)
            data = serializer.data

            meets_min = request.query_params.get('meets_minimum')
            if meets_min == 'true':
                data = [c for c in data if c['meets_minimum']]
            elif meets_min == 'false':
                data = [c for c in data if not c['meets_minimum']]

            structure_filter = request.query_params.get('structure_complete')
            if structure_filter == 'true':
                data = [c for c in data if c['is_structure_complete']]
            elif structure_filter == 'false':
                data = [c for c in data if not c['is_structure_complete']]

            summary = {
                'total_clans': len(serializer.data),
                'active_clans': len([c for c in serializer.data if c['status'] == 'active']),
                'total_members': sum(c['members_count'] for c in serializer.data),
                'total_accepted': sum(c['accepted_count'] for c in serializer.data),
                'total_pending': sum(c['pending_count'] for c in serializer.data),
            }

            return Response(
                success_response(
                    "تم جلب بيانات جميع العشائر بنجاح",
                    data={
                        'summary': summary,
                        'clans': data,
                    }
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء جلب بيانات العشائر"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # GET /scouts/dept/clan_detail/?clan_id=1
    @action(detail=False, methods=['get'])
    def clan_detail(self, request):
        """View full details of a specific clan"""
        try:
            admin = request.user_data
            is_dept_manager(admin)

            clan_id = request.query_params.get('clan_id')
            if not clan_id:
                return Response(
                    error_response("يجب تحديد رقم العشيرة"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            clan = get_clan_or_404(clan_id)
            serializer = ClanDetailSerializer(clan)
            stats = get_clan_stats(clan)
            structure = get_clan_structure(clan)

            return Response(
                success_response(
                    "تم جلب بيانات العشيرة بنجاح",
                    data={
                        'clan': serializer.data,
                        'stats': stats,
                        'structure': structure,
                    }
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء جلب بيانات العشيرة"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # GET /scouts/dept/clan_members/?clan_id=1
    @action(detail=False, methods=['get'])
    def clan_members(self, request):
        """View all members of a specific clan"""
        try:
            admin = request.user_data
            is_dept_manager(admin)

            clan_id = request.query_params.get('clan_id')
            if not clan_id:
                return Response(
                    error_response("يجب تحديد رقم العشيرة"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            clan = get_clan_or_404(clan_id)

            members = clan.members.select_related(
                'student', 'group'
            ).all()

            filter_status = request.query_params.get('status')
            if filter_status:
                members = members.filter(status=filter_status)

            filter_role = request.query_params.get('role')
            if filter_role:
                members = members.filter(role=filter_role)

            members = members.order_by('-created_at')
            serializer = ScoutMemberListSerializer(members, many=True)

            return Response(
                success_response(
                    "تم جلب قائمة الأعضاء بنجاح",
                    data=serializer.data
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء جلب قائمة الأعضاء"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # GET /scouts/dept/clan_groups/?clan_id=1
    @action(detail=False, methods=['get'])
    def clan_groups(self, request):
        """View all groups of a specific clan"""
        try:
            admin = request.user_data
            is_dept_manager(admin)

            clan_id = request.query_params.get('clan_id')
            if not clan_id:
                return Response(
                    error_response("يجب تحديد رقم العشيرة"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            clan = get_clan_or_404(clan_id)
            groups = clan.groups.all().order_by('display_order')
            serializer = GroupSerializer(groups, many=True)

            return Response(
                success_response(
                    "تم جلب رهوط العشيرة بنجاح",
                    data=serializer.data
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء جلب الرهوط"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # GET /scouts/dept/clan_structure/?clan_id=1
    @action(detail=False, methods=['get'])
    def clan_structure(self, request):
        """View the full administrative hierarchy of a clan"""
        try:
            admin = request.user_data
            is_dept_manager(admin)

            clan_id = request.query_params.get('clan_id')
            if not clan_id:
                return Response(
                    error_response("يجب تحديد رقم العشيرة"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            clan = get_clan_or_404(clan_id)
            structure = get_clan_structure(clan)

            return Response(
                success_response(
                    "تم جلب الهيكل الإداري بنجاح",
                    data=structure
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء جلب الهيكل الإداري"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==========================================
    # Administrative Interventions (with Logs)
    # ==========================================

    # POST /scouts/dept/change_clan_status/
    @action(detail=False, methods=['post'])
    def change_clan_status(self, request):
        """Activate or deactivate a clan"""
        try:
            admin = request.user_data
            is_dept_manager(admin)

            clan_id = request.data.get('clan_id')
            if not clan_id:
                return Response(
                    error_response("يجب تحديد رقم العشيرة"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            clan = get_clan_or_404(clan_id)

            new_status = request.data.get('status')
            if new_status not in ['active', 'inactive']:
                return Response(
                    error_response("حالة العشيرة يجب أن تكون 'active' أو 'inactive'"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            old_status = clan.status

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    clan.status = new_status
                    clan.updated_at = timezone.now()
                    clan.save()

            self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['change_clan_status'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
            )

            return Response(
                success_response(
                    "تم تغيير حالة العشيرة بنجاح",
                    data={
                        'clan_id': clan.clan_id,
                        'clan_name': clan.name,
                        'old_status': old_status,
                        'new_status': new_status,
                    }
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء تغيير حالة العشيرة"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # POST /scouts/dept/change_member_role/
    @action(detail=False, methods=['post'])
    def change_member_role(self, request):
        """Change a member's role (intervention)"""
        try:
            admin = request.user_data
            is_dept_manager(admin)

            clan_id = request.data.get('clan_id')
            member_id = request.data.get('member_id')

            if not clan_id or not member_id:
                return Response(
                    error_response("يجب تحديد رقم العشيرة ورقم العضو"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            clan = get_clan_or_404(clan_id)
            member = get_member_or_404(member_id)
            validate_member_belongs_to_clan(member, clan)
            validate_member_is_accepted(member)

            serializer = ScoutChangeRoleSerializer(
                data=request.data,
                context={'member': member}
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

            validate_unique_role(
                clan=clan,
                role=new_role,
                group=member.group,
                exclude_member_id=member.scout_member_id
            )
            validate_single_leadership_role(member, new_role, clan)
            old_role = member.role

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    member.role = new_role
                    member.updated_at = timezone.now()
                    member.save()

            self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['change_role'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
                student_id=member.student_id,
            )

            return Response(
                success_response(
                    "تم تغيير دور العضو بنجاح",
                    data={
                        'member_id': member.scout_member_id,
                        'member_name': member.student.name,
                        'old_role': old_role,
                        'new_role': new_role,
                    }
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء تغيير دور العضو"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # POST /scouts/dept/remove_member/
    @action(detail=False, methods=['post'])
    def remove_member(self, request):
        """Remove a member from a clan (intervention)"""
        try:
            admin = request.user_data
            is_dept_manager(admin)

            clan_id = request.data.get('clan_id')
            member_id = request.data.get('member_id')

            if not clan_id or not member_id:
                return Response(
                    error_response("يجب تحديد رقم العشيرة ورقم العضو"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            clan = get_clan_or_404(clan_id)
            member = get_member_or_404(member_id)
            validate_member_belongs_to_clan(member, clan)

            member_name = member.student.name
            student_id = member.student_id

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    member.delete()

            self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['remove_member'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
                student_id=student_id,
            )

            return Response(
                success_response(
                    f"تم إزالة العضو {member_name} من العشيرة بنجاح"
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء إزالة العضو"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )