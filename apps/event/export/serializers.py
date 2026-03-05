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
    committee_preparation = serializers.CharField(required=False, allow_blank=True, max_length=200)
    committee_organizing = serializers.CharField(required=False, allow_blank=True, max_length=200)
    committee_execution = serializers.CharField(required=False, allow_blank=True, max_length=200)
    committee_purchases = serializers.CharField(required=False, allow_blank=True, max_length=200)
    committee_supervision = serializers.CharField(required=False, allow_blank=True, max_length=200)
    committee_other = serializers.CharField(required=False, allow_blank=True, max_length=200)
    
    evaluation = serializers.ChoiceField(
        required=False,
        choices=[
            ('excellent', 'ممتاز'),
            ('very_good', 'جيد جدا'),
            ('good', 'جيد'),
            ('average', 'متوسط')
        ]
    )
    
    suggestions = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list
    )
    
    def validate_project_stages(self, value):
        if len(value) > 290:
            raise serializers.ValidationError("Project stages must not exceed 290 characters.")
        return value
    
    def validate_preparation_stage(self, value):
        if len(value) > 290:
            raise serializers.ValidationError("Preparation stage must not exceed 290 characters.")
        return value
    
    def validate_execution_stage(self, value):
        if len(value) > 290:
            raise serializers.ValidationError("Execution stage must not exceed 290 characters.")
        return value
    
    def validate_evaluation_stage(self, value):
        if len(value) > 290:
            raise serializers.ValidationError("Evaluation stage must not exceed 290 characters.")
        return value
    
    def validate_achieved_goals(self, value):
        if len(value) > 290:
            raise serializers.ValidationError("Achieved goals must not exceed 290 characters.")
        return value
    def validate_committee_preparation(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Preparation committee must not exceed 50 characters")
        return value
    
    def validate_committee_organizing(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Organizing committee must not exceed 50 characters")
        return value
    
    def validate_committee_execution(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Execution committee must not exceed 50 characters")
        return value
    
    def validate_committee_purchases(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Procurement committee must not exceed 50 characters")
        return value
    
    def validate_committee_supervision(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Supervision committee must not exceed 50 characters")
        return value
    
    def validate_committee_other(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Other committee field must not exceed 50 characters")
        return value
    
    def validate_suggestions(self, value):
        if len(value) > 3:
            raise serializers.ValidationError("Maximum 3 suggestions are allowed")
        for i, suggestion in enumerate(value):
            if len(suggestion) > 290:
                raise serializers.ValidationError(f"Suggestion {i+1} must not exceed 290 characters")
        return value