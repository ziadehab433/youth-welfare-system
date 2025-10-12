# from django.db import transaction
# from django.core.exceptions import ValidationError
# from django.utils import timezone
# from apps.solidarity.models import Solidarities, Logs


# class SolidarityService:
#     """
#     Business logic for solidarity operations
#     Follow naming convention: snake_case for methods
#     """
    
#     @staticmethod
#     @transaction.atomic
#     def create_application(student, application_data):
#         """
#         Create a new solidarity application
        
#         Args:
#             student: Students instance
#             application_data: dict with application details
        
#         Returns:
#             Solidarities instance
#         """
#         # Business rule: Check if student has pending application
#         if SolidarityService.has_pending_application(student):
#             raise ValidationError(
#                 "You already have a pending application. Please wait for review."
#             )
        
#         # Calculate total income
#         father_income = application_data.get('father_income', 0) or 0
#         mother_income = application_data.get('mother_income', 0) or 0
#         total_income = father_income + mother_income
        
#         # Create application
#         solidarity = Solidarities.objects.create(
#             student=student,
#             faculty=student.faculty,
#             family_numbers=application_data['family_numbers'],
#             father_status=application_data.get('father_status'),
#             mother_status=application_data.get('mother_status'),
#             father_income=father_income,
#             mother_income=mother_income,
#             total_income=total_income,
#             arrange_of_brothers=application_data.get('arrange_of_brothers'),
#             m_phone_num=application_data.get('m_phone_num'),
#             f_phone_num=application_data.get('f_phone_num'),
#             reason=application_data['reason'],
#             docs=application_data.get('docs'),
#             disabilities=application_data.get('disabilities'),
#             housing_status=application_data.get('housing_status'),
#             grade=application_data.get('grade'),
#             acd_status=application_data.get('acd_status'),
#             address=application_data['address'],
#             req_status='PENDING'
#         )
        
#         # Log the action
#         SolidarityService.log_action(
#             actor=None,  # Will be handled by view
#             action='CREATE_APPLICATION',
#             solidarity=solidarity
#         )
        
#         return solidarity
    
#     @staticmethod
#     def has_pending_application(student):
#         """Check if student has pending applications"""
#         return Solidarities.objects.filter(
#             student=student,
#             req_status='PENDING'
#         ).exists()
    
#     @staticmethod
#     def get_student_applications(student, status=None):
#         """Get all applications for a specific student"""
#         queryset = Solidarities.objects.filter(student=student)
        
#         if status:
#             queryset = queryset.filter(req_status=status)
        
#         return queryset.select_related('faculty', 'approved_by').order_by('-created_at')
    
#     @staticmethod
#     def get_application_status(student, solidarity_id):
#         """Get status of specific application"""
#         try:
#             solidarity = Solidarities.objects.get(
#                 solidarity_id=solidarity_id,
#                 student=student
#             )
#             return {
#                 'solidarity_id': solidarity.solidarity_id,
#                 'req_status': solidarity.req_status,
#                 'created_at': solidarity.created_at,
#                 'updated_at': solidarity.updated_at,
#                 'approved_by': solidarity.approved_by.name if solidarity.approved_by else None
#             }
#         except Solidarities.DoesNotExist:
#             raise ValidationError("Application not found or access denied.")
    
#     @staticmethod
#     @transaction.atomic
#     def approve_application(solidarity_id, admin):
#         """
#         Approve solidarity application
        
#         Args:
#             solidarity_id: ID of the application
#             admin: Admins instance (who is approving)
        
#         Returns:
#             dict with success status
#         """
#         try:
#             solidarity = Solidarities.objects.select_for_update().get(
#                 solidarity_id=solidarity_id
#             )
#         except Solidarities.DoesNotExist:
#             raise ValidationError("Application not found.")
        
#         # Business rule: Only pending applications can be approved
#         if solidarity.req_status != 'PENDING':
#             raise ValidationError(
#                 f"Cannot approve application with status: {solidarity.req_status}"
#             )
        
#         # Faculty admin can only approve from their faculty
#         if admin.role == 'FACULTY_ADMIN':
#             if solidarity.faculty != admin.faculty:
#                 raise ValidationError(
#                     "You can only approve applications from your faculty."
#                 )
        
#         # Update status
#         solidarity.req_status = 'APPROVED'
#         solidarity.approved_by = admin
#         solidarity.updated_at = timezone.now()
#         solidarity.save()
        
#         # Log action
#         SolidarityService.log_action(
#             actor=admin,
#             action='APPROVE_APPLICATION',
#             solidarity=solidarity
#         )
        
#         return {
#             'success': True,
#             'message': 'Application approved successfully',
#             'solidarity': solidarity
#         }
    
#     @staticmethod
#     @transaction.atomic
#     def reject_application(solidarity_id, admin, rejection_reason=None):
#         """
#         Reject solidarity application
        
#         Args:
#             solidarity_id: ID of the application
#             admin: Admins instance (who is rejecting)
#             rejection_reason: Reason for rejection (optional)
        
#         Returns:
#             dict with success status
#         """
#         try:
#             solidarity = Solidarities.objects.select_for_update().get(
#                 solidarity_id=solidarity_id
#             )
#         except Solidarities.DoesNotExist:
#             raise ValidationError("Application not found.")
        
#         if solidarity.req_status != 'PENDING':
#             raise ValidationError(
#                 f"Cannot reject application with status: {solidarity.req_status}"
#             )
        
#         # Faculty admin can only reject from their faculty
#         if admin.role == 'FACULTY_ADMIN':
#             if solidarity.faculty != admin.faculty:
#                 raise ValidationError(
#                     "You can only reject applications from your faculty."
#                 )
        
#         # Update status
#         solidarity.req_status = 'REJECTED'
#         solidarity.approved_by = admin
#         solidarity.updated_at = timezone.now()
#         solidarity.save()
        
#         # Log action
#         SolidarityService.log_action(
#             actor=admin,
#             action='REJECT_APPLICATION',
#             solidarity=solidarity
#         )
        
#         return {
#             'success': True,
#             'message': 'Application rejected',
#             'solidarity': solidarity
#         }
    
#     @staticmethod
#     def get_applications_for_review(admin, status=None, filters=None):
#         """
#         Get applications for admin review
        
#         Args:
#             admin: Admins instance
#             status: Filter by status (optional)
#             filters: Additional filters (optional)
        
#         Returns:
#             QuerySet of Solidarities
#         """
#         queryset = Solidarities.objects.select_related(
#             'student',
#             'faculty',
#             'approved_by'
#         )
        
#         # Faculty admin sees only their faculty
#         if admin.role == 'FACULTY_ADMIN':
#             queryset = queryset.filter(faculty=admin.faculty)
        
#         # Apply status filter
#         if status:
#             queryset = queryset.filter(req_status=status)
        
#         # Apply additional filters
#         if filters:
#             if 'faculty_id' in filters and filters['faculty_id']:
#                 queryset = queryset.filter(faculty_id=filters['faculty_id'])
            
#             if 'date_from' in filters and filters['date_from']:
#                 queryset = queryset.filter(created_at__gte=filters['date_from'])
            
#             if 'date_to' in filters and filters['date_to']:
#                 queryset = queryset.filter(created_at__lte=filters['date_to'])
        
#         return queryset.order_by('-created_at')
    
#     @staticmethod
#     def get_all_applications(filters=None):
#         """
#         Get all applications (for super admin)
        
#         Args:
#             filters: dict of filters
        
#         Returns:
#             QuerySet of Solidarities
#         """
#         queryset = Solidarities.objects.select_related(
#             'student',
#             'faculty',
#             'approved_by'
#         )
        
#         if filters:
#             if 'faculty' in filters and filters['faculty']:
#                 queryset

# @staticmethod
# def get_all_applications(filters=None):
#     queryset = Solidarities.objects.select_related('student', 'faculty', 'approved_by')
#     if filters:
#         if filters.get('faculty'):
#             queryset = queryset.filter(faculty_id=filters['faculty'])
#     if filters.get('status'):
#         queryset = queryset.filter(req_status=filters['status'])
#     if filters.get('date_from'):
#         queryset = queryset.filter(created_at__gte=filters['date_from'])
#     if filters.get('date_to'):
#         queryset = queryset.filter(created_at__lte=filters['date_to'])
#     if filters.get('student_id'):
#         queryset = queryset.filter(student_id=filters['student_id'])
#         return queryset.order_by('-created_at')
    
# @staticmethod
# def get_application_detail(solidarity_id):
#     try:
#         return Solidarities.objects.select_related('student', 'faculty', 'approved_by').get(
#             solidarity_id=solidarity_id
#         )
#     except Solidarities.DoesNotExist:
#         raise ValidationError("Application not found.")

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.solidarity.models import Solidarities, Logs
import logging
logger = logging.getLogger(__name__)

class SolidarityService:
    """ Business logic for solidarity operations """

    @staticmethod
    @transaction.atomic
    def create_application(student, application_data):
        """ Create a new solidarity application """
        if SolidarityService.has_pending_application(student):
            raise ValidationError("You already have a pending application. Please wait for review.")
        
        father_income = application_data.get('father_income', 0) or 0
        mother_income = application_data.get('mother_income', 0) or 0
        total_income = father_income + mother_income
        
        solidarity = Solidarities.objects.create(
            student=student,
            faculty=student.faculty,
            family_numbers=application_data['family_numbers'],
            father_status=application_data.get('father_status'),
            mother_status=application_data.get('mother_status'),
            father_income=father_income,
            mother_income=mother_income,
            total_income=total_income,
            arrange_of_brothers=application_data.get('arrange_of_brothers'),
            m_phone_num=application_data.get('m_phone_num'),
            f_phone_num=application_data.get('f_phone_num'),
            reason=application_data['reason'],
            docs=application_data.get('docs'),
            disabilities=application_data.get('disabilities'),
            housing_status=application_data.get('housing_status'),
            grade=application_data.get('grade'),
            acd_status=application_data.get('acd_status'),
            address=application_data['address'],
            req_status='PENDING'
        )
        
        SolidarityService.log_action(actor=None, action='CREATE_APPLICATION', solidarity=solidarity)
        
        return solidarity

    @staticmethod
    def has_pending_application(student):
        """ Check if student has pending applications """
        return Solidarities.objects.filter(student=student, req_status='PENDING').exists()

    @staticmethod
    def get_student_applications(student, status=None):
        """ Get all applications for a specific student """
        queryset = Solidarities.objects.filter(student=student)
        if status:
            queryset = queryset.filter(req_status=status)
        return queryset.select_related('faculty', 'approved_by').order_by('-created_at')

    @staticmethod
    def get_application_detail(solidarity_id):
        """ Get application detail """
        try:
            return Solidarities.objects.select_related('student', 'faculty', 'approved_by').get(solidarity_id=solidarity_id)
        except Solidarities.DoesNotExist:
            raise ValidationError("Application not found.")


    @staticmethod
    @transaction.atomic
    def approve_application(solidarity_id, admin):
        """Approve solidarity application"""
        try:
            solidarity = Solidarities.objects.select_for_update().get(solidarity_id=solidarity_id)
            logger.info(f"Attempting to approve application ID {solidarity_id} with current status: {solidarity.req_status}")
        except Solidarities.DoesNotExist:
            raise ValidationError("Application not found.")

        # ✅ Normalize case for comparison
        if solidarity.req_status.lower() != 'pending':
            logger.error(f"Cannot approve application with status: {solidarity.req_status}")
            raise ValidationError(f"Cannot approve application with status: {solidarity.req_status}")

        # ✅ Faculty restriction
        if admin.role == 'FACULTY_ADMIN' and solidarity.faculty != admin.faculty:
            raise ValidationError("You can only approve applications from your faculty.")

        # ✅ Set to lowercase to match PostgreSQL enum
        solidarity.req_status = 'approved'
        solidarity.approved_by = admin
        solidarity.updated_at = timezone.now()
        solidarity.save()

        SolidarityService.log_action(actor=admin, action='APPROVE_APPLICATION', solidarity=solidarity)

        return {'success': True, 'message': 'Application approved successfully', 'solidarity': solidarity}


    @staticmethod
    @transaction.atomic
    def reject_application(solidarity_id, admin, rejection_reason=None):
        """ Reject solidarity application """
        try:
            solidarity = Solidarities.objects.select_for_update().get(solidarity_id=solidarity_id)
        except Solidarities.DoesNotExist:
            raise ValidationError("Application not found.")

        if solidarity.req_status.lower() != 'pending':
            raise ValidationError(f"Cannot reject application with status: {solidarity.req_status}")

        if admin.role == 'FACULTY_ADMIN' and solidarity.faculty != admin.faculty:
            raise ValidationError("You can only reject applications from your faculty.")
        
        solidarity.req_status = 'rejected'
        solidarity.approved_by = admin
        solidarity.updated_at = timezone.now()
        solidarity.save()
        
        SolidarityService.log_action(actor=admin, action='REJECT_APPLICATION', solidarity=solidarity)
        
        return {'success': True, 'message': 'Application rejected', 'solidarity': solidarity}

    @staticmethod
    def get_applications_for_review(admin, status=None, filters=None):
        """ Get applications for admin review """
        queryset = Solidarities.objects.select_related('student', 'faculty', 'approved_by')
        if admin.role == 'FACULTY_ADMIN':
            queryset = queryset.filter(faculty=admin.faculty)

        if status:
            queryset = queryset.filter(req_status=status)
        
        if filters:
            if 'faculty_id' in filters and filters['faculty_id']:
                queryset = queryset.filter(faculty_id=filters['faculty_id'])
            if 'date_from' in filters and filters['date_from']:
                queryset = queryset.filter(created_at__gte=filters['date_from'])
            if 'date_to' in filters and filters['date_to']:
                queryset = queryset.filter(created_at__lte=filters['date_to'])

        return queryset.order_by('-created_at')

    @staticmethod
    def get_all_applications(filters=None):
        """ Get all applications (for super admin) """
        queryset = Solidarities.objects.select_related('student', 'faculty', 'approved_by')
        if filters:
            if 'faculty' in filters and filters['faculty']:
                queryset = queryset.filter(faculty_id=filters['faculty'])
            if 'status' in filters and filters['status']:
                queryset = queryset.filter(req_status=filters['status'])
            if 'date_from' in filters and filters['date_from']:
                queryset = queryset.filter(created_at__gte=filters['date_from'])
            if 'date_to' in filters and filters['date_to']:
                queryset = queryset.filter(created_at__lte=filters['date_to'])
            if 'student_id' in filters and filters['student_id']:
                queryset = queryset.filter(student_id=filters['student_id'])

        return queryset.order_by('-created_at')

    @staticmethod
    def log_action(actor, action, solidarity):
        """ Log action for audit trails """
        Logs.objects.create(actor=actor, action=action, solidarity=solidarity, target_type='solidarity')