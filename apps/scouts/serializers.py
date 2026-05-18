from rest_framework import serializers
from .models import Clans, ClanGroups, ScoutMembers, UniversityScoutMembers, UniversityScoutProgramMembers, UniversityScoutPrograms


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

    def get_members_count(self, obj) -> int:
        return obj.members.filter(status='مقبول').count()

    def get_groups_count(self, obj) -> int:
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
        read_only_fields = [
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

    def get_members_count(self, obj) -> int:
        return obj.members.filter(status='مقبول').count()

    def get_groups(self, obj) -> list:
        groups = obj.groups.all().order_by('display_order')
        return GroupDetailSerializer(groups, many=True).data

    def get_structure(self, obj) -> dict:
        """Return the full administrative structure"""
        clan_level_roles = [r[0] for r in ScoutMembers.CLAN_LEVEL_ROLES]

        leaders = obj.members.filter(
            status='مقبول'
        ).exclude(
            role='عضو'
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

            if member.role in clan_level_roles:
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
        read_only_fields = [
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

    def get_members_count(self, obj) -> int:
        return obj.members.count()

    def get_accepted_count(self, obj) -> int:
        return obj.members.filter(status='مقبول').count()

    def get_pending_count(self, obj) -> int:
        return obj.members.filter(status='منتظر').count()

    def get_groups_count(self, obj) -> int:
        return obj.groups.count()

    def get_is_structure_complete(self, obj) -> bool:
        required_roles = [
            'قائد العشيرة',
            'مساعد قائد',
            'مساعدة قائد',
            'رائد أكبر',
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

    def get_members_count(self, obj) -> int:
        return obj.group_members.filter(status='مقبول').count()


class GroupDetailSerializer(serializers.ModelSerializer):
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
        read_only_fields = [
            'group_id',
            'name',
            'display_order',
            'members_count',
            'leaders',
        ]

    def get_members_count(self, obj) -> int:
        return obj.group_members.filter(status='مقبول').count()

    def get_leaders(self, obj) -> dict:
        group_level_roles = [r[0] for r in ScoutMembers.GROUP_LEVEL_ROLES]

        leaders = obj.group_members.filter(
            status='مقبول',
            role__in=group_level_roles
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

class ScoutJoinSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoutMembers
        fields = ['clan']

    def validate(self, data):
        student = self.context['request'].user
        clan = data['clan']

        existing = ScoutMembers.objects.filter(
            student_id=student.student_id,
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

        if clan.faculty_id != student.faculty_id:
            raise serializers.ValidationError(
                "لا يمكنك الانضمام إلى عشيرة كلية أخرى"
            )

        return data


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
        read_only_fields = [
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


class ScoutReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=['approve', 'reject']
    )
    rejection_reason = serializers.CharField(
        required=False,
        allow_blank=True
    )

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError(
                "يجب كتابة سبب الرفض"
            )
        return data


class ScoutAssignGroupSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()

    def validate_group_id(self, value):
        if not ClanGroups.objects.filter(group_id=value).exists():
            raise serializers.ValidationError(
                "الرهط غير موجود"
            )
        return value


class ScoutChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=ScoutMembers.ROLE_CHOICES
    )

    def validate_role(self, value):
        member = self.context.get('member')
        if not member:
            return value

        if value != 'عضو' and member.status != 'مقبول':
            raise serializers.ValidationError(
                "يجب قبول العضو أولاً قبل تعيينه في منصب قيادي"
            )

        female_only = ScoutMembers.FEMALE_ONLY_ROLES
        male_only = ScoutMembers.MALE_ONLY_ROLES

        if member.student.gender == 'M' and value in female_only:
            raise serializers.ValidationError(
                "لا يمكن تعيين طالب ذكر في منصب مخصص للإناث"
            )

        if member.student.gender == 'F' and value in male_only:
            raise serializers.ValidationError(
                "لا يمكن تعيين طالبة أنثى في منصب مخصص للذكور"
            )

        return value


class ScoutAddByNidSerializer(serializers.Serializer):
    nid = serializers.CharField(required=True)

    def validate_nid(self, value):
        from apps.accounts.models import Students
        if not Students.objects.filter(nid=value).exists():
            raise serializers.ValidationError(
                "لا يوجد طالب بهذا الرقم القومي"
            )
        return value


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
        read_only_fields = [
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
class UniversityScoutProgramSerializer(serializers.ModelSerializer):

    class Meta:
        model = UniversityScoutPrograms

        fields = [
            'program_id',
            'name',
            'description',
            'is_active',
            'created_at',
        ]

        read_only_fields = [
            'program_id',
            'is_active',
            'created_at',
        ]


class UniversityScoutMemberSerializer(
    serializers.ModelSerializer
):

    student_name = serializers.CharField(
        source='scout_member.student.name',
        read_only=True
    )

    faculty_name = serializers.CharField(
        source='scout_member.clan.faculty.name',
        read_only=True
    )

    clan_name = serializers.CharField(
        source='scout_member.clan.name',
        read_only=True
    )
    programs = serializers.SerializerMethodField()

    class Meta:
        model = UniversityScoutMembers

        fields = [
            'university_member_id',
            'scout_member',
            'student_name',
            'faculty_name',
            'clan_name',
            'university_role',
            'programs',
            'created_at',
        ]

    def get_programs(self, obj):

        return [
            {
                'id': membership.id,
                'program_id': membership.program.program_id,
                'program_name': membership.program.name,
            }
            for membership in obj.program_memberships.all()
        ]


class UniversityScoutProgramMemberSerializer(
    serializers.ModelSerializer
):

    student_name = serializers.CharField(
        source='university_member.scout_member.student.name',
        read_only=True
    )

    faculty_name = serializers.CharField(
        source='university_member.scout_member.clan.faculty.name',
        read_only=True
    )

    program_name = serializers.CharField(
        source='program.name',
        read_only=True
    )

    class Meta:

        model = UniversityScoutProgramMembers

        fields = [
            'id',
            'university_member',
            'student_name',
            'faculty_name',
            'program',
            'program_name',
            'created_at',
        ]


class CreateUniversityProgramSerializer(
    serializers.Serializer
):

    name = serializers.CharField(
        max_length=100
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True
    )


class AddToUniversityScoutsSerializer(
    serializers.Serializer
):

    scout_member_id = serializers.IntegerField()


class AssignUniversityRoleSerializer(
    serializers.Serializer
):

    university_member_id = serializers.IntegerField()

    university_role = serializers.ChoiceField(
        choices=UniversityScoutMembers.UNIVERSITY_ROLES
    )


class AssignMemberToProgramSerializer(
    serializers.Serializer
):

    university_member_id = serializers.IntegerField()

    program_id = serializers.IntegerField()


class RemoveUniversityTeamMemberSerializer(
    serializers.Serializer
):

    university_member_id = serializers.IntegerField()