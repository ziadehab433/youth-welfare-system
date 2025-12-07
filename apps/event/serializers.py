from rest_framework import serializers
from apps.event.models import Events

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = '__all__'  
