from apps.family.models import Families, FamilyMembers
from apps.accounts.models import AdminsUser
from django.core.exceptions import ValidationError
from django.db.models import Count, F
from django.utils import timezone
from django.db import transaction
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
        



    @staticmethod
    def get_families_for_student(student):
        """Get all families the student is a member of"""
        return FamilyMembers.objects.filter(
            student=student,
            status='مقبول' 
        ).select_related('family', 'family__faculty').order_by('-joined_at')
    
    @staticmethod
    def get_available_families_for_student(student):
        """Get families available for student to join"""
        
        if not student.faculty:
            return []  # Student has no faculty, no families available
        
        # Get families where student is already a member
        student_family_ids = FamilyMembers.objects.filter(
            student=student
        ).values_list('family_id', flat=True)
        
        # Get all active families
        available_families = Families.objects.annotate(
            current_members=Count('family_members')
        ).filter(
            status='مقبول'
        ).exclude(
            family_id__in=student_family_ids
        ).filter(
            current_members__lt=F('min_limit')  # Not full
        ).select_related('faculty')
        
        # Filter by faculty and type in Python for clarity
        filtered_families = []
        for family in available_families:
            if family.type == 'مركزية':
                # Central family - available to all
                filtered_families.append(family)
            elif family.type in ['نوعية', 'اصدقاء البيئة']:  
                # Same faculty required
                if family.faculty_id == student.faculty_id:  
                    filtered_families.append(family)
        
        return filtered_families
    

    @staticmethod
    def get_family_members(family_id, requester_student=None):
        """
        Get all members of a family
        
        Only students with role 'اخ اكبر' or 'اخت كبرى' (founders) can view members
        
        Args:
            family_id: ID of the family
            requester_student: The student requesting
        """
        try:
            family = Families.objects.get(family_id=family_id)
        except Families.DoesNotExist:
            raise ValidationError("Family not found")
        
        # Check if requester is a member with founder role
        if not requester_student:
            raise ValidationError("Authentication required")
        
        founder_roles = ['اخ اكبر', 'اخت كبرى' ,'رئيس' , 'نائب رئيس']
        
        is_founder = FamilyMembers.objects.filter(
            family=family,
            student=requester_student,
            role__in=founder_roles
        ).exists()
        
        if not is_founder:
            raise ValidationError("Only family founders can view members")
        
        # Get family members
        members = FamilyMembers.objects.filter(
            family=family
        ).select_related('student', 'dept').order_by('-joined_at')
        
        return family, members
    





    @staticmethod
    def join_family(family_id, student):

        """
        Join a family with validation
        
        Args:
            family_id: ID of family to join
            student: Student object trying to join
            
        Returns:
            FamilyMembers instance created
            
        Raises:
            ValidationError: If student can't join
        """
        
        if not student.faculty:
            raise ValidationError("Student is not assigned to any faculty")
        
        try:
            family = Families.objects.get(family_id=family_id)
        except Families.DoesNotExist:
            raise ValidationError("Family not found")
        
        # Check 1: Family status must be active
        if family.status != 'مقبول':
            raise ValidationError(f"Family is not open for joining (Status: {family.status})")
        
        # Check 2: Student not already a member
        is_member = FamilyMembers.objects.filter(
            family=family,
            student=student
        ).exists()
        
        if is_member:
            raise ValidationError("You are already a member of this family")
        
        # Check 3: Faculty and type criteria
        if family.type == 'مركزية':
            # Central family - available to all
            pass
        elif family.type in ['نوعية', 'اصدقاء البيئة']:
            # Same faculty required
            if family.faculty != student.faculty:
                raise ValidationError(f"This family is only for {family.faculty.name} faculty")
        else:
            raise ValidationError(f"Unknown family type: {family.type}")
        
        # Check 4: Family not full
        current_count = FamilyMembers.objects.filter(family=family).count()
        if current_count >= family.min_limit:
            raise ValidationError(f"Family is full ({current_count}/{family.min_limit} members)")
        
        # Check 5: Verify min_limit is reasonable
        if current_count >= family.min_limit:
            raise ValidationError("Family has reached maximum capacity")
        
        # Create membership
        try:
            with transaction.atomic():
                member = FamilyMembers.objects.create(
                    family=family,
                    student=student,
                    role='عضو',  # Default role for new members
                    status='مقبول',  # Default status
                    joined_at=timezone.now(),
                    dept=None  # Can be updated later by admin
                )
                return member
        except Exception as e:
            raise ValidationError(f"Error joining family: {str(e)}")
        




    @staticmethod
    def check_pending_requests(student):
        """
        Check if student (president) already has a pending family request
        
        Args:
            student: Student object
            
        Returns:
            Pending family if exists, None otherwise
            
        Raises:
            ValidationError: If student already has a pending request
        """
        
        # Check if this student is a president (رئيس) of any pending family
        pending_family = FamilyMembers.objects.filter(
            student=student,
            role='رئيس',
            family__status='منتظر'
        ).select_related('family').first()
        
        if pending_family:
            raise ValidationError(
                f"You already have a pending family request: '{pending_family.family.name}'. "
                f"Please wait for it to be reviewed or cancelled before creating a new one."
            )
        
        return None


    @staticmethod
    def create_family_request(request_data, created_by_student):
        """
        Create a new family request with founders
        
        Args:
            request_data: Dict containing name, description, faculty_id, founders
            created_by_student: Student creating the request (will be recorded)
            
        Returns:
            Families instance
            
        Raises:
            ValidationError: If validation fails
        """
        
        # Check if president already has a pending request
        FamilyService.check_pending_requests(request_data['founders']['president'])
        
        # Additional check: Ensure president is not already president of an approved family
        existing_family = FamilyMembers.objects.filter(
            student=request_data['founders']['president'],
            role='رئيس',
            family__status__in=['مقبول']
        ).select_related('family').first()
        
        if existing_family:
            raise ValidationError(
                f"You are already president of '{existing_family.family.name}'. "
                f"Each student can only be president of one family."
            )
        
        try:
            with transaction.atomic():
                # Create the family
                family = Families.objects.create(
                    name=request_data['name'],
                    description=request_data['description'],
                    faculty=request_data['faculty'],
                    type='نوعية',
                    status='منتظر',
                    min_limit=15,
                    created_by_id=1,
                    created_at=timezone.now()
                )
                
                # Create president member
                president = request_data['founders']['president']
                FamilyMembers.objects.create(
                    family=family,
                    student=president,
                    role='رئيس',
                    status='مقبول',
                    joined_at=timezone.now(),
                    dept_id=None
                )
                
                # Create vice president member
                vice_president = request_data['founders']['vice_president']
                FamilyMembers.objects.create(
                    family=family,
                    student=vice_president,
                    role='نائب رئيس',
                    status='مقبول',
                    joined_at=timezone.now(),
                    dept_id=None
                )
                
                # Create committee heads (7 total)
                for head in request_data['founders']['committee_heads']:
                    FamilyMembers.objects.create(
                        family=family,
                        student=head['student'],
                        role='رئيس لجنة',
                        status='مقبول',
                        joined_at=timezone.now(),
                        dept=head['dept']
                    )
                
                # Create committee assistants (7 total)
                for assistant in request_data['founders']['committee_assistants']:
                    FamilyMembers.objects.create(
                        family=family,
                        student=assistant['student'],
                        role='نائب رئيس لجنة',
                        status='مقبول',
                        joined_at=timezone.now(),
                        dept=assistant['dept']
                    )
                
                return family
        
        except Exception as e:
            raise ValidationError(f"Error creating family request: {str(e)}")
        





    @staticmethod
    def get_student_family_requests(student):
        """
        Get all family creation requests submitted by student (as president)
        
        Args:
            student: Student object
            
        Returns:
            QuerySet of Families where student is president
        """
        
        family_requests = Families.objects.filter(
            family_members__student=student,
            family_members__role='رئيس'
        ).select_related('faculty').distinct().order_by('-created_at')
        
        return family_requests


    @staticmethod
    def get_student_family_request_detail(family_id, student):
        """
        Get detailed family creation request for a student (must be president)
        
        Args:
            family_id: ID of family
            student: Student object
            
        Returns:
            Family instance
            
        Raises:
            ValidationError: If not found or student is not president
        """
        
        try:
            family = Families.objects.select_related('faculty').get(
                family_id=family_id
            )
        except Families.DoesNotExist:
            raise ValidationError("Family request not found")
        
        # Check if student is the president of this family
        is_president = FamilyMembers.objects.filter(
            family=family,
            student=student,
            role='رئيس'
        ).exists()
        
        if not is_president:
            raise ValidationError("You are not the president of this family")
        
        return family


    @staticmethod
    def get_request_statistics(student):
        """
        Get statistics about student's family requests
        
        Args:
            student: Student object
            
        Returns:
            Dict with counts by status
        """
        
        requests = Families.objects.filter(
            family_members__student=student,
            family_members__role='رئيس'
        ).distinct()
        
        total = requests.count()
        pending = requests.filter(status='منتظر').count()
        approved = requests.filter(status='مقبول').count()
        rejected = requests.filter(status='مرفوض').count()
        
        return {
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected
        }