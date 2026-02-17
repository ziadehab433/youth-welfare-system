from rest_framework import serializers
from apps.event.models import Events
from apps.accounts.models import AdminsUser
from apps.solidarity.models import Faculties
from apps.accounts.utils import get_current_admin

class EventCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = [
            'title', 'description', 'dept', 'cost',
            'location', 'restrictions', 'reward', 'imgs',
            'st_date', 'end_date', 's_limit', 'type', 'family',
            'resource', 'selected_facs' 
        ]

    def __init__(self, *args, **kwargs):
        """Dynamically remove selected_facs field for non-department managers"""
        super().__init__(*args, **kwargs)
        
        # Check if we have request in context
        request = self.context.get('request')
        if request:
            admin = get_current_admin(request)  # You'll need to import this
            # Remove selected_facs field for faculty admins
            if admin.role == 'مسؤول كلية' and 'selected_facs' in self.fields:
                self.fields.pop('selected_facs')

    def validate_selected_facs(self, value):
        """
        Validate that all selected_facs are valid faculty IDs in the database
        This validation will only run for department managers since the field
        is removed for faculty admins
        """
        if not value: 
            return value
        
        if not isinstance(value, list):
            raise serializers.ValidationError("selected_facs must be a list of faculty IDs")
        
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate faculty IDs are not allowed")
        
        existing_faculties = Faculties.objects.filter(faculty_id__in=value).values_list('faculty_id', flat=True)
        existing_faculties_set = set(existing_faculties)
        provided_faculties_set = set(value)
        
        invalid_faculties = provided_faculties_set - existing_faculties_set
        
        if invalid_faculties:
            raise serializers.ValidationError(
                f"The following faculty IDs do not exist: {sorted(invalid_faculties)}"
            )
        
        return value
    
    def validate(self, data):
        if data.get('st_date') and data.get('end_date'):
            if data['end_date'] < data['st_date']:
                raise serializers.ValidationError("End date must be after start date")
        
        # Additional validation for faculty admins
        request = self.context.get('request')
        if request:
            admin = get_current_admin(request)
            # If faculty admin, ensure selected_facs is not in data (should be removed already)
            if admin.role == 'مسؤول كلية' and 'selected_facs' in data:
                raise serializers.ValidationError({
                    "selected_facs": "Faculty admins cannot use the selected_facs field"
                })
        
        return data
    
    def create(self, validated_data):
        validated_data['plan'] = None
        validated_data['active'] = True 
        validated_data['status'] = 'منتظر' 
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data['plan'] = None
        validated_data['active'] = True 
        validated_data['status'] = 'منتظر' 
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('active', None)
        
        # Optionally remove selected_facs from response for faculty admins
        request = self.context.get('request')
        if request:
            admin = get_current_admin(request)
            if admin.role == 'مسؤول كلية' and 'selected_facs' in representation:
                representation.pop('selected_facs')
        
        return representation

class EventListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = [
            'event_id', 'title', 'description', 'st_date', 'end_date',
            'location', 'status', 'type', 'cost', 's_limit', 'faculty_id'
        ]

class EventDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    dept_name = serializers.CharField(source='dept.name', read_only=True, allow_null=True)
    family_name = serializers.CharField(source='family.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Events
        exclude = ['plan']

    def to_representation(self, instance):
        """Remove selected_facs from response for faculty admins"""
        representation = super().to_representation(instance)
        
        # Check if we have request in context
        request = self.context.get('request')
        if request:
            admin = get_current_admin(request)
            # Remove selected_facs for faculty admins
            if admin.role == 'مسؤول كلية' and 'selected_facs' in representation:
                representation.pop('selected_facs')
        
        return representation

class EventAvailableSerializer(serializers.ModelSerializer):
    """
    Serializer for available events list view
    """
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    dept_name = serializers.CharField(source='dept.name', read_only=True, allow_null=True)
    days_remaining = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    current_participants = serializers.SerializerMethodField()

    class Meta:
        model = Events
        fields = [
            'event_id', 'title', 'description', 'st_date', 'end_date',
            'location', 'type', 'cost', 's_limit', 'faculty_name', 
            'dept_name', 'days_remaining', 'is_full', 'current_participants',
            'imgs', 'reward'
        ]

    def get_days_remaining(self, obj):
        from django.utils import timezone
        if obj.st_date:
            delta = obj.st_date - timezone.now().date()
            return delta.days
        return None

    def get_current_participants(self, obj):
        return obj.prtcps_set.filter(status='مقبول').count()

    def get_is_full(self, obj):
        if obj.s_limit:
            current = self.get_current_participants(obj)
            return current >= obj.s_limit
        return False


class EventJoinedSerializer(serializers.ModelSerializer):
    """
    Serializer for events the student has joined
    """
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    dept_name = serializers.CharField(source='dept.name', read_only=True, allow_null=True)
    participation_status = serializers.CharField(source='prtcps_set.first.status', read_only=True)
    participation_rank = serializers.IntegerField(source='prtcps_set.first.rank', read_only=True)
    participation_reward = serializers.CharField(source='prtcps_set.first.reward', read_only=True)

    class Meta:
        model = Events
        fields = [
            'event_id', 'title', 'description', 'st_date', 'end_date',
            'location', 'type', 'cost', 'faculty_name', 'dept_name',
            'participation_status', 'participation_rank', 'participation_reward',
            'imgs', 'reward'
        ]