from rest_framework import serializers
from apps.event.models import Events

class EventSerializer(serializers.ModelSerializer):
    family_name = serializers.CharField(
        source='family.name',
        read_only=True,
        allow_null=True
    )
    class Meta:
        model = Events
        fields = '__all__'
class ParticipantActionSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(help_text="The ID of the student to manage")