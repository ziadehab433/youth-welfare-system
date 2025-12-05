from apps.family.models import Families, FamilyMembers
from apps.accounts.models import AdminsUser
from django.core.exceptions import ValidationError

class FamilyService:
    
    @staticmethod
    def get_families_for_faculty(admin):
        """Get all families for the faculty of the current admin"""
        if not admin.faculty:
            raise ValidationError("Admin is not associated with any faculty")
        
        return Families.objects.filter(
            faculty=admin.faculty
        ).select_related('faculty', 'created_by', 'approved_by')
    
    @staticmethod
    def get_family_detail(family_id, admin):
        """Get specific family details with members"""
        try:
            family = Families.objects.select_related(
                'faculty', 'created_by', 'approved_by'
            ).get(family_id=family_id)
            
            # Ensure admin belongs to same faculty
            if family.faculty != admin.faculty:
                raise ValidationError("This family does not belong to your faculty")
            
            # Fetch family members separately to avoid id column issue
            family_members = FamilyMembers.objects.filter(
                family_id=family_id
            ).select_related('student', 'dept')
            
            # Attach members to family object for serializer
            family.family_members_list = family_members
            
            return family
        except Families.DoesNotExist:
            raise ValidationError("Family not found")