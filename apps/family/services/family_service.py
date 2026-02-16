from apps.family.models import *
from apps.accounts.models import AdminsUser , Students
from apps.solidarity.models import Departments, Faculties
from apps.event.models import Events, Prtcps

from django.core.exceptions import ValidationError
from django.db.models import Count, F
from django.utils import timezone
from django.db import transaction
from apps.family.models import Posts    
from apps.event.models import Events
from apps.family.constants import COMMITTEES, ADMIN_ROLES, STUDENT_ROLES, COMMITTEE_ROLES
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

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
            #status='مقبول' 
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
            status__in=['موافقة مبدئية', 'مقبول']
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
        
        founder_roles = ['أخ أكبر' , 'أخت كبرى']
        
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
        
        # Check 1: Family status must be approved
        if family.status != 'مقبول' and family.status != 'موافقة مبدئية':
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
                    status='منتظر',  # Default status
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
            role='أخ أكبر',
            family__status='منتظر'
        ).select_related('family').first()
        
        if pending_family:
            raise ValidationError(
                f"You already have a pending family request: '{pending_family.family.name}'. "
                f"Please wait for it to be reviewed or cancelled before creating a new one."
            )
        
        return None



##########33
#CREATE REQUEST TO CREATE A FAMMILY

    @staticmethod
    def get_committee_by_key(committee_key):
        """Get committee configuration by key"""
        for committee in COMMITTEES:
            if committee['key'] == committee_key:
                return committee
        return None

    @staticmethod
    def check_student_duplicate_roles(student):
        """
        Check if student already has a default role in any active family
        """
        existing_role = FamilyMembers.objects.filter(
            student=student,
            role__in=STUDENT_ROLES,
            family__status__in=['مقبول']
        ).select_related('family').first()

        if existing_role:
            raise ValidationError(
                f"الطالب برقم {student.student_id} مسؤول بالفعل عن دور '{existing_role.role}' "
                f"في '{existing_role.family.name}'. كل طالب يمكن أن يكون له دور واحد فقط."
            )

    @staticmethod
    def check_student_pending_request(student):
        """
        Check if student already has a pending family request
        """
        pending_family = FamilyMembers.objects.filter(
            student=student,
            family__status='منتظر'
        ).select_related('family').first()

        if pending_family:
            raise ValidationError(
                f"الطالب برقم {student.student_id} لديه بالفعل طلب أسرة قيد الانتظار: "
                f"'{pending_family.family.name}'. يرجى الانتظار لمراجعته."
            )

    @staticmethod
    def get_student_by_uid(uid):
        """
        Get student by UID (University ID / student_id)
        
        Args:
            uid: Student University ID
            
        Returns:
            Student object
            
        Raises:
            ValidationError: If student not found
        """
        try:
            return Students.objects.get(uid=uid)
        except Students.DoesNotExist:
            raise ValidationError(f"الطالب برقم الجامعة {uid} غير موجود")

    @staticmethod
    def create_family_request(request_data, created_by_student, user_id):
        """
        Create a new family request with all founders, committees, and activities

        Args:
            request_data: Validated dict containing family and member data
            created_by_student: Student creating the request

        Returns:
            Families instance

        Raises:
            ValidationError: If validation fails
        """

        try:
            with transaction.atomic():
                # Get faculty
                try:
                    faculty = Faculties.objects.get(
                        faculty_id=request_data['faculty_id']
                    )
                except Faculties.DoesNotExist:
                    raise ValidationError(
                        f"الكلية برقم {request_data['faculty_id']} غير موجودة"
                    )

                if created_by_student:
                    # Create the family
                    family = Families.objects.create(
                        name=request_data['name'],
                        description=request_data['description'],
                        faculty=faculty,
                        type=request_data['family_type'],
                        status='منتظر',
                        min_limit=request_data.get('min_limit', 50),
                        created_by_id=user_id,  # Admin user ID
                        created_at=timezone.now()
                    )
                else:
                    family = Families.objects.create(
                        name=request_data['name'],
                        description=request_data['description'],
                        faculty=faculty,
                        type="اصدقاء البيئة",
                        status='منتظر',
                        min_limit=request_data.get('min_limit', 50),
                        created_by_id=user_id,  # Admin user ID
                        created_at=timezone.now()
                    )

                # ===== Create Default Role Members =====
                FamilyService._create_default_role_members(
                    family,
                    request_data['default_roles']
                )

                # ===== Create Committee Members and Events =====
                FamilyService._create_committees_with_activities(
                    family,
                    request_data['committees']
                )
                
                # ===== Create Participants for Environment Family =====
                if not created_by_student and 'participants' in request_data:
                    FamilyService._create_participant_members(
                        family,
                        request_data['participants']
                    )

                return family

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"خطأ في إنشاء طلب الأسرة: {str(e)}")

    @staticmethod
    def _create_participant_members(family, participant_nids):
        """
        Create family members for participants using their NIDs
        
        Args:
            family: Families instance
            participant_nids: List of NIDs for participants
        """
        try:
            from django.db import connection
            
            # Get all students by NID
            students = Students.objects.filter(nid__in=participant_nids)
            
            # Create a map for quick lookup
            student_by_nid = {student.nid: student for student in students}
            
            with connection.cursor() as cursor:
                for nid in participant_nids:
                    if nid in student_by_nid:
                        student = student_by_nid[nid]
                        
                        # Check if student already exists in family
                        if not FamilyMembers.objects.filter(
                            family=family,
                            student=student
                        ).exists():
                            
                            # Execute INSERT query
                            cursor.execute(
                                """
                                INSERT INTO family_members 
                                (family_id, student_id, role, status, joined_at, dept_id)
                                VALUES (%s, %s, %s::family_members_roles, %s, NOW(), NULL)
                                """,
                                [family.family_id, student.student_id, 'عضو', 'منتظر']
                            )
                
        except Exception as e:
            raise ValidationError(f"خطأ في إضافة المشاركين: {str(e)}")

    @staticmethod
    def _create_default_role_members(family, default_roles_data):
        """
        Create FamilyAdmins and FamilyMembers for all 9 default roles

        Args:
            family: Families instance
            default_roles_data: Dict with role names and person data
        """

        # ===== Create Admin Roles in FamilyAdmins Table =====
        admin_roles_mapping = {
            'رائد': 'رائد',
            'نائب رائد': 'نائب رائد',
            'مسؤول': 'مسؤول',
            'أمين صندوق': 'أمين صندوق',
        }

        for data_key, role_name in admin_roles_mapping.items():
            if data_key not in default_roles_data:
                raise ValidationError(f"الدور المفقود: {data_key}")

            admin_data = default_roles_data[data_key]

            # Create admin record in FamilyAdmins table
            FamilyAdmins.objects.create(
                family=family,
                name=admin_data['name'],
                nid=admin_data['nid'],
                ph_no=admin_data['ph_no'],
                role=role_name
            )

        # ===== Create Student Roles in FamilyMembers Table =====
        student_roles_mapping = {
            'أخ أكبر': 'أخ أكبر',
            'أخت كبرى': 'أخت كبرى',
            'أمين سر': 'أمين سر',
        }

        for data_key, role_name in student_roles_mapping.items():
            if data_key not in default_roles_data:
                raise ValidationError(f"الدور المفقود: {data_key}")

            person_data = default_roles_data[data_key]
            student_uid = person_data['uid']

            # Get student by UID
            student = FamilyService.get_student_by_uid(student_uid)

            # Check validations
            FamilyService.check_student_duplicate_roles(student)
            FamilyService.check_student_pending_request(student)

            FamilyMembers.objects.create(
                family=family,
                student=student,
                role=role_name,
                status='مقبول',
                joined_at=timezone.now(),
                dept=None
            )

        # ===== Create 2 Elected Members =====
        elected_members_data = [
            default_roles_data.get('عضو منتخب 1'),
            default_roles_data.get('عضو منتخب 2')
        ]

        for elected_data in elected_members_data:
            if not elected_data:
                raise ValidationError("أعضاء منتخبون مفقودون (عضو منتخب)")

            student_uid = elected_data['uid']

            # Get student by UID
            student = FamilyService.get_student_by_uid(student_uid)

            # Check validations
            FamilyService.check_student_duplicate_roles(student)
            FamilyService.check_student_pending_request(student)

            FamilyMembers.objects.create(
                family=family,
                student=student,
                role='عضو منتخب',
                status='مقبول',
                joined_at=timezone.now(),
                dept=None
            )

    @staticmethod
    def _create_committees_with_activities(family, committees_data):
        """
        Create committee members and their activities/events

        Args:
            family: Families instance
            committees_data: List of committee configurations
        """

        for committee_data in committees_data:
            committee_key = committee_data['committee_key']

            # Get committee configuration
            committee_config = FamilyService.get_committee_by_key(committee_key)
            if not committee_config:
                raise ValidationError(f"مفتاح اللجنة غير صحيح: {committee_key}")

            # Get head and assistant student objects by UID
            try:
                head_student = FamilyService.get_student_by_uid(
                    committee_data['head']['uid']
                )
                assistant_student = FamilyService.get_student_by_uid(
                    committee_data['assistant']['uid']
                )
            except ValidationError as e:
                raise e

            # Get department
            try:
                dept = Departments.objects.get(
                    dept_id=committee_data['head']['dept_id']
                )
            except Departments.DoesNotExist:
                raise ValidationError(
                    f"القسم برقم {committee_data['head']['dept_id']} غير موجود"
                )

            # Create committee head
            FamilyMembers.objects.create(
                family=family,
                student=head_student,
                role='أمين لجنة',
                status='مقبول',
                joined_at=timezone.now(),
                dept=dept
            )

            # Create committee assistant
            FamilyMembers.objects.create(
                family=family,
                student=assistant_student,
                role='أمين مساعد لجنة',
                status='مقبول',
                joined_at=timezone.now(),
                dept=dept
            )

            # Create activities/events for this committee
            if 'activities' in committee_data and committee_data['activities']:
                for activity in committee_data['activities']:
                    Events.objects.create(
                        title=activity['title'],
                        description=activity.get('description', ''),
                        family=family,
                        dept=dept,
                        faculty=family.faculty,
                        created_by_id=1,  # Admin user
                        st_date=activity['st_date'],
                        end_date=activity['end_date'],
                        location=activity.get('location', ''),
                        cost=Decimal(str(activity['cost'])) if activity.get('cost') else None,
                        type='اسر',
                        status='منتظر'
                    )

##################################

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
            family_members__role='أخ أكبر'
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
            role='أخ أكبر'
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
            family_members__role='أخ أكبر'
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
    
########POSTS#########


    
    @staticmethod
    def create_family_post(family_id, student, title, description):
        """
        Create a new post in a family
        
        Only students with role 'أخ أكبر' or 'أخت كبرى' can create posts
        
        Args:
            family_id: ID of family
            student: Student object
            title: Post title
            description: Post description
            
        Returns:
            Posts instance
            
        Raises:
            ValidationError: If validation fails
        """
        
        try:
            family = Families.objects.get(family_id=family_id)
        except Families.DoesNotExist:
            raise ValidationError("Family not found")
        
        # Check if student is member of family with required role
        allowed_roles = ['أخ أكبر', 'أخت كبرى']
        
        member = FamilyMembers.objects.filter(
            family=family,
            student=student,
            role__in=allowed_roles
        ).first()
        
        if not member:
            raise ValidationError(
                "Only family president or vice president can create posts"
            )
        
        # Create post
        try:
            post = Posts.objects.create(
                title=title,
                description=description,
                family=family,
                faculty=family.faculty
            )
            return post
        except Exception as e:
            raise ValidationError(f"Error creating post: {str(e)}")
    
    
    @staticmethod
    def get_family_posts(family_id, student):
        """
        Get all posts in a family
        
        Only students who are members of the family can view posts
        
        Args:
            family_id: ID of family
            student: Student object
            
        Returns:
            QuerySet of Posts
            
        Raises:
            ValidationError: If student is not member
        """
        
        try:
            family = Families.objects.get(family_id=family_id)
        except Families.DoesNotExist:
            raise ValidationError("Family not found")
        
        # Check if student is member of family
        is_member = FamilyMembers.objects.filter(
            family=family,
            student=student
        ).exists()
        
        if not is_member:
            raise ValidationError("You are not a member of this family")
        
        # Get all posts for this family
        posts = Posts.objects.filter(
            family=family
        ).select_related('family', 'faculty').order_by('-created_at')
        
        return posts
    
    #If we need to get a publia access for all students for all posts    
    # @staticmethod
    # def get_family_posts_no_restriction(family_id):
    #     """
    #     Get all posts in a family (for public viewing, no member check)
        
    #     Args:
    #         family_id: ID of family
            
    #     Returns:
    #         QuerySet of Posts
            
    #     Raises:
    #         ValidationError: If family not found
    #     """
        
    #     try:
    #         family = Families.objects.get(family_id=family_id)
    #     except Families.DoesNotExist:
    #         raise ValidationError("Family not found")
        
    #     posts = Posts.objects.filter(
    #         family=family
    #     ).select_related('family', 'faculty').order_by('-created_at')
        
    #     return posts                    



# DASHBOARD



    
    @staticmethod
    def get_family_dashboard(family_id, student):
        """
        Get comprehensive family dashboard data for founder
        
        Args:
            family_id: ID of family
            student: Student object (must be founder/president)
            
        Returns:
            Dict with dashboard data
            
        Raises:
            ValidationError: If not found or not founder
        """
        
        try:
            family = Families.objects.select_related('faculty').get(
                family_id=family_id
            )
        except Families.DoesNotExist:
            raise ValidationError("Family not found")
        
        # Check if student is founder (president or vice president)
        is_founder = FamilyMembers.objects.filter(
            family=family,
            student=student,
            role__in=['أخ أكبر', 'أخت كبرى']
        ).exists()
        
        if not is_founder:
            raise ValidationError("You are not a founder of this family")
        
        # Get statistics
        stats = FamilyService._get_statistics(family)
        
        # Get members info
        members_info = FamilyService._get_members_info(family)
        
        # Get leadership (president, vice president, committee heads)
        leadership = FamilyService._get_leadership(family)
        
        # Get recent activities/events
        recent_activities = FamilyService._get_recent_activities(family)
        
        # Get recent posts
        recent_posts = FamilyService._get_recent_posts(family)
        
        return {
            'family': {
                'family_id': family.family_id,
                'name': family.name,
                'description': family.description,
                'type': family.type,
                'status': family.status,
                'faculty': {
                    'faculty_id': family.faculty.faculty_id if family.faculty else None,
                    'name': family.faculty.name if family.faculty else None
                },
                'created_at': family.created_at,
                'updated_at': family.updated_at
            },
            'statistics': stats,
            'members': members_info,
            'leadership': leadership,
            'recent_activities': recent_activities,
            'recent_posts': recent_posts
        }
    
    
    @staticmethod
    def _get_statistics(family):
        """Get family statistics"""
        total_members = FamilyMembers.objects.filter(family=family).count()
        
        roles_breakdown = FamilyMembers.objects.filter(
            family=family
        ).values('role').annotate(count=Count('student_id'))
        
        # Count events (from Events table)
        try:
            from apps.accounts.models import Events
            events_count = Events.objects.filter(family=family).count()
        except:
            events_count = 0
        
        # Count posts
        posts_count = Posts.objects.filter(family=family).count()
        
        return {
            'total_members': total_members,
            'events_count': events_count,
            'posts_count': posts_count,
            'roles_breakdown': [
                {
                    'role': item['role'],
                    'count': item['count']
                }
                for item in roles_breakdown
            ]
        }
    
    
    @staticmethod
    def _get_members_info(family):
        """Get active members count and breakdown"""
        active_members = FamilyMembers.objects.filter(
            family=family,
            status='مقبول'
        ).count()
        
        pending_members = FamilyMembers.objects.filter(
            family=family,
            status='منتظر'
        ).count()
        
        return {
            'total': FamilyMembers.objects.filter(family=family).count(),
            'active': active_members,
            'pending': pending_members
        }
    
    
    @staticmethod
    def _get_leadership(family):
        """Get leadership structure"""
        leadership = {
            'president': None,
            'vice_president': None,
            'committee_heads': [],
            'committee_assistants': []
        }
        
        # Get president
        president = FamilyMembers.objects.filter(
            family=family,
            role='أخ أكبر'
        ).select_related('student').first()
        
        if president:
            leadership['president'] = {
                'student_id': president.student.student_id,
                'name': president.student.name,
                'email': president.student.email,
                'faculty_id': president.student.faculty_id if president.student.faculty else None,
                'role': president.role
            }
        
        # Get vice president
        vice_president = FamilyMembers.objects.filter(
            family=family,
            role='أخت كبرى'
        ).select_related('student').first()
        
        if vice_president:
            leadership['vice_president'] = {
                'student_id': vice_president.student.student_id,
                'name': vice_president.student.name,
                'email': vice_president.student.email,
                'faculty_id': vice_president.student.faculty_id if vice_president.student.faculty else None,
                'role': vice_president.role
            }
        
        # Get committee heads
        heads = FamilyMembers.objects.filter(
            family=family,
            role='أمين لجنة'
        ).select_related('student', 'dept')
        
        leadership['committee_heads'] = [
            {
                'student_id': head.student.student_id,
                'name': head.student.name,
                'email': head.student.email,
                'dept_id': head.dept.dept_id if head.dept else None,
                'dept_name': head.dept.name if head.dept else None,
                'role': head.role
            }
            for head in heads
        ]
        
        # Get committee assistants
        assistants = FamilyMembers.objects.filter(
            family=family,
            role='أمين مساعد لجنة'
        ).select_related('student', 'dept')
        
        leadership['committee_assistants'] = [
            {
                'student_id': assistant.student.student_id,
                'name': assistant.student.name,
                'email': assistant.student.email,
                'dept_id': assistant.dept.dept_id if assistant.dept else None,
                'dept_name': assistant.dept.name if assistant.dept else None,
                'role': assistant.role
            }
            for assistant in assistants
        ]
        
        return leadership
    
    
    @staticmethod
    def _get_recent_activities(family, limit=5):
        """Get recent events/activities"""
        try:
            from apps.accounts.models import Events
            events = Events.objects.filter(
                family=family
            ).select_related('dept').order_by('-created_at')[:limit]
            
            return [
                {
                    'event_id': event.event_id,
                    'title': event.title,
                    'description': event.description,
                    'start_date': event.st_date,
                    'end_date': event.end_date,
                    'location': event.location,
                    'status': event.status,
                    'type': event.type,
                    'created_at': event.created_at
                }
                for event in events
            ]
        except:
            return []
    
    
    @staticmethod
    def _get_recent_posts(family, limit=5):
        """Get recent posts"""
        posts = Posts.objects.filter(
            family=family
        ).select_related('family', 'faculty').order_by('-created_at')[:limit]
        
        return [
            {
                'post_id': post.post_id,
                'title': post.title,
                'description': post.description,
                'created_at': post.created_at,
                'updated_at': post.updated_at
            }
            for post in posts
        ]
    

########## Fam Events 


    
    @staticmethod
    def create_event_request(family_id, student, event_data):
        """
        Create a new event request for a family using Events model
        
        Only president and vice president can create events
        The faculty admin of the family's faculty becomes the created_by admin
        Status will be 'منتظر' until faculty admin approves
        
        Args:
            family_id: ID of family
            student: Student object (president/vice president)
            event_data: Dict with event details
            
        Returns:
            Tuple of (Events instance, student creator, admin)
            
        Raises:
            ValidationError: If validation fails
        """
        
        try:
            family = Families.objects.get(family_id=family_id)
        except Families.DoesNotExist:
            raise ValidationError("Family not found")
        
        # Check if student is president or vice president
        allowed_roles = ['أخ أكبر', 'أخت كبرى']
        
        member = FamilyMembers.objects.filter(
            family=family,
            student=student,
            role__in=allowed_roles
        ).first()
        
        if not member:
            raise ValidationError(
                "Only family president or vice president can create events"
            )
        
        # Ensure family has faculty assigned
        if not family.faculty:
            raise ValidationError("Family must have a faculty assigned")
        
        # Get the admin for the family's faculty
        try:
            admin = AdminsUser.objects.filter(faculty=family.faculty).first()
            
            if not admin:
                raise ValidationError(
                    f"No admin found for {family.faculty.name}. "
                    f"Please contact the faculty administration."
                )
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error finding faculty admin: {str(e)}")
        
        # Create event request in Events table
        try:
            with transaction.atomic():
                event = Events.objects.create(
                    title=event_data['title'],
                    description=event_data['description'],
                    type=event_data['type'],
                    st_date=event_data['st_date'],
                    end_date=event_data['end_date'],
                    location=event_data['location'],
                    s_limit=event_data.get('s_limit'),
                    cost=event_data.get('cost'),
                    dept=event_data.get('dept'),
                    restrictions=event_data.get('restrictions', ''),
                    reward=event_data.get('reward', ''),
                    family=family,
                    faculty=family.faculty,
                    
                    created_by=admin,  # Faculty admin of the family's faculty
                    status='منتظر',  # Pending review
                    created_at=timezone.now()
                )
                
                # Refresh to get all related data
                event = Events.objects.select_related(
                    'family', 'faculty', 'created_by'
                ).get(event_id=event.event_id)
                
                return event, student, admin
        
        except Exception as e:
            raise ValidationError(f"Error creating event request: {str(e)}")
    
    
    @staticmethod
    def get_family_event_requests(family_id, student):
        """Get all event requests for a family"""
        
        try:
            family = Families.objects.get(family_id=family_id)
        except Families.DoesNotExist:
            raise ValidationError("Family not found")
        
        # Check if student is member
        is_member = FamilyMembers.objects.filter(
            family=family,
            student=student
        ).exists()
        
        if not is_member:
            raise ValidationError("You are not a member of this family")
        
        # Get all events for this family with related data
        events = Events.objects.filter(
            family=family
        ).select_related(
            'family', 'faculty', 'created_by', 'dept'
        ).order_by('-created_at')
        
        return events
    
    
    @staticmethod
    def get_family_approved_events(family_id, student):
        """Get all APPROVED events for a family (visible to all members)"""
        
        try:
            family = Families.objects.get(family_id=family_id)
        except Families.DoesNotExist:
            raise ValidationError("Family not found")
        
        # Check if student is member
        is_member = FamilyMembers.objects.filter(
            family=family,
            student=student
        ).exists()
        
        if not is_member:
            raise ValidationError("You are not a member of this family")
        
        # Get only approved events with related data
        events = Events.objects.filter(
            family=family,
            status='مقبول'
        ).select_related(
            'family', 'faculty', 'created_by', 'dept'
        ).order_by('-created_at')
        
        return events
    
    
    @staticmethod
    def get_pending_event_requests(faculty_id, admin):
        """Get all pending event requests for a faculty (for admin review)"""
        
        # Check if admin belongs to this faculty
        if admin.faculty_id != faculty_id:
            raise ValidationError("You don't have access to this faculty")
        
        # Get all pending event requests with related data
        events = Events.objects.filter(
            faculty_id=faculty_id,
            status='منتظر'
        ).select_related(
            'family', 'faculty', 'created_by', 'dept'
        ).order_by('-created_at')
        
        return events
    
    


    @staticmethod
    def register_for_event(family_id, event_id, student):
        """
        Register a student for an event within their family
        
        Args:
            family_id: ID of family the student is member of
            event_id: ID of event to register for
            student: Student object trying to register
            
        Returns:
            Prtcps instance created
            
        Raises:
            ValidationError: If student can't register
        """
        from django.db import transaction
        from django.utils import timezone
        
        # Check 1: Student must have a faculty
        if not student.faculty:
            raise ValidationError("Student is not assigned to any faculty")
        
        # Check 2: Verify family exists
        try:
            family = Families.objects.get(family_id=family_id)
        except Families.DoesNotExist:
            raise ValidationError("Family not found")
        
        # Check 3: Verify student is a member of this family
        try:
            membership = FamilyMembers.objects.get(
                family=family,
                student=student
            )
        except FamilyMembers.DoesNotExist:
            raise ValidationError("You are not a member of this family")
        
        # Check 4: Verify membership status is valid (not rejected/pending)
        if membership.status not in ['مقبول', 'منتظر', None]:
            raise ValidationError(f"Your membership status is: {membership.status}. Cannot register for events.")
        
        # Check 5: Verify member role (must be 'عضو' or equivalent)
        if membership.role != 'عضو':
            raise ValidationError("Only family members with role 'عضو' can register for events")
        
        # Check 6: Verify event exists
        try:
            event = Events.objects.select_related('family', 'faculty').get(event_id=event_id)
        except Events.DoesNotExist:
            raise ValidationError("Event not found")
        
        # Check 7: Event must belong to the specified family
        # if not event.family or event.family.family_id != family_id:
        #     raise ValidationError(f"This event does not belong to the family '{family.name}'")
        
        # Check 8: Event must belong to student's faculty
        if event.faculty and event.faculty != student.faculty:
            raise ValidationError(
                f"This event is only for {event.faculty.name} faculty. "
                f"You belong to {student.faculty.name} faculty."
            )
        
        # Check 9: Student not already registered
        already_registered = Prtcps.objects.filter(
            event=event,
            student=student
        ).exists()
        
        if already_registered:
            raise ValidationError("You are already registered for this event")
        
        # Check 10: Event not full (if limit exists)
        if event.s_limit:
            current_participants = Prtcps.objects.filter(event=event).count()
            if current_participants >= event.s_limit:
                raise ValidationError(
                    f"Event is full ({current_participants}/{event.s_limit} participants)"
                )
        
        # Check 11: Event must be open/available (optional - adjust status values as needed)
        if event.status and event.status not in ['مفتوح', 'متاح', 'active', None  , 'مقبول']:
            raise ValidationError(f"Event is not open for registration (Status: {event.status})")
        
        # Check 12: Event date validation (optional - can't register for past events)
        from datetime import date
        if event.end_date < date.today():
            raise ValidationError("Cannot register for past events")
        
        # Create registration
        try:
            with transaction.atomic():
                participation = Prtcps.objects.create(
                    event=event,
                    student=student,
                    status='منتظر',  # Default pending status
                    rank=None,       # Will be assigned later
                    reward=None      # Will be assigned after event
                )
                return participation
        except Exception as e:
            raise ValidationError(f"Error registering for event: {str(e)}")
