from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from drf_spectacular.utils import extend_schema
from ..models import Clans, ClanGroups, ScoutMembers
from ..serializers import (
    ClanSerializer,
    ClanCreateSerializer,
    ClanDetailSerializer,
    GroupSerializer,
    GroupCreateSerializer,
    ScoutMemberListSerializer,
    ScoutReviewSerializer,
    ScoutAssignGroupSerializer,
    ScoutChangeRoleSerializer,
)
from ..utils import (
    is_faculty_admin,
    get_admin_clan,
    get_group_or_404,
    get_member_or_404,
    validate_group_belongs_to_clan,
    validate_member_belongs_to_clan,
    validate_member_is_pending,
    validate_member_is_accepted,
    validate_unique_role,
    get_clan_stats,
    get_clan_structure,
    success_response,
    error_response,
    SCOUT_LOG_ACTIONS,
    SCOUT_TARGET_TYPE,
    validate_single_leadership_role,
)
from apps.accounts.mixins import AdminActionMixin

@extend_schema(tags=["Faculty Admin Scouts"])
class FacultyAdminScoutViewSet(ViewSet, AdminActionMixin):
    """
    Faculty admin scout endpoints with logging.
    """

    # ==========================================
    # Clan Management
    # ==========================================

    # GET /scouts/faculty/clan/
    @action(detail=False, methods=['get'])
    def clan(self, request):
        """View clan with full details and stats"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            serializer = ClanDetailSerializer(clan)
            stats = get_clan_stats(clan)

            return Response(
                success_response(
                    "تم جلب بيانات العشيرة بنجاح",
                    data={
                        'clan': serializer.data,
                        'stats': stats,
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

    # POST /scouts/faculty/create_clan/
    @action(detail=False, methods=['post'])
    def create_clan(self, request):
        """Create a new clan for the faculty"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)

            if Clans.objects.filter(faculty_id=admin['faculty_id']).exists():
                return Response(
                    error_response("كليتك لديها عشيرة بالفعل"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = request.data.copy()
            data['faculty'] = admin['faculty_id']

            serializer = ClanCreateSerializer(data=data)

            if not serializer.is_valid():
                return Response(
                    error_response(
                        "بيانات العشيرة غير صحيحة",
                        errors=serializer.errors
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    return serializer.save(
                        created_by_id=admin_obj.admin_id,
                        created_at=timezone.now()
                    )

            clan = self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['create_clan'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
            )

            return Response(
                success_response(
                    "تم إنشاء العشيرة بنجاح",
                    data=ClanSerializer(clan).data
                ),
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء إنشاء العشيرة"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # PUT /scouts/faculty/update_clan/
    @action(detail=False, methods=['put'])
    def update_clan(self, request):
        """Update clan info"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            serializer = ClanSerializer(
                clan,
                data=request.data,
                partial=True
            )

            if not serializer.is_valid():
                return Response(
                    error_response(
                        "بيانات التعديل غير صحيحة",
                        errors=serializer.errors
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    return serializer.save(updated_at=timezone.now())

            self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['update_clan'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
            )

            return Response(
                success_response(
                    "تم تعديل بيانات العشيرة بنجاح",
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
                error_response("حدث خطأ أثناء تعديل بيانات العشيرة"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # GET /scouts/faculty/structure/
    @action(detail=False, methods=['get'])
    def structure(self, request):
        """View the full administrative hierarchy"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

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
    # Group Management
    # ==========================================

    # GET /scouts/faculty/groups/
    @action(detail=False, methods=['get'])
    def groups(self, request):
        """List all groups in the clan"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            groups = clan.groups.all().order_by('display_order')
            serializer = GroupSerializer(groups, many=True)

            return Response(
                success_response(
                    "تم جلب الرهوط بنجاح",
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

    # POST /scouts/faculty/create_group/
    @action(detail=False, methods=['post'])
    def create_group(self, request):
        """Create a new group in the clan"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            data = request.data.copy()
            data['clan'] = clan.clan_id

            serializer = GroupCreateSerializer(data=data)

            if not serializer.is_valid():
                return Response(
                    error_response(
                        "بيانات الرهط غير صحيحة",
                        errors=serializer.errors
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    return serializer.save(created_at=timezone.now())

            group = self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['create_group'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
            )

            return Response(
                success_response(
                    "تم إنشاء الرهط بنجاح",
                    data=GroupSerializer(group).data
                ),
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء إنشاء الرهط"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # PUT /scouts/faculty/update_group/
    @action(detail=False, methods=['put'])
    def update_group(self, request):
        """Update group name or display order"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            group_id = request.data.get('group_id')
            if not group_id:
                return Response(
                    error_response("يجب تحديد رقم الرهط"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            group = get_group_or_404(group_id)
            validate_group_belongs_to_clan(group, clan)

            serializer = GroupSerializer(
                group,
                data=request.data,
                partial=True
            )

            if not serializer.is_valid():
                return Response(
                    error_response(
                        "بيانات التعديل غير صحيحة",
                        errors=serializer.errors
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    return serializer.save(updated_at=timezone.now())

            self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['update_group'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
            )

            return Response(
                success_response(
                    "تم تعديل الرهط بنجاح",
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
                error_response("حدث خطأ أثناء تعديل الرهط"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # POST /scouts/faculty/delete_group/
    @action(detail=False, methods=['post'])
    def delete_group(self, request):
        """Delete a group. Members become unassigned."""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            group_id = request.data.get('group_id')
            if not group_id:
                return Response(
                    error_response("يجب تحديد رقم الرهط"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            group = get_group_or_404(group_id)
            validate_group_belongs_to_clan(group, clan)

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    ScoutMembers.objects.filter(group=group).update(
                        group=None,
                        updated_at=timezone.now()
                    )
                    group.delete()

            self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['delete_group'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
            )

            return Response(
                success_response("تم حذف الرهط بنجاح"),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء حذف الرهط"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==========================================
    # Member Management
    # ==========================================

    # GET /scouts/faculty/members/
    @action(detail=False, methods=['get'])
    def members(self, request):
        """List all members with optional filters"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            members = clan.members.select_related(
                'student', 'group'
            ).all()

            filter_status = request.query_params.get('status')
            if filter_status:
                members = members.filter(status=filter_status)

            filter_role = request.query_params.get('role')
            if filter_role:
                members = members.filter(role=filter_role)

            filter_group = request.query_params.get('group_id')
            if filter_group:
                members = members.filter(group_id=filter_group)

            unassigned = request.query_params.get('unassigned')
            if unassigned == 'true':
                members = members.filter(
                    group__isnull=True,
                    status='مقبول'
                )

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

    # POST /scouts/faculty/review_member/
    @action(detail=False, methods=['post'])
    def review_member(self, request):
        """Approve or reject a join request"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            member_id = request.data.get('member_id')
            if not member_id:
                return Response(
                    error_response("يجب تحديد رقم العضو"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            member = get_member_or_404(member_id)
            validate_member_belongs_to_clan(member, clan)
            validate_member_is_pending(member)

            serializer = ScoutReviewSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    error_response(
                        "بيانات المراجعة غير صحيحة",
                        errors=serializer.errors
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            action_type = serializer.validated_data['action']

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    now = timezone.now()
                    if action_type == 'approve':
                        member.status = 'مقبول'
                        member.joined_at = now
                    else:
                        member.status = 'مرفوض'
                        member.rejection_reason = serializer.validated_data.get('rejection_reason')

                    member.reviewed_by_id = admin_obj.admin_id
                    member.reviewed_at = now
                    member.updated_at = now
                    member.save()

            log_action = SCOUT_LOG_ACTIONS['approve_member'] if action_type == 'approve' else SCOUT_LOG_ACTIONS['reject_member']

            self.execute_admin_action(
                request=request,
                action_name=log_action,
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
                student_id=member.student_id,
            )

            msg = "تم قبول طلب الانضمام بنجاح" if action_type == 'approve' else "تم رفض طلب الانضمام"

            return Response(
                success_response(msg),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء مراجعة الطلب"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # POST /scouts/faculty/assign_group/
    @action(detail=False, methods=['post'])
    def assign_group(self, request):
        """Assign an accepted member to a group"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            member_id = request.data.get('member_id')
            if not member_id:
                return Response(
                    error_response("يجب تحديد رقم العضو"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            member = get_member_or_404(member_id)
            validate_member_belongs_to_clan(member, clan)
            validate_member_is_accepted(member)

            serializer = ScoutAssignGroupSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    error_response(
                        "بيانات التوزيع غير صحيحة",
                        errors=serializer.errors
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            group = get_group_or_404(
                serializer.validated_data['group_id']
            )
            validate_group_belongs_to_clan(group, clan)

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    member.group = group
                    member.updated_at = timezone.now()
                    member.save()

            self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['assign_group'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
                student_id=member.student_id,
            )

            return Response(
                success_response(
                    "تم توزيع العضو على الرهط بنجاح",
                    data={
                        'member_id': member.scout_member_id,
                        'group_id': group.group_id,
                        'group_name': group.name,
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
                error_response("حدث خطأ أثناء توزيع العضو"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # POST /scouts/faculty/change_role/
    @action(detail=False, methods=['post'])
    def change_role(self, request):
        """Change an accepted member's role"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            member_id = request.data.get('member_id')
            if not member_id:
                return Response(
                    error_response("يجب تحديد رقم العضو"),
                    status=status.HTTP_400_BAD_REQUEST
                )

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

    # POST /scouts/faculty/transfer_member/
    @action(detail=False, methods=['post'])
    def transfer_member(self, request):
        """Transfer a member to a different group"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            member_id = request.data.get('member_id')
            if not member_id:
                return Response(
                    error_response("يجب تحديد رقم العضو"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            member = get_member_or_404(member_id)
            validate_member_belongs_to_clan(member, clan)
            validate_member_is_accepted(member)

            serializer = ScoutAssignGroupSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    error_response(
                        "بيانات النقل غير صحيحة",
                        errors=serializer.errors
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            new_group = get_group_or_404(
                serializer.validated_data['group_id']
            )
            validate_group_belongs_to_clan(new_group, clan)

            if member.group_id == new_group.group_id:
                return Response(
                    error_response("العضو موجود بالفعل في هذا الرهط"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            old_group_name = member.group.name if member.group else "غير محدد"

            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    if member.role in [
                        'GROUP_LEADER_MALE', 'GROUP_LEADER_FEMALE',
                        'GROUP_ASSISTANT_MALE', 'GROUP_ASSISTANT_FEMALE'
                    ]:
                        member.role = 'MEMBER'
                    member.group = new_group
                    member.updated_at = timezone.now()
                    member.save()

            self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['transfer_member'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
                student_id=member.student_id,
            )

            return Response(
                success_response(
                    "تم نقل العضو بنجاح",
                    data={
                        'member_id': member.scout_member_id,
                        'from_group': old_group_name,
                        'to_group': new_group.name,
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
                error_response("حدث خطأ أثناء نقل العضو"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # POST /scouts/faculty/remove_member/
    @action(detail=False, methods=['post'])
    def remove_member(self, request):
        """Remove a member from the clan"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            member_id = request.data.get('member_id')
            if not member_id:
                return Response(
                    error_response("يجب تحديد رقم العضو"),
                    status=status.HTTP_400_BAD_REQUEST
                )

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
        
    # POST /scouts/faculty/add_by_nid/
    @action(detail=False, methods=['post'])
    def add_by_nid(self, request):
        """Add a student directly to the clan by national ID"""
        try:
            admin = request.user_data
            is_faculty_admin(admin)
            clan = get_admin_clan(admin)

            from ..serializers import ScoutAddByNidSerializer
            serializer = ScoutAddByNidSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    error_response(
                        "بيانات الإضافة غير صحيحة",
                        errors=serializer.errors
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            nid = serializer.validated_data['nid']

            # Get the student
            from youth_welfare.models import Students
            student = Students.objects.get(nid=nid)

            # Check if student belongs to same faculty
            if student.faculty_id != clan.faculty_id:
                return Response(
                    error_response("هذا الطالب لا ينتمي إلى كلية هذه العشيرة"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if already a member
            existing = ScoutMembers.objects.filter(
                student=student,
                clan=clan
            ).first()

            if existing:
                if existing.status == 'مقبول':
                    return Response(
                        error_response("هذا الطالب عضو بالفعل في العشيرة"),
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif existing.status == 'منتظر':
                    return Response(
                        error_response("هذا الطالب لديه طلب انضمام قيد المراجعة"),
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif existing.status == 'مرفوض':
                    # Re-activate rejected member
                    def business_logic(admin_obj, ip_address):
                        with transaction.atomic():
                            now = timezone.now()
                            existing.status = 'مقبول'
                            existing.role = 'MEMBER'
                            existing.group = None
                            existing.rejection_reason = None
                            existing.reviewed_by_id = admin_obj.admin_id
                            existing.reviewed_at = now
                            existing.joined_at = now
                            existing.updated_at = now
                            existing.save()

                    self.execute_admin_action(
                        request=request,
                        action_name=SCOUT_LOG_ACTIONS['add_by_nid'],
                        target_type=SCOUT_TARGET_TYPE,
                        business_operation=business_logic,
                        student_id=student.student_id,
                    )

                    return Response(
                        success_response(
                            f"تم إضافة الطالب {student.name} إلى العشيرة بنجاح"
                        ),
                        status=status.HTTP_201_CREATED
                    )

            # Create new member directly as ACCEPTED
            def business_logic(admin_obj, ip_address):
                with transaction.atomic():
                    now = timezone.now()
                    ScoutMembers.objects.create(
                        student=student,
                        clan=clan,
                        role='MEMBER',
                        status='مقبول',
                        reviewed_by_id=admin_obj.admin_id,
                        reviewed_at=now,
                        joined_at=now,
                        created_at=now,
                    )

            self.execute_admin_action(
                request=request,
                action_name=SCOUT_LOG_ACTIONS['add_by_nid'],
                target_type=SCOUT_TARGET_TYPE,
                business_operation=business_logic,
                student_id=student.student_id,
            )

            return Response(
                success_response(
                    f"تم إضافة الطالب {student.name} إلى العشيرة بنجاح"
                ),
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            if hasattr(e, 'detail'):
                return Response(
                    error_response(str(e.detail)),
                    status=e.status_code
                )
            return Response(
                error_response("حدث خطأ أثناء إضافة الطالب"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )