from rest_framework import serializers
from .models import Clans, ClanGroups, ScoutMembers


# ============================================
# Clan Serializers
# ============================================

class ClanSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(
        source='faculty.name',
        read_only=True
    )
    members_count = serializers.SerializerMethodField()
    groups_count = serializers.SerializerMethodField()

    class Meta:
        model = Clans
        fields = [
            'clan_id',
            'name',
            'description',
            'faculty',
            'faculty_name',
            'status',
            'min_members',
            'members_count',
            'groups_count',
            'created_at',
        ]
        read_only_fields = ['clan_id', 'created_at']

    def get_members_count(self, obj):
        """Count only accepted members"""
        return obj.members.filter(status='مقبول').count()

    def get_groups_count(self, obj):
        """Count all groups in the clan"""
        return obj.groups.count()


class ClanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clans
        fields = [
            'name',
            'description',
            'faculty',
            'min_members',
        ]

    def validate_faculty(self, value):
        """Ensure one clan per faculty"""
        if Clans.objects.filter(faculty=value).exists():
            raise serializers.ValidationError(
                "هذه الكلية لديها عشيرة بالفعل"
            )
        return value


class ClanDetailSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(
        source='faculty.name',
        read_only=True
    )
    groups = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    structure = serializers.SerializerMethodField()

    class Meta:
        model = Clans
        fields = [
            'clan_id',
            'name',
            'description',
            'faculty',
            'faculty_name',
            'status',
            'min_members',
            'members_count',
            'groups',
            'structure',
            'created_at',
        ]
        read_only_fields = '__all__'

    def get_members_count(self, obj):
        return obj.members.filter(status='مقبول').count()

    def get_groups(self, obj):
        groups = obj.groups.all().order_by('display_order')
        return GroupDetailSerializer(groups, many=True).data

    def get_structure(self, obj):
        """Return the full administrative structure"""
        leaders = obj.members.filter(
            status='مقبول'
        ).exclude(
            role='MEMBER'
        ).select_related('student', 'group')

        structure = {
            'clan_level': {},
            'group_level': {},
        }

        for member in leaders:
            role_data = {
                'scout_member_id': member.scout_member_id,
                'name': member.student.name,
                'gender': member.student.gender,
                'group': member.group.name if member.group else None,
            }

            if member.role in [
                'CLAN_LEADER', 'ASSISTANT_MALE', 'ASSISTANT_FEMALE',
                'HEAD_ROVER', 'SECRETARY', 'EQUIPMENT_MANAGER', 'VETERAN'
            ]:
                structure['clan_level'][member.role] = role_data
            else:
                group_name = member.group.name if member.group else 'غير محدد'
                if group_name not in structure['group_level']:
                    structure['group_level'][group_name] = {}
                structure['group_level'][group_name][member.role] = role_data

        return structure


class ClanOverviewSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(
        source='faculty.name',
        read_only=True
    )
    members_count = serializers.SerializerMethodField()
    accepted_count = serializers.SerializerMethodField()
    pending_count = serializers.SerializerMethodField()
    groups_count = serializers.SerializerMethodField()
    is_structure_complete = serializers.SerializerMethodField()

    class Meta:
        model = Clans
        fields = [
            'clan_id',
            'name',
            'faculty',
            'faculty_name',
            'status',
            'min_members',
            'members_count',
            'accepted_count',
            'pending_count',
            'groups_count',
            'is_structure_complete',
            'created_at',
        ]
        read_only_fields = '__all__'

    def get_members_count(self, obj):
        return obj.members.count()

    def get_accepted_count(self, obj):
        return obj.members.filter(status='مقبول').count()

    def get_pending_count(self, obj):
        return obj.members.filter(status='منتظر').count()

    def get_groups_count(self, obj):
        return obj.groups.count()

    def get_is_structure_complete(self, obj):
        """Check if all required leadership positions are filled"""
        required_roles = [
            'CLAN_LEADER',
            'ASSISTANT_MALE',
            'ASSISTANT_FEMALE',
            'HEAD_ROVER',
        ]
        existing = obj.members.filter(
            status='مقبول',
            role__in=required_roles
        ).values_list('role', flat=True)

        return all(r in existing for r in required_roles)


# ============================================
# Group Serializers
# ============================================

class GroupSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = ClanGroups
        fields = [
            'group_id',
            'name',
            'clan',
            'display_order',
            'members_count',
            'created_at',
        ]
        read_only_fields = ['group_id', 'created_at']

    def get_members_count(self, obj):
        return obj.members.filter(status='مقبول').count()


class GroupDetailSerializer(serializers.ModelSerializer):
    """Group with leadership details (male + female)"""
    members_count = serializers.SerializerMethodField()
    leaders = serializers.SerializerMethodField()

    class Meta:
        model = ClanGroups
        fields = [
            'group_id',
            'name',
            'display_order',
            'members_count',
            'leaders',
        ]

    def get_members_count(self, obj):
        return obj.members.filter(status='مقبول').count()

    def get_leaders(self, obj):
        """Get group leaders (male + female) and assistants"""
        leadership_roles = [
            'GROUP_LEADER_MALE',
            'GROUP_LEADER_FEMALE',
            'GROUP_ASSISTANT_MALE',
            'GROUP_ASSISTANT_FEMALE',
        ]
        leaders = obj.members.filter(
            status='مقبول',
            role__in=leadership_roles
        ).select_related('student')

        result = {}
        for leader in leaders:
            result[leader.role] = {
                'scout_member_id': leader.scout_member_id,
                'name': leader.student.name,
            }
        return result


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClanGroups
        fields = [
            'name',
            'clan',
            'display_order',
        ]


# ============================================
# Scout Member Serializers
# ============================================

# Student submits a join request
class ScoutJoinSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoutMembers
        fields = [
            'clan',
        ]

    def validate(self, data):
        """
        Validate join request:
        - No active duplicate requests
        - Allows re-application after rejection (handled in view)
        - Student must belong to the same faculty
        """
        student = self.context['request'].user_data
        clan = data['clan']

        existing = ScoutMembers.objects.filter(
            student_id=student['student_id'],
            clan=clan
        ).first()

        if existing:
            if existing.status == 'منتظر':
                raise serializers.ValidationError(
                    "لديك طلب انضمام قيد المراجعة بالفعل"
                )
            elif existing.status == 'مقبول':
                raise serializers.ValidationError(
                    "أنت عضو بالفعل في العشيرة"
                )
            # مرفوض → allow re-application (handled in view)

        if clan.faculty_id != student['faculty_id']:
            raise serializers.ValidationError(
                "لا يمكنك الانضمام إلى عشيرة كلية أخرى"
            )

        return data


# Student views their membership status
class ScoutStatusSerializer(serializers.ModelSerializer):
    clan_name = serializers.CharField(
        source='clan.name',
        read_only=True
    )
    group_name = serializers.CharField(
        source='group.name',
        read_only=True,
        default=None
    )

    class Meta:
        model = ScoutMembers
        fields = [
            'scout_member_id',
            'clan',
            'clan_name',
            'group',
            'group_name',
            'role',
            'status',
            'rejection_reason',
            'joined_at',
        ]
        read_only_fields = '__all__'


# Faculty admin / dept manager reviews a join request
class ScoutReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=['approve', 'reject']
    )
    rejection_reason = serializers.CharField(
        required=False,
        allow_blank=True
    )

    def validate(self, data):
        """Rejection requires a reason"""
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError(
                "يجب كتابة سبب الرفض"
            )
        return data


# Faculty admin assigns member to a group
class ScoutAssignGroupSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()

    def validate_group_id(self, value):
        """Ensure the group exists"""
        if not ClanGroups.objects.filter(group_id=value).exists():
            raise serializers.ValidationError(
                "الرهط غير موجود"
            )
        return value


# Faculty admin / dept manager changes member role
class ScoutChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=ScoutMembers.ROLE_CHOICES
    )

    def validate_role(self, value):
        """
        Validate role change:
        - Leadership roles require accepted status
        - Gender must match gendered roles
        """
        member = self.context.get('member')
        if not member:
            return value

        if value != 'MEMBER' and member.status != 'مقبول':
            raise serializers.ValidationError(
                "يجب قبول العضو أولاً قبل تعيينه في منصب قيادي"
            )

        # Gender validation for gendered roles
        if member.student.gender == 'M' and value in [
            'GROUP_LEADER_FEMALE', 'GROUP_ASSISTANT_FEMALE', 'ASSISTANT_FEMALE'
        ]:
            raise serializers.ValidationError(
                "لا يمكن تعيين طالب ذكر في منصب مخصص للإناث"
            )

        if member.student.gender == 'F' and value in [
            'GROUP_LEADER_MALE', 'GROUP_ASSISTANT_MALE', 'ASSISTANT_MALE'
        ]:
            raise serializers.ValidationError(
                "لا يمكن تعيين طالبة أنثى في منصب مخصص للذكور"
            )

        return value


# Faculty admin adds a student directly by national ID
class ScoutAddByNidSerializer(serializers.Serializer):
    nid = serializers.CharField(required=True)

    def validate_nid(self, value):
        """Ensure the student exists"""
        from youth_welfare.models import Students
        if not Students.objects.filter(nid=value).exists():
            raise serializers.ValidationError(
                "لا يوجد طالب بهذا الرقم القومي"
            )
        return value


# Faculty admin views full members list
class ScoutMemberListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source='student.name',
        read_only=True
    )
    student_email = serializers.CharField(
        source='student.email',
        read_only=True
    )
    student_gender = serializers.CharField(
        source='student.gender',
        read_only=True
    )
    student_phone = serializers.CharField(
        source='student.phone_number',
        read_only=True
    )
    group_name = serializers.CharField(
        source='group.name',
        read_only=True,
        default=None
    )

    class Meta:
        model = ScoutMembers
        fields = [
            'scout_member_id',
            'student',
            'student_name',
            'student_email',
            'student_gender',
            'student_phone',
            'clan',
            'group',
            'group_name',
            'role',
            'status',
            'joined_at',
            'created_at',
        ]
        read_only_fields = '__all__'