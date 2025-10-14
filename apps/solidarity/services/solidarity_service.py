from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.solidarity.models import Solidarities, Logs
import logging

from django.db.models import Q


logger = logging.getLogger(__name__)

class SolidarityService:
    """ Business logic for solidarity operations """

    @staticmethod
    @transaction.atomic
    def create_application(student, application_data):
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
            req_status='pending'
        )

        SolidarityService.log_action(actor=None, action='create_application', solidarity=solidarity)
        return solidarity

    @staticmethod
    def has_pending_application(student):
        return Solidarities.objects.filter(student=student, req_status='pending').exists()


    @staticmethod
    def get_student_applications(admin, status=None, filters=None):
        queryset = Solidarities.objects.select_related('student', 'faculty', 'approved_by')

        # Filter by faculty automatically if admin is faculty_admin
        if admin.role.lower() == 'faculty_admin':
            faculty_id = getattr(admin, 'faculty_id', None)
            if faculty_id:
                queryset = queryset.filter(faculty_id=faculty_id)
            else:
                # In case faculty is not linked properly, return empty queryset
                return Solidarities.objects.none()

        # could rem
        if status:
            queryset = queryset.filter(req_status=status)

        if filters:
            if filters.get('faculty_id'):
                queryset = queryset.filter(faculty_id=filters['faculty_id'])
            if filters.get('date_from'):
                queryset = queryset.filter(created_at__gte=filters['date_from'])
            if filters.get('date_to'):
                queryset = queryset.filter(created_at__lte=filters['date_to'])

        return queryset.order_by('-created_at')




    @staticmethod
    def get_application_detail(solidarity_id):
        try:
            return Solidarities.objects.select_related('student', 'faculty', 'approved_by').get(solidarity_id=solidarity_id)
        except Solidarities.DoesNotExist:
            raise ValidationError("Application not found.")

    @staticmethod
    @transaction.atomic
    def approve_application(solidarity_id, admin):
        try:
            solidarity = Solidarities.objects.select_for_update().get(solidarity_id=solidarity_id)
            logger.info(f"Attempting to approve application ID {solidarity_id} with current status: {solidarity.req_status}")
        except Solidarities.DoesNotExist:
            raise ValidationError("Application not found.")

        if solidarity.req_status.lower() != 'pending':
            raise ValidationError(f"Cannot approve application with status: {solidarity.req_status}")

        if admin.role == 'faculty_admin' and solidarity.faculty != admin.faculty:
            raise ValidationError("You can only approve applications from your faculty.")

        solidarity.req_status = 'approved'
        solidarity.approved_by = admin
        solidarity.updated_at = timezone.now()
        solidarity.save()
        return {'success': True, 'message': 'Application approved successfully', 'solidarity': solidarity}

    @staticmethod
    @transaction.atomic
    def reject_application(solidarity_id, admin, rejection_reason=None):
        try:
            solidarity = Solidarities.objects.select_for_update().get(solidarity_id=solidarity_id)
        except Solidarities.DoesNotExist:
            raise ValidationError("Application not found.")

        if solidarity.req_status.lower() != 'pending':
            raise ValidationError(f"Cannot reject application with status: {solidarity.req_status}")

        if admin.role == 'faculty_admin' and solidarity.faculty != admin.faculty:
            raise ValidationError("You can only reject applications from your faculty.")

        solidarity.req_status = 'rejected'
        solidarity.approved_by = admin
        solidarity.updated_at = timezone.now()
        solidarity.save()

        return {'success': True, 'message': 'Application rejected', 'solidarity': solidarity}

    @staticmethod
    def get_applications_for_review(admin, status=None, filters=None):
        queryset = Solidarities.objects.select_related('student', 'faculty', 'approved_by')
        if admin.role == 'faculty_admin' and hasattr(admin, 'faculty'):
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
    def get_all_applications(admin=None, filters=None):
        queryset = (
            Solidarities.objects
            .select_related('student', 'faculty', 'approved_by')
            .filter(req_status='approved')
        )

        if admin and hasattr(admin, 'role'):
            if admin.role == 'department_manager' and getattr(admin, 'dept_id', None):
                queryset = queryset.filter(faculty_id__in=[
                    f.faculty_id for f in admin.dept.faculties_set.all()
                ])

        if filters:
            if filters.get('faculty'):
                queryset = queryset.filter(faculty_id=filters['faculty'])
            if filters.get('total_income'):
                ti = filters['total_income'].lower()
                if ti == 'low':
                    queryset = queryset.filter(total_income__lt=3000)
                elif ti == 'moderate':
                    queryset = queryset.filter(total_income__gte=3000, total_income__lte=5000)
                elif ti == 'high':
                    queryset = queryset.filter(total_income__gt=5000)

            if filters.get('family_numbers'):
                fn = str(filters['family_numbers']).lower()
                if fn == 'few':
                    queryset = queryset.filter(family_numbers__lt=3)
                elif fn == 'moderate':
                    queryset = queryset.filter(family_numbers__gte=3, family_numbers__lte=4)
                elif fn == 'many':
                    queryset = queryset.filter(family_numbers__gt=4)

            if filters.get('disabilities'):
                queryset = queryset.filter(disabilities__icontains=filters['disabilities'])

            if filters.get('housing_status'):
                queryset = queryset.filter(housing_status__iexact=filters['housing_status'])

            if filters.get('grade'):
                queryset = queryset.filter(grade__icontains=filters['grade'])

            if filters.get('father_status'):
                queryset = queryset.filter(father_status__icontains=filters['father_status'])

            if filters.get('mother_status'):
                queryset = queryset.filter(mother_status__icontains=filters['mother_status'])

        return queryset.order_by('-created_at')

    @staticmethod
    def log_action(actor, action, solidarity):
        Logs.objects.create(actor=actor, action=action, solidarity=solidarity, target_type='solidarity')
