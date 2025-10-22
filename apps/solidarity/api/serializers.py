
from drf_spectacular.utils import extend_schema_field

from rest_framework import serializers
from apps.solidarity.models import Solidarities

class SolidarityApplySerializer(serializers.Serializer):
    family_numbers = serializers.IntegerField(min_value=1)
    father_status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    mother_status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    father_income = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, min_value=0)
    mother_income = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, min_value=0)
    arrange_of_brothers = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    m_phone_num = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    f_phone_num = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    reason = serializers.CharField()
    docs = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    disabilities = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    housing_status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    grade = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    acd_status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField()

class SolidarityStatusSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    approved_by_name = serializers.CharField(source='approved_by.name', read_only=True, allow_null=True)

    class Meta:
        model = Solidarities
        fields = ['solidarity_id', 'req_status', 'status_display', 'created_at', 'updated_at', 'approved_by_name']
    @extend_schema_field(serializers.CharField())

    def get_status_display(self, obj):
        statuses = {
            'PENDING': 'Pending',
            'APPROVED': 'Approved',
            'REJECTED': 'Rejected',
            'IN_REVIEW': 'In Review',
        }
        return statuses.get(obj.req_status, obj.req_status)

class SolidarityListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_uid = serializers.CharField(source='student.uid', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)

    class Meta:
        model = Solidarities
        fields = [
            'solidarity_id', 'student_name', 'student_uid',
            'faculty_name', 'req_status', 'total_income',
            'family_numbers', 'created_at'
        ]

class SolidarityDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_uid = serializers.CharField(source='student.uid', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.name', read_only=True, allow_null=True)

    class Meta:
        model = Solidarities
        fields = '__all__'

class ApprovalSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)

class RejectionSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=False, allow_blank=True)