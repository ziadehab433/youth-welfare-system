from rest_framework import serializers
from apps.event.models import Plans, Events
from apps.family.models import Faculties


# ───────────────────── nested event serializer (full detail) ─────────────────────

class PlanEventSerializer(serializers.ModelSerializer):
    """Full event details when nested inside a plan response."""

    dept_name = serializers.CharField(source='dept.name', read_only=True, default=None)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True, default=None)
    family_name = serializers.CharField(source='family.name', read_only=True, default=None)

    class Meta:
        model = Events
        fields = [
            'event_id',
            'title',
            'description',
            'dept',
            'dept_name',
            'faculty',
            'faculty_name',
            'created_by',
            'created_by_name',
            'family',
            'family_name',
            'cost',
            'location',
            'restrictions',
            'reward',
            'status',
            'type',
            'imgs',
            'st_date',
            'end_date',
            's_limit',
            'resource',
            'selected_facs',
            'active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


# ───────────────────── plan list serializer ─────────────────────

class PlanListSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, default=None)
    events_count = serializers.IntegerField(source='events.count', read_only=True)

    class Meta:
        model = Plans
        fields = [
            'plan_id',
            'name',
            'term',
            'faculty',
            'faculty_name',
            'events_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


# ───────────────────── plan detail serializer ─────────────────────

class PlanDetailSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, default=None)
    events = PlanEventSerializer(many=True, read_only=True)

    class Meta:
        model = Plans
        fields = [
            'plan_id',
            'name',
            'term',
            'faculty',
            'faculty_name',
            'events',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


# ───────────────────── plan create serializer ─────────────────────

class PlanCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    term = serializers.IntegerField()
    faculty_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_term(self, value):
        if value not in (1, 2):
            raise serializers.ValidationError("الفصل الدراسي يجب أن يكون 1 أو 2")
        return value

    def validate_faculty_id(self, value):
        if value is not None:
            if not Faculties.objects.filter(pk=value).exists():
                raise serializers.ValidationError("الكلية المحددة غير موجودة")
        return value

    def to_internal_value(self, data):
        """Convert faculty_id to faculty FK instance for service layer."""
        ret = super().to_internal_value(data)
        faculty_id = ret.pop('faculty_id', None)
        if faculty_id is not None:
            ret['faculty'] = Faculties.objects.get(pk=faculty_id)
        else:
            ret['faculty'] = None
        return ret


# ───────────────────── plan update serializer ─────────────────────

class PlanUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    term = serializers.IntegerField(required=False)

    def validate_term(self, value):
        if value not in (1, 2):
            raise serializers.ValidationError("الفصل الدراسي يجب أن يكون 1 أو 2")
        return value


# ───────────────────── add event serializer ─────────────────────

class AddEventToPlanSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()

    def validate_event_id(self, value):
        if not Events.objects.filter(pk=value).exists():
            raise serializers.ValidationError("النشاط المحدد غير موجود")
        return value