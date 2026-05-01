from rest_framework import serializers

from apps.event.teams.models import EventTeamMembers, EventTeams, EventTeamSettings


class EventTeamSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTeamSettings
        fields = [
            'setting_id',
            'event',
            'enabled',
            'min_members',
            'max_members',
            'max_teams',
            'allow_individual_join',
            'require_team_approval',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'setting_id',
            'event',
            'created_by',
            'created_at',
            'updated_at',
        ]


class EventTeamSettingsCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTeamSettings
        fields = [
            'enabled',
            'min_members',
            'max_members',
            'max_teams',
            'allow_individual_join',
            'require_team_approval',
        ]

    def validate(self, attrs):
        min_members = attrs.get(
            'min_members',
            getattr(self.instance, 'min_members', None),
        )
        max_members = attrs.get(
            'max_members',
            getattr(self.instance, 'max_members', None),
        )
        max_teams = attrs.get(
            'max_teams',
            getattr(self.instance, 'max_teams', None),
        )

        if min_members is not None and min_members < 1:
            raise serializers.ValidationError({
                'min_members': 'يجب أن يكون الحد الأدنى لعدد الأعضاء أكبر من أو يساوي 1.'
            })

        if max_members is not None and max_members < 1:
            raise serializers.ValidationError({
                'max_members': 'يجب أن يكون الحد الأقصى لعدد الأعضاء أكبر من أو يساوي 1.'
            })

        if min_members is not None and max_members is not None:
            if max_members < min_members:
                raise serializers.ValidationError({
                    'max_members': 'يجب أن يكون الحد الأقصى لعدد الأعضاء أكبر من أو يساوي الحد الأدنى.'
                })

        if max_teams is not None and max_teams < 1:
            raise serializers.ValidationError({
                'max_teams': 'يجب أن يكون الحد الأقصى لعدد الفرق أكبر من أو يساوي 1.'
            })

        return attrs


class CreateTeamSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)


class JoinTeamByCodeSerializer(serializers.Serializer):
    join_code = serializers.CharField(max_length=12)


class AdminCreateTeamSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    captain_id = serializers.IntegerField()
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )

    def validate_student_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError('لا يسمح بتكرار معرفات الطلاب.')
        return value

    def validate(self, attrs):
        captain_id = attrs.get('captain_id')
        student_ids = attrs.get('student_ids', [])

        if captain_id not in student_ids:
            raise serializers.ValidationError({
                'captain_id': 'يجب أن يكون قائد الفريق ضمن قائمة الطلاب.'
            })

        return attrs


class RejectTeamSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )


class AssignTeamResultSerializer(serializers.Serializer):
    rank = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
    )

    is_winner = serializers.BooleanField(
        required=False,
    )

    def validate(self, attrs):
        rank = attrs.get('rank', None)
        is_winner = attrs.get('is_winner', None)

        if rank is None and is_winner is None:
            raise serializers.ValidationError(
                'يجب إرسال الترتيب أو تحديد حالة الفوز على الأقل.'
            )

        return attrs


class TeamMemberSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source='student.student_id', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)

    participation_id = serializers.IntegerField(source='participation.id', read_only=True)
    participation_status = serializers.CharField(source='participation.status', read_only=True)

    class Meta:
        model = EventTeamMembers
        fields = [
            'member_id',
            'student_id',
            'student_name',
            'student_email',
            'participation_id',
            'participation_status',
            'role',
            'status',
            'joined_at',
        ]


class EventTeamDetailSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)

    captain_name = serializers.CharField(source='captain.name', read_only=True)

    approved_by_name = serializers.CharField(
        source='approved_by.name',
        read_only=True,
        allow_null=True,
    )

    rejected_by_name = serializers.CharField(
        source='rejected_by.name',
        read_only=True,
        allow_null=True,
    )

    created_by_admin_name = serializers.CharField(
        source='created_by_admin.name',
        read_only=True,
        allow_null=True,
    )

    result_assigned_by_name = serializers.CharField(
        source='result_assigned_by.name',
        read_only=True,
        allow_null=True,
    )

    members_count = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    class Meta:
        model = EventTeams
        fields = [
            'team_id',
            'event',
            'event_title',
            'name',
            'captain',
            'captain_name',
            'join_code',
            'status',
            'approved_by',
            'approved_by_name',
            'approved_at',
            'rejected_by',
            'rejected_by_name',
            'rejected_at',
            'rejection_reason',
            'created_by_admin',
            'created_by_admin_name',
            'rank',
            'is_winner',
            'result_assigned_by',
            'result_assigned_by_name',
            'result_assigned_at',
            'created_at',
            'updated_at',
            'members_count',
            'members',
        ]

    def get_members_count(self, obj):
        annotated_count = getattr(obj, 'active_members_count', None)

        if annotated_count is not None:
            return annotated_count

        return obj.members.filter(
            status=EventTeamMembers.MemberStatus.ACTIVE
        ).count()

    def get_members(self, obj):
        members = obj.members.all()
        return TeamMemberSerializer(members, many=True).data