from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from apps.solidarity.models import Solidarities, SolidarityDocs
from apps.solidarity.models import Solidarities, SolidarityDocs, Logs, Faculties
from .utils import DISCOUNT_TYPE_MAPPING
from django.core.validators import FileExtensionValidator, RegexValidator

class SolidarityApplySerializer(serializers.Serializer):
    # Basic info
    family_numbers = serializers.IntegerField(min_value=1, max_value=50)
    reason = serializers.CharField(max_length=500, min_length=1)
    address = serializers.CharField(max_length=300, min_length=5)
    
    # Status fields
    father_status = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        max_length=100
    )
    mother_status = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        max_length=100
    )
    
    # Income validation
    father_income = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False, 
        allow_null=True, 
        min_value=0,
        max_value=999999.99  
    )
    mother_income = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False, 
        allow_null=True, 
        min_value=0,
        max_value=999999.99
    )
    
    # Phone validation with regex
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Phone number must be 9-15 digits'
    )
    f_phone_num = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[phone_regex],
        max_length=15
    )
    m_phone_num = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[phone_regex],
        max_length=15
    )
    
    # Other fields
    arrange_of_brothers = serializers.IntegerField(
        required=False, 
        allow_null=True, 
        min_value=1,
        max_value=20
    )
    grade = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    acd_status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    housing_status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    disabilities = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    sd = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    #  Enhanced file validation
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    
    social_research_file = serializers.FileField(required=True)
    salary_proof_file = serializers.FileField(required=True)
    father_id_file = serializers.FileField(required=True)
    student_id_file = serializers.FileField(required=True)
    land_ownership_file = serializers.FileField(required=False, allow_null=True)
    sd_file = serializers.FileField(required=False, allow_null=True)
    
    
    def _validate_file(self, file_obj, field_name, required=True):
        """Generic file validation"""
        if file_obj is None:
            if required:
                raise serializers.ValidationError(f"{field_name} is required")
            return file_obj
        
        # Check file size
        if file_obj.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"{field_name} exceeds {self.MAX_FILE_SIZE / (1024*1024):.0f}MB limit"
            )
        
        # Check file extension
        ext = file_obj.name.split('.')[-1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"{field_name} must be one of: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        return file_obj
    
    def validate_social_research_file(self, value):
        return self._validate_file(value, "Social research file", required=True)
    
    def validate_salary_proof_file(self, value):
        return self._validate_file(value, "Salary proof file", required=True)
    
    def validate_father_id_file(self, value):
        return self._validate_file(value, "Father ID file", required=True)
    
    def validate_student_id_file(self, value):
        return self._validate_file(value, "Student ID file", required=True)
    
    # Cross-field validation
    def validate(self, data):
        """Cross-field validation"""
        
        # If father is deceased, income should not be provided
        if data.get('father_status', '').lower() == 'متوفي':
            if data.get('father_income') and data.get('father_income') > 0:
                raise serializers.ValidationError({
                    'father_income': "Cannot set income if father is deceased"
                })
        
        # If mother is deceased, income should not be provided
        if data.get('mother_status', '').lower() == 'متوفاة':
            if data.get('mother_income') and data.get('mother_income') > 0:
                raise serializers.ValidationError({
                    'mother_income': "Cannot set income if mother is deceased"
                })
        

        
        return data
    
class SolidarityStatusSerializer(serializers.ModelSerializer):
    approved_by_name = serializers.CharField(source='approved_by.name', read_only=True, allow_null=True)

    class Meta:
        model = Solidarities
        fields = ['solidarity_id', 'req_status', 'created_at', 'updated_at', 'approved_by_name' , 'approved_by' , 'reason' , 'family_numbers' , 'total_income' , 'discount_type']


class SolidarityListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_uid = serializers.CharField(source='student.uid', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)

    class Meta:
        model = Solidarities
        fields = [
            'solidarity_id', 'student_name', 'student_uid',
            'faculty_name', 'req_status', 'total_income',
            'family_numbers', 'created_at','discount_type'
        ]

class DiscountItemSerializer(serializers.Serializer):
    """Serializer داخلي لاستقبال نوع الخصم وقيمته المخصصة."""
    
    discount_type = serializers.ChoiceField(
        choices=[
            ('full_discount', 'خصم كامل'),
            ('bk_discount', 'خصم كتاب'),
            ('reg_discount', 'خصم انتظام'),
            ('aff_discount', 'خصم انتساب'),
        ],
        help_text="نوع الخصم (English key)"
    )
    discount_value = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, 
        help_text="قيمة الخصم المراد تطبيقها"
    )

class DiscountAssignSerializer(serializers.Serializer):
    discounts = serializers.ListField(
        child=DiscountItemSerializer(),
        allow_empty=False,
        help_text="List of discounts"
    )

    
class FacultyDiscountUpdateSerializer(serializers.Serializer):
    aff_discount = serializers.ListField(
        child=serializers.FloatField(), 
        required=False, 
        help_text="قائمة بقيم خصم الانتساب"
    )
    reg_discount = serializers.ListField(
        child=serializers.FloatField(), 
        required=False, 
        help_text="قائمة بقيم خصم الانتظام"
    )
    bk_discount = serializers.ListField(
        child=serializers.FloatField(), 
        required=False, 
        help_text="قائمة بقيم خصم الكتب"
    )
    full_discount = serializers.ListField(
        child=serializers.FloatField(), 
        required=False, 
        help_text="قائمة بقيم الخصم الكامل"
    )

class SolidarityDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_uid = serializers.CharField(source='student.uid', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    # approved_by_name = serializers.CharField(source='approved_by.name', read_only=True, allow_null=True)
    # app_or_rej_by_aid =serializers.CharField(source='approved_by' ,read_only=True, allow_null=False )

    class Meta:
        model = Solidarities
        fields = '__all__'

class ApprovalSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)

class RejectionSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class SolidarityDocsSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = SolidarityDocs
        fields = ['doc_id', 'solidarity', 'doc_type', 'file_url', 'mime_type', 'file_size', 'uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        url = obj.file.url if obj.file else None
        return request.build_absolute_uri(url) if request and url else url

from rest_framework import serializers

class LogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.name', read_only=True)
    actor_role = serializers.CharField(source='actor_type', read_only=True)
    solidarity_id = serializers.IntegerField(source='solidarity.solidarity_id', read_only=True, allow_null=True)
    faculty_name = serializers.SerializerMethodField()

    class Meta:
        model = Logs
        fields = [
            'log_id', 'actor_name','actor_id', 'actor_role', 'faculty_name','action',  'target_type', 
            'solidarity_id', 'ip_address', 'logged_at'
        ]

    def get_faculty_name(self, obj):
        # Safely access faculty through actor
        try:
            return obj.actor.faculty.name if obj.actor and obj.actor.faculty else None
        except AttributeError:
            return None

class DeptFacultiesSerializer(serializers.ModelSerializer): 
    class Meta:
        model = Faculties
        fields = [
            "faculty_id", "name"
        ]

class SolidarityApprovedRowSerializer(serializers.Serializer):
    solidarity_id = serializers.IntegerField()
    student_name = serializers.CharField()
    student_id = serializers.IntegerField()
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2)



class FacultyApprovedResponseSerializer(serializers.Serializer):
    total_approved = serializers.IntegerField()
    total_discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    results = SolidarityApprovedRowSerializer(many=True)
    discount_type = serializers.ListField()


class DeptFacultySummarySerializer(serializers.Serializer):

    faculty_id = serializers.IntegerField()
    faculty_name = serializers.CharField()
    total_approved_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    approved_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
