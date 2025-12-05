from rest_framework import serializers
from apps.family.models import Families, FamilyMembers

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