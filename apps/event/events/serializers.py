from rest_framework import serializers
from apps.event.models import Events, Prtcps, EventDocs
from apps.accounts.models import AdminsUser
from apps.solidarity.models import Faculties
from apps.accounts.utils import get_current_admin
from drf_spectacular.utils import extend_schema_field

class EventDocsSerializer(serializers.ModelSerializer):
    """Serializer for event documents/images"""
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source='uploaded_by.name', read_only=True, allow_null=True)

    class Meta:
        model = EventDocs
        fields = [
            'doc_id', 
            'event', 
            'doc_type', 
            'file_name',
            'file_url', 
            'mime_type', 
            'file_size', 
            'uploaded_at', 
            'uploaded_by',
            'uploaded_by_name'
        ]
        read_only_fields = ['doc_id', 'uploaded_at', 'uploaded_by', 'uploaded_by_name']

    @extend_schema_field(serializers.URLField)
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file_path:
            from django.conf import settings
            url = f"{settings.MEDIA_URL}{obj.file_path}"
            return request.build_absolute_uri(url) if request else url
        return None


class EventImageUploadSerializer(serializers.Serializer):
    """Serializer for uploading event images"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    
    images = serializers.ListField(
        child=serializers.FileField(),
        required=True,
        allow_empty=False,
        max_length=10,  # Maximum 10 images per upload
        help_text="List of image files (max 10, each max 20MB)"
    )
    
    doc_type = serializers.ChoiceField(
        choices=[
            ('event_image', 'صورة الفعالية'),
            ('poster', 'ملصق'),
            ('certificate', 'شهادة'),
            ('other', 'أخرى'),
        ],
        default='event_image',
        required=False
    )
    
    def validate_images(self, images):
        """Validate each image file"""
        for image in images:
            # Check file size
            if image.size > self.MAX_FILE_SIZE:
                raise serializers.ValidationError(
                    f"File {image.name} exceeds {self.MAX_FILE_SIZE / (1024*1024):.0f}MB limit"
                )
            
            # Check file extension
            ext = image.name.split('.')[-1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise serializers.ValidationError(
                    f"File {image.name} has invalid extension. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
                )
        
        return images


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = [
            'title', 'description', 'dept', 'cost',
            'location', 'restrictions', 'reward', 
            'st_date', 'end_date', 's_limit', 'type',
            'resource', 'selected_facs', 'plan' 
        ]
        extra_kwargs = {
            'plan': {'required': False, 'allow_null': True},
            'selected_facs': {'required': False, 'allow_null': True, 'allow_empty': True}
        }

    def __init__(self, *args, **kwargs):
        """Dynamically remove selected_facs field for non-department managers"""
        super().__init__(*args, **kwargs)
        
        request = self.context.get('request')
        if request:
            admin = get_current_admin(request) 
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
        
        request = self.context.get('request')
        if request:
            admin = get_current_admin(request)
            if admin.role == 'مسؤول كلية' and data.get('selected_facs'):
                raise serializers.ValidationError({
                    "selected_facs": "Faculty admins cannot use the selected_facs field"
                })
        
        return data
    
    def create(self, validated_data):
        validated_data['active'] = True 
        validated_data['status'] = 'منتظر' 
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data['active'] = True 
        validated_data['status'] = 'منتظر' 
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('active', None)
        
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
            'location', 'status', 'type', 'cost', 's_limit', 'faculty_id', 'dept_id','active'
        ]

class ParticipantSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    
    class Meta:
        model = Prtcps
        fields = ['id', 'student_id', 'student_name', 'rank', 'reward', 'status']

class EventDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    dept_name = serializers.CharField(source='dept.name', read_only=True, allow_null=True)
    family_name = serializers.CharField(source='family.name', read_only=True, allow_null=True)
    
    participants = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    
    class Meta:
        model = Events
        exclude = ['plan']
    
    def get_participants(self, obj):
        if hasattr(obj, 'participants'):
            participants = obj.participants
        else:
            participants = obj.prtcps_set.all()
        
        return ParticipantSerializer(participants, many=True).data
    
    def get_images(self, obj):
        """Return all images for this event"""
        docs = obj.event_docs.all()
        return EventDocsSerializer(docs, many=True, context=self.context).data

    def to_representation(self, instance):
        """Remove selected_facs from response for faculty admins"""
        representation = super().to_representation(instance)
        
        request = self.context.get('request')
        if request:
            admin = get_current_admin(request)
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
             'reward'
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
         'reward'
        ]
        
class ParticipantResultSerializer(serializers.Serializer):
    rank = serializers.IntegerField(
        required=False, 
        allow_null=True, 
        min_value=1,
    )
    reward = serializers.CharField(
        required=False, 
        allow_null=True, 
        max_length=255,
    )

    def validate(self, data):
        if not data.get('rank') and not data.get('reward'):
            raise serializers.ValidationError(
                "At least one of 'rank' or 'reward' must be provided."
            )
        return data