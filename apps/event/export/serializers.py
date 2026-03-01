from rest_framework import serializers

class EventReportSerializer(serializers.Serializer):
    event_title = serializers.CharField(required=False, allow_blank=True, max_length=200)
    event_code = serializers.CharField(required=False, allow_blank=True, max_length=50)
    male_count = serializers.IntegerField(required=False, min_value=0)
    female_count = serializers.IntegerField(required=False, min_value=0)
    total_participants = serializers.IntegerField(required=False, min_value=0)
    start_date = serializers.CharField(required=False, allow_blank=True, max_length=20)
    duration_days = serializers.IntegerField(required=False, min_value=0)
    project_stages = serializers.CharField(required=False, allow_blank=True, max_length=500)
    preparation_stage = serializers.CharField(required=False, allow_blank=True, max_length=500)
    execution_stage = serializers.CharField(required=False, allow_blank=True, max_length=500)
    evaluation_stage = serializers.CharField(required=False, allow_blank=True, max_length=500)
    achieved_goals = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_project_stages(self, value):
        if len(value) > 290:
            raise serializers.ValidationError("Project stages must not exceed 500 characters.")
        return value
    
    def validate_preparation_stage(self, value):
        if len(value) > 290:
            raise serializers.ValidationError("Preparation stage must not exceed 500 characters.")
        return value
    
    def validate_execution_stage(self, value):
        if len(value) > 290:
            raise serializers.ValidationError("Execution stage must not exceed 500 characters.")
        return value
    
    def validate_evaluation_stage(self, value):
        if len(value) > 290:
            raise serializers.ValidationError("Evaluation stage must not exceed 500 characters.")
        return value
    
    def validate_achieved_goals(self, value):
        if len(value) > 290:
            raise serializers.ValidationError("Achieved goals must not exceed 500 characters.")
        return value