from rest_framework import serializers
from apps.family.models import *
from apps.accounts.models import Students 
from apps.solidarity.models import Faculties ,Departments
from apps.event.models import Events
from apps.family.constants import COMMITTEES, ADMIN_ROLES, STUDENT_ROLES, COMMITTEE_ROLES
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from apps.family.models import Families, FamilyMembers
from apps.event.models import Events, Prtcps
class FamilyMembersSerializer(serializers.ModelSerializer):
    # These fields extract nested data from the student object
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.IntegerField(source='student.student_id', read_only=True)
    national_id = serializers.IntegerField(source='student.nid' , read_only=True)
    u_id = serializers.IntegerField(source='student.uid',read_only=True)
    dept_name = serializers.CharField(source='dept.name', read_only=True, allow_null=True)
    
    class Meta:
        model = FamilyMembers
        fields = ['student_id', 'student_name', 'national_id','u_id', 'role', 'status', 'joined_at', 'dept', 'dept_name']
        read_only_fields = ['joined_at']

class FamiliesListSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, allow_null=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Families
        fields = ['family_id', 'name', 'description', 'faculty', 'faculty_name', 'status', 
                  'created_at', 'updated_at', 'min_limit', 'type', 'created_by_name', 'member_count']
        read_only_fields = ['family_id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.family_members.count()

class FamilyEventSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = ['event_id', 'title', 'type', 'st_date', 'status', 'cost']

class FamiliesDetailSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, allow_null=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True, allow_null=True)
    
    family_members = serializers.SerializerMethodField()
    family_events = serializers.SerializerMethodField()
    
    class Meta:
        model = Families
        fields = [
            'family_id', 'name', 'description', 'faculty', 'faculty_name', 'status', 
            'created_at', 'updated_at', 'min_limit', 'type', 'created_by_name', 
            'approved_by_name', 'family_members', 'family_events'
        ]
        read_only_fields = ['family_id', 'created_at', 'updated_at']
    
    def get_family_members(self, obj):
        if hasattr(obj, 'family_members_list'):
            members = obj.family_members_list
        else:
            members = FamilyMembers.objects.filter(family_id=obj.family_id).select_related('student', 'dept')
        
        return FamilyMembersSerializer(members, many=True).data

    def get_family_events(self, obj):
        events = Events.objects.filter(family=obj).order_by('-st_date')
        return FamilyEventSimpleSerializer(events, many=True).data

class CentralFamilyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Families
        fields = ['name', 'description']



# STD


class StudentFamiliesSerializer(serializers.Serializer):
    """Serializer for families from student perspective with their role"""
    family_id = serializers.IntegerField(source='family.family_id')
    name = serializers.CharField(source='family.name')
    description = serializers.CharField(source='family.description', allow_null=True)
    faculty_name = serializers.CharField(source='family.faculty.name', read_only=True, allow_null=True)
    type = serializers.CharField(source='family.type')
    status = serializers.CharField(source='family.status')
    
    # Student's membership details
    role = serializers.CharField()  # Role in this family
    member_status = serializers.CharField(source='status')  # Membership status
    joined_at = serializers.DateTimeField()
    member_count = serializers.SerializerMethodField()
    
    def get_member_count(self, obj):
        return obj.family.family_members.count()
    


class AvailableFamiliesSerializer(serializers.ModelSerializer):
    """Serializer for families available to join"""
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    member_count = serializers.SerializerMethodField()
    available_slots = serializers.SerializerMethodField()
    
    class Meta:
        model = Families
        fields = [
            'family_id', 'name', 'description', 'faculty', 'faculty_name', 
            'type', 'status', 'min_limit', 'created_at', 
            'member_count', 'available_slots'
        ]
        read_only_fields = ['family_id', 'created_at']
    
    def get_member_count(self, obj):
        return obj.family_members.count()
    
    def get_available_slots(self, obj):
        current_count = obj.family_members.count()
        return max(0, obj.min_limit - current_count)
    


class FamilyMembersDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for family members"""
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.IntegerField(source='student.student_id', read_only=True)
    national_id = serializers.IntegerField(source='student.nid', read_only=True)
    u_id = serializers.IntegerField(source='student.uid', read_only=True)
    email = serializers.EmailField(source='student.email', read_only=True)
    phone = serializers.CharField(source='student.phone_number', read_only=True, allow_null=True)
    dept_name = serializers.CharField(source='dept.name', read_only=True, allow_null=True)
    
    class Meta:
        model = FamilyMembers
        fields = [
            'student_id', 'student_name', 'national_id', 'u_id', 'email', 'phone',
            'role', 'status', 'joined_at', 'dept', 'dept_name'
        ]
        read_only_fields = ['joined_at']




class JoinFamilySerializer(serializers.Serializer):
    """Serializer for joining a family"""
    family_id = serializers.IntegerField(read_only=True)
    family_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    joined_at = serializers.DateTimeField(read_only=True)
    message = serializers.CharField(read_only=True)


class CommitteeMemberSerializer(serializers.Serializer):
    """Serializer for committee members (heads and assistants)"""
    student_id = serializers.IntegerField()
    dept_id = serializers.IntegerField()
    role = serializers.CharField()  # 'أمين لجنة' or 'أمين مساعد لجنة'
    
    def validate(self, data):
        """Validate student and department exist"""
        try:
            student = Students.objects.get(student_id=data['student_id'])
        except Students.DoesNotExist:
            raise serializers.ValidationError(f"Student {data['student_id']} not found")
        
        try:
            dept = Departments.objects.get(dept_id=data['dept_id'])
        except Departments.DoesNotExist:
            raise serializers.ValidationError(f"Department {data['dept_id']} not found")
        
        data['student'] = student
        data['dept'] = dept
        return data


class FounderSerializer(serializers.Serializer):
    """Serializer for family founders"""
    president_id = serializers.IntegerField()
    vice_president_id = serializers.IntegerField()
    committee_heads = CommitteeMemberSerializer(many=True)  # 7 heads
    committee_assistants = CommitteeMemberSerializer(many=True)  # 7 assistants
    
    def validate(self, data):
        """Validate president and vice president"""
        try:
            president = Students.objects.get(student_id=data['president_id'])
        except Students.DoesNotExist:
            raise serializers.ValidationError(f"President {data['president_id']} not found")
        
        try:
            vice_president = Students.objects.get(student_id=data['vice_president_id'])
        except Students.DoesNotExist:
            raise serializers.ValidationError(f"Vice President {data['vice_president_id']} not found")
        
        # Validate committee counts
        if len(data['committee_heads']) != 7:
            raise serializers.ValidationError("Must have exactly 7 committee heads")
        
        if len(data['committee_assistants']) != 7:
            raise serializers.ValidationError("Must have exactly 7 committee assistants")
        
        data['president'] = president
        data['vice_president'] = vice_president
        return data


class CreateFamilyRequestSerializer(serializers.Serializer):
    """Serializer for creating a new family request"""
    name = serializers.CharField(max_length=100)
    description = serializers.CharField()
    faculty_id = serializers.IntegerField()
    founders = FounderSerializer()
    
    def validate(self, data):
        """Validate faculty exists"""
        try:
            faculty = Faculties.objects.get(faculty_id=data['faculty_id'])
        except Faculties.DoesNotExist:
            raise serializers.ValidationError(f"Faculty {data['faculty_id']} not found")
        
        data['faculty'] = faculty
        return data
    


class FamilyRequestListSerializer(serializers.ModelSerializer):
    """Serializer for listing family creation requests"""
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    president_name = serializers.SerializerMethodField()
    vice_president_name = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Families
        fields = [
            'family_id', 'name', 'description', 'faculty', 'faculty_name',
            'type', 'status', 'min_limit', 'created_at', 'updated_at',
            'president_name', 'vice_president_name', 'member_count'
        ]
        read_only_fields = ['family_id', 'created_at', 'updated_at']
    
    def get_president_name(self, obj):
        """Get president's name"""
        president = FamilyMembers.objects.filter(
            family=obj,
            role='أخ أكبر'
        ).select_related('student').first()
        
        return president.student.name if president else None
    
    def get_vice_president_name(self, obj):
        """Get vice president's name"""
        vice_president = FamilyMembers.objects.filter(
            family=obj,
            role='أخت كبرى'
        ).select_related('student').first()
        
        return vice_president.student.name if vice_president else None
    
    def get_member_count(self, obj):
        """Get total members including founders"""
        return obj.family_members.count()


class FamilyRequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for family creation requests"""
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    members = serializers.SerializerMethodField()
    committee_heads = serializers.SerializerMethodField()
    committee_assistants = serializers.SerializerMethodField()
    
    class Meta:
        model = Families
        fields = [
            'family_id', 'name', 'description', 'faculty', 'faculty_name',
            'type', 'status', 'min_limit', 'created_at', 'updated_at',
            'members', 'committee_heads', 'committee_assistants'
        ]
        read_only_fields = ['family_id', 'created_at', 'updated_at']
    
    def get_members(self, obj):
        """Get president and vice president"""
        members = FamilyMembers.objects.filter(
            family=obj,
            role__in=['أخ أكبر', 'أخت كبرى']
        ).select_related('student')
        
        return [
            {
                'role': m.role,
                'student_id': m.student.student_id,
                'name': m.student.name,
                'email': m.student.email
            }
            for m in members
        ]
    
    def get_committee_heads(self, obj):
        """Get committee heads with departments"""
        heads = FamilyMembers.objects.filter(
            family=obj,
            role='أمين لجنة'
        ).select_related('student', 'dept')
        
        return [
            {
                'student_id': h.student.student_id,
                'name': h.student.name,
                'dept_id': h.dept.dept_id if h.dept else None,
                'dept_name': h.dept.name if h.dept else None,
                'email': h.student.email
            }
            for h in heads
        ]
    
    def get_committee_assistants(self, obj):
        """Get committee assistants with departments"""
        assistants = FamilyMembers.objects.filter(
            family=obj,
            role='أمين مساعد لجنة'
        ).select_related('student', 'dept')
        
        return [
            {
                'student_id': a.student.student_id,
                'name': a.student.name,
                'dept_id': a.dept.dept_id if a.dept else None,
                'dept_name': a.dept.name if a.dept else None,
                'email': a.student.email
            }
            for a in assistants
        ]   









class CreatePostSerializer(serializers.Serializer):
    """Serializer for creating posts"""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    
    def validate_title(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Title cannot be empty")
        return value
    
    def validate_description(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Description cannot be empty")
        return value


class FamilyPostSerializer(serializers.ModelSerializer):
    """Serializer for family posts"""
    family_name = serializers.CharField(source='family.name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Posts
        fields = [
            'post_id', 'title', 'description', 'family', 'family_name',
            'faculty', 'faculty_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['post_id', 'created_at', 'updated_at']







class FamilyDashboardSerializer(serializers.Serializer):
    """Serializer for family dashboard"""
    
    family = serializers.DictField()
    statistics = serializers.DictField()
    members = serializers.DictField()
    leadership = serializers.DictField()
    recent_activities = serializers.ListField()
    recent_posts = serializers.ListField()



#fam events

class CreateEventRequestSerializer(serializers.Serializer):
    """Serializer for creating event requests"""
    title = serializers.CharField(max_length=150)
    description = serializers.CharField()
    type = serializers.CharField(max_length=100)
    st_date = serializers.DateField()
    end_date = serializers.DateField()
    location = serializers.CharField(max_length=150)
    s_limit = serializers.IntegerField(required=False, allow_null=True)
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    restrictions = serializers.CharField(required=False, allow_blank=True)
    reward = serializers.CharField(required=False, allow_blank=True)
    resource = models.TextField(blank=True, null=True)
    dept_id = serializers.PrimaryKeyRelatedField(
        queryset=Departments.objects.all(),
        source='dept',
        required=True
    )

    def validate(self, data):
        """Validate dates"""
        if data['end_date'] < data['st_date']:
            raise serializers.ValidationError(
                "End date must be after or equal to start date"
            )
        return data
    
    def validate_title(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Title cannot be empty")
        return value
    
    def validate_description(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Description cannot be empty")
        return value
    def validate_dept_id(self, value):
        if not Departments.objects.filter(dept_id=value.dept_id).exists():
            raise serializers.ValidationError("Invalid dept_id")
        return value



class EventRequestResponseSerializer(serializers.ModelSerializer):
    """Serializer for event request response"""
    family_name = serializers.CharField(source='family.name', read_only=True, allow_null=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    created_by_admin_info = serializers.SerializerMethodField()
    created_by_student_info = serializers.SerializerMethodField()
    dept_id = serializers.IntegerField(source='department.dept_id', read_only=True)

    class Meta:
        model = Events
        fields = [
            'event_id', 'title', 'description', 'type', 'st_date', 'end_date',
            'location', 's_limit', 'cost', 'restrictions', 'reward', 'status',
            'family', 'family_name', 'faculty', 'faculty_name','dept_id',
            'created_by', 'created_by_admin_info','created_by_student_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'event_id', 'status', 'created_at', 'updated_at', 'created_by' 
        ]
    
    def get_family_name(self, obj):
        """Get family name"""
        if obj.family:
            return obj.family.name
        return None
    
    def get_faculty_name(self, obj):
        """Get faculty name"""
        if obj.faculty:
            return obj.faculty.name
        return None
    
    def get_created_by_admin_info(self, obj):
        """Get faculty admin info who will review this event"""
        if obj.created_by:
            return {
                'admin_id': obj.created_by.admin_id,
                'name': getattr(obj.created_by, 'name', None) or 
                        getattr(obj.created_by, 'full_name', None) or
                        getattr(obj.created_by, 'admin_name', None),
                'faculty_id': obj.created_by.faculty_id,
                'email': getattr(obj.created_by, 'email', None),
                'role': 'مسؤول كلية'
            }
        return None
    
    def get_created_by_student_info(self, obj):
        """Get student creator info from context"""
        student = self.context.get('created_by_student')
        if student:
            return {
                'student_id': student.student_id,
                'name': student.name,
                'email': student.email,
                'faculty_id': student.faculty_id if student.faculty else None,
                'role': 'Family President/Vice President'
            }
        return None

    
    def get_created_by_student_info(self, obj):
        """
        Get student creator info from context
        This is passed when creating the event
        """
        student = self.context.get('created_by_student')
        if student:
            return {
                'student_id': student.student_id,
                'name': student.name,
                'email': student.email,
                'faculty_id': student.faculty_id if student.faculty else None
            }
        return None
    

##################################################################################

#CREATATION REQUEST FAMILY



class ActivitySerializer(serializers.Serializer):
    """Serializer for individual activity/event"""
    title = serializers.CharField(max_length=150, required=True)
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )
    st_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False)
    location = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True
    )
    cost = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    def validate(self, data):
        """Validate that end_date >= st_date"""
        if data.get('end_date') and data.get('st_date'):
            if data['end_date'] < data['st_date']:
                raise ValidationError(
                    "تاريخ الانتهاء يجب أن يكون أكبر من أو يساوي تاريخ البداية"
                )
        return data


# ========== Admin Input Serializer ==========

class AdminDataSerializer(serializers.Serializer):
    """Serializer for admin/employee person data"""
    name = serializers.CharField(max_length=255, required=True)
    nid = serializers.IntegerField(required=True)  # National ID
    ph_no = serializers.IntegerField(required=True)  # Phone number

    def validate_nid(self, value):
        """Validate national ID"""
        if value <= 0:
            raise ValidationError("رقم الهوية يجب أن يكون رقماً موجباً")
        return value

    def validate_ph_no(self, value):
        """Validate phone number"""
        if value <= 0:
            raise ValidationError("رقم الهاتف يجب أن يكون رقماً موجباً")
        return value


# ========== Student Input Serializer ==========

class StudentDataSerializer(serializers.Serializer):
    """Serializer for student person reference using UID (University ID)"""
    uid = serializers.IntegerField(required=True)  # University ID / student_id

    def validate_uid(self, value):
        """Validate student exists by UID"""
        if not Students.objects.filter(uid=value).exists():
            raise ValidationError(f"الطالب برقم الجامعة {value} غير موجود")
        return value


# ========== Committee Person Serializer ==========

class CommitteePersonSerializer(serializers.Serializer):
    """Serializer for committee head/assistant using UID (University ID)"""
    uid = serializers.IntegerField(required=True)  # University ID / student_id
    dept_id = serializers.IntegerField(required=True)

    def validate_uid(self, value):
        """Validate student exists by UID"""
        if not Students.objects.filter(uid=value).exists():
            raise ValidationError(f"الطالب برقم الجامعة {value} غير موجود")
        return value

    def validate_dept_id(self, value):
        """Validate department exists"""
        if not Departments.objects.filter(dept_id=value).exists():
            raise ValidationError(f"القسم برقم {value} غير موجود")
        return value


# ========== Committee Data Serializer ==========

class CommitteeDataSerializer(serializers.Serializer):
    """Serializer for a complete committee with head, assistant, and activities"""
    committee_key = serializers.ChoiceField(
        choices=[c['key'] for c in COMMITTEES],
        required=True
    )
    head = CommitteePersonSerializer(required=True)
    assistant = CommitteePersonSerializer(required=True)
    activities = ActivitySerializer(many=True, required=False, allow_empty=True)

    def validate(self, data):
        """Validate head and assistant are different people"""
        if data['head']['uid'] == data['assistant']['uid']:
            raise ValidationError(
                "رئيس اللجنة ونائب الرئيس يجب أن يكونا شخصين مختلفين"
            )

        # Verify departments match
        if data['head']['dept_id'] != data['assistant']['dept_id']:
            raise ValidationError(
                "رئيس اللجنة ونائب الرئيس يجب أن يكونا من نفس القسم"
            )

        return data


# ========== Default Roles Serializer ==========

class DefaultRolesDataSerializer(serializers.Serializer):
    """Serializer for default roles with admin and student data"""

    # Admin roles
    رائد = AdminDataSerializer(required=True)
    نائب_رائد = AdminDataSerializer(required=True, source='نائب رائد')
    مسؤول = AdminDataSerializer(required=True)
    أمين_صندوق = AdminDataSerializer(required=True, source='أمين صندوق')

    # Student roles (using UID instead of student_id)
    أخ_أكبر = StudentDataSerializer(required=True, source='أخ أكبر')
    أخت_كبرى = StudentDataSerializer(required=True, source='أخت كبرى')
    أمين_سر = StudentDataSerializer(required=True, source='أمين سر')
    عضو_منتخب_1 = StudentDataSerializer(required=True, source='عضو منتخب 1')
    عضو_منتخب_2 = StudentDataSerializer(required=True, source='عضو منتخب 2')

    def validate(self, data):
        """Validate no student is assigned twice"""
        student_uids = [
            data['أخ أكبر']['uid'],
            data['أخت كبرى']['uid'],
            data['أمين سر']['uid'],
            data['عضو منتخب 1']['uid'],
            data['عضو منتخب 2']['uid'],
        ]

        if len(student_uids) != len(set(student_uids)):
            raise ValidationError("كل طالب يمكن أن يكون له دور واحد فقط")

        return data


# ========== Main Create Family Serializer ==========

class CreateFamilyRequestSerializer(serializers.Serializer):
    """Main serializer for creating family request with all details"""

    # Family Information
    family_type = serializers.ChoiceField(
        choices=['نوعية', 'مركزية'],
        required=True,
        help_text="نوع الأسرة: نوعية (متخصصة) أو مركزية"
    )
    name = serializers.CharField(max_length=100, required=True)
    description = serializers.CharField(max_length=1000, required=True)
    min_limit = serializers.IntegerField(
        default=15,
        min_value=1,
        required=False
    )

    # Faculty
    faculty_id = serializers.IntegerField(required=True)

    # Default Roles (9 people: 4 admins + 5 students)
    default_roles = DefaultRolesDataSerializer(required=True)

    # Committees (7 committees with heads, assistants, and activities)
    committees = CommitteeDataSerializer(
        many=True,
        required=True,
        help_text="7 لجان مع رؤساء ونواب ونشاطات"
    )

    def validate_faculty_id(self, value):
        """Validate faculty exists"""
        if not Faculties.objects.filter(faculty_id=value).exists():
            raise ValidationError(f"الكلية برقم {value} غير موجودة")
        return value

    def validate_committees(self, value):
        """Validate all 7 committees are present with no duplicates"""
        if len(value) != 7:
            raise ValidationError(f"يجب أن يكون لديك بالضبط 7 لجان، لديك {len(value)}")

        committee_keys = [c['committee_key'] for c in value]
        valid_keys = [com['key'] for com in COMMITTEES]

        for key in committee_keys:
            if key not in valid_keys:
                raise ValidationError(f"مفتاح اللجنة غير صحيح: {key}")

        if len(committee_keys) != len(set(committee_keys)):
            raise ValidationError("تم العثور على لجان مكررة")

        # Validate no person is assigned to multiple committee positions
        all_student_uids = []
        for committee in value:
            all_student_uids.append(committee['head']['uid'])
            all_student_uids.append(committee['assistant']['uid'])

        if len(all_student_uids) != len(set(all_student_uids)):
            raise ValidationError(
                "كل طالب يمكن أن يكون مسؤولاً عن لجنة واحدة فقط"
            )

        return value

    def validate(self, data):
        """Cross-field validation"""
        # Ensure default roles students are different from committee students
        default_role_students = [
            data['default_roles']['أخ أكبر']['uid'],
            data['default_roles']['أخت كبرى']['uid'],
            data['default_roles']['أمين سر']['uid'],
            data['default_roles']['عضو منتخب 1']['uid'],
            data['default_roles']['عضو منتخب 2']['uid'],
        ]

        committee_student_uids = []
        for committee in data['committees']:
            committee_student_uids.append(committee['head']['uid'])
            committee_student_uids.append(committee['assistant']['uid'])

        overlap = set(default_role_students) & set(committee_student_uids)
        if overlap:
            raise ValidationError(
                f"الطلاب برقم الجامعة {list(overlap)} مكلفين بأدوار افتراضية وأدوار لجان في نفس الوقت"
            )

        return data


# ========== Detail Response Serializers ==========

class FamilyAdminDetailSerializer(serializers.ModelSerializer):
    """Serializer for FamilyAdmin detail response"""
    class Meta:
        model = FamilyAdmins
        fields = ['id', 'name', 'nid', 'ph_no', 'role']
        read_only_fields = ['id']


class FamilyMemberDetailSerializer(serializers.ModelSerializer):
    """Serializer for FamilyMember detail response"""
    uid = serializers.CharField(source='student.student_id', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    dept_name = serializers.CharField(source='dept.name', read_only=True, allow_null=True)

    class Meta:
        model = FamilyMembers
        fields = [
            'uid', 'student_name', 'student_email',
            'role', 'status', 'joined_at', 'dept_name'
        ]
        read_only_fields = ['joined_at']

class ParticipantSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_nid = serializers.CharField(source='student.nid', read_only=True)
    college_id = serializers.CharField(source='student.uid', read_only=True)
    class Meta:
        model = Prtcps
        fields = ['student_name', 'student_nid', 'college_id', 'status', 'rank', 'reward']
class EventDetailSerializer(serializers.ModelSerializer):
    dept_name = serializers.CharField(source='dept.name', read_only=True, allow_null=True)
    family_name = serializers.CharField(source='family.name', read_only=True, allow_null=True)
    registered_members = serializers.SerializerMethodField()
    class Meta:
        model = Events
        fields = [
            'event_id', 'title', 'description', 'st_date', 'end_date',
            'location', 'cost', 'dept_name', 'family_name',
            'registered_members'
        ]
    def get_registered_members(self, obj):
        registrations = obj.prtcps_set.all().select_related('student').defer('student__can_create_fam')
        return ParticipantSerializer(registrations, many=True).data
    
class FamilyRequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for created family with all members and activities"""
    faculty_name = serializers.CharField(
        source='faculty.name',
        read_only=True,
        allow_null=True
    )
    admins = FamilyAdminDetailSerializer(
        source='familyadmins_set',
        many=True,
        read_only=True
    )
    student_members = serializers.SerializerMethodField()
    committees_data = serializers.SerializerMethodField()
    events = EventDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Families
        fields = [
            'family_id', 'name', 'description', 'faculty', 'faculty_name',
            'type', 'status', 'min_limit', 'created_at', 'updated_at',
            'admins', 'student_members', 'committees_data', 'events'
        ]
        read_only_fields = ['family_id', 'created_at', 'updated_at']

    def get_student_members(self, obj):
        """Get all student members grouped by role"""
        members = FamilyMembers.objects.filter(family=obj).select_related('student')

        result = {}
        for m in members:
            if m.role == 'عضو منتخب':
                if m.role not in result:
                    result[m.role] = []
                result[m.role].append({
                    'uid': m.student.student_id,
                    'name': m.student.name,
                    'email': m.student.email,
                    'role': m.role,
                    'status': m.status,
                    'joined_at': m.joined_at.isoformat() if m.joined_at else None
                })
            else:
                result[m.role] = {
                    'uid': m.student.student_id,
                    'name': m.student.name,
                    'email': m.student.email,
                    'role': m.role,
                    'status': m.status,
                    'joined_at': m.joined_at.isoformat() if m.joined_at else None
                }

        return result

    def get_committees_data(self, obj):
        """Get all committee data with heads, assistants, and activities"""
        committees = FamilyMembers.objects.filter(
            family=obj,
            role__in=['أمين لجنة', 'أمين مساعد لجنة']
        ).select_related('student', 'dept').order_by('dept_id')

        # Group by department
        committees_dict = {}
        for member in committees:
            dept_id = member.dept_id
            if dept_id not in committees_dict:
                committees_dict[dept_id] = {
                    'dept_id': dept_id,
                    'dept_name': member.dept.name if member.dept else None,
                    'head': None,
                    'assistant': None,
                    'activities': []
                }

            if member.role == 'أمين لجنة':
                committees_dict[dept_id]['head'] = {
                    'uid': member.student.student_id,
                    'name': member.student.name,
                    'email': member.student.email
                }
            elif member.role == 'أمين مساعد لجنة':
                committees_dict[dept_id]['assistant'] = {
                    'uid': member.student.student_id,
                    'name': member.student.name,
                    'email': member.student.email
                }

        # Add activities
        for committee_data in committees_dict.values():
            events = Events.objects.filter(
                family=obj,
                dept_id=committee_data['dept_id']
            ).values(
                'event_id', 'title', 'description', 'st_date', 'end_date',
                'location', 'cost'
            )
            committee_data['activities'] = list(events)

        return list(committees_dict.values())


class PreApproveFamilySerializer(serializers.Serializer):
    """Serializer for pre-approval data inputs"""
    min_limit = serializers.IntegerField(
        required=True, 
        min_value=1,
        help_text="أقل عدد مطلوب للأعضاء"
    )
    closing_date = serializers.DateField(
        required=True,
        help_text="آخر موعد مسموح للانضمام"
    )

    def validate_closing_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("تاريخ الإغلاق لا يمكن أن يكون في الماضي")
        return value



class FamilyFounderSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()
    national_id = serializers.SerializerMethodField()
    university_id = serializers.SerializerMethodField()
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Students
        fields = [
            'student_id',
            'name', 
            'email', 
            'national_id',
            'university_id',
            'phone_number',
            'faculty_name',
            'can_create_fam',
            'acd_year',
            'major',
            'gender'
        ]
        read_only_fields = fields
    
    def get_phone_number(self, obj):
        try:
            # Assuming your EncryptedTextField handles decryption automatically
            # If not, you might need: return decrypt_field(obj.phone_number)
            return str(obj.phone_number) if obj.phone_number else None
        except Exception:
            return None
    
    def get_national_id(self, obj):
        try:
            return str(obj.nid) if obj.nid else None
        except Exception:
            return None
    
    def get_university_id(self, obj):
        try:
            return str(obj.uid) if obj.uid else None
        except Exception:
            return None
        


#PUBLIC for Departments
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departments
        fields = ['dept_id', 'name']