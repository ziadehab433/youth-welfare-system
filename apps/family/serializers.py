from rest_framework import serializers
from apps.family.models import *
from apps.accounts.models import Students 
from apps.solidarity.models import Faculties ,Departments

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

class FamiliesDetailSerializer(serializers.ModelSerializer):
    family_members = serializers.SerializerMethodField()
    faculty_name = serializers.CharField(source='faculty.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, allow_null=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Families
        fields = ['family_id', 'name', 'description', 'faculty', 'faculty_name', 'status', 
                  'created_at', 'updated_at', 'min_limit', 'type', 'created_by_name', 
                  'approved_by_name', 'family_members']
        read_only_fields = ['family_id', 'created_at', 'updated_at']
    
    def get_family_members(self, obj):
        """Get family members from manually attached queryset"""
        if hasattr(obj, 'family_members_list'):
            members = obj.family_members_list
        else:
            members = FamilyMembers.objects.filter(family_id=obj.family_id).select_related('student', 'dept')
        
        return FamilyMembersSerializer(members, many=True).data
    




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
    role = serializers.CharField()  # 'رئيس لجنة' or 'نائب رئيس لجنة'
    
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
            role='رئيس'
        ).select_related('student').first()
        
        return president.student.name if president else None
    
    def get_vice_president_name(self, obj):
        """Get vice president's name"""
        vice_president = FamilyMembers.objects.filter(
            family=obj,
            role='نائب رئيس'
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
            role__in=['رئيس', 'نائب رئيس']
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
            role='رئيس لجنة'
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
            role='نائب رئيس لجنة'
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