from rest_framework import serializers
from apps.event.models import Prtcps, Events


class EventRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for event registration response"""
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_location = serializers.CharField(source='event.location', read_only=True)
    event_start_date = serializers.DateField(source='event.st_date', read_only=True)
    event_end_date = serializers.DateField(source='event.end_date', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    
    class Meta:
        model = Prtcps
        fields = [
            'event',
            'event_title',
            'event_location',
            'event_start_date',
            'event_end_date',
            'student',
            'student_name',
            'status',
            'rank',
            'reward'
        ]
        read_only_fields = ['status', 'rank', 'reward']