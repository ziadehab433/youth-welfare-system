from rest_framework import serializers
from .models import Solidarities  # adjust name based on your table

class SolidaritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Solidarities
        fields = '__all__'  # or list specific fields
