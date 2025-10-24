import os
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.solidarity.models import Solidarities, Logs, SolidarityDocs
import logging
from rest_framework.exceptions import PermissionDenied, NotFound

from django.db.models import Q

from youth_welfare import settings


logger = logging.getLogger(__name__)

class SolidarityService:
    @staticmethod
    @transaction.atomic
    def create_application(student, application_data, uploaded_docs=None):
        if SolidarityService.has_pending_application(student):
            raise ValidationError("لديك طلب معلق بالفعل. يرجى الانتظار للمراجعة.")

        father_income = application_data.get('father_income') or 0
        mother_income = application_data.get('mother_income') or 0
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
            disabilities=application_data.get('disabilities'),
            housing_status=application_data.get('housing_status'),
            grade=application_data.get('grade'),
            acd_status=application_data.get('acd_status'),
            address=application_data['address'],
            req_status='منتظر'
        )

        if uploaded_docs:
            upload_dir = f"uploads/solidarity/{solidarity.solidarity_id}/"
            os.makedirs(os.path.join(settings.MEDIA_ROOT, upload_dir), exist_ok=True)
            
            for doc_type, file_info in uploaded_docs.items():
                full_path = os.path.join(settings.MEDIA_ROOT, file_info['file_path'])
                SolidarityDocs.objects.create(
                    solidarity=solidarity,
                    doc_type=doc_type,
                    file_name=file_info['file_name'],
                    file_path=file_info['file_path'],
                    mime_type=file_info['mime_type'],
                    file_size=file_info['file_size'],
                    uploaded_at=timezone.now()
                )

        logger.info(f"Application {solidarity.solidarity_id} created for {student.name}")
        return solidarity

    @staticmethod
    def has_pending_application(student):
        return Solidarities.objects.filter(student=student, req_status='منتظر').exists()
    


    @staticmethod
    def get_student_applications(admin, status=None, filters=None):
        solidarity = Solidarities.objects
        queryset = Solidarities.objects.select_related('student', 'faculty', 'approved_by')

        # Filter by faculty automatically if admin is faculty_admin
        if admin.role.lower() == 'مسؤول كلية' :
            faculty_id = getattr(admin, 'faculty_id', None)
            if admin.faculty_id:
                queryset = queryset.filter(faculty_id=admin.faculty_id)
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
    def get_application_detail(solidarity_id, admin):
        if admin.role != 'مسؤول كلية' :
            raise PermissionDenied("You can not view applications .")
        try:
            solidarity = (
                Solidarities.objects
                .select_related('student', 'faculty', 'approved_by')
                .get(pk=solidarity_id)
            )
        except Solidarities.DoesNotExist:
            raise NotFound("Application not found.")

        print(f"Admin faculty_id: {admin.faculty_id}, Admin faculty: {admin.faculty}")
        print(f"Solidarity faculty_id: {solidarity.faculty_id}, Solidarity faculty: {solidarity.faculty}")

        # Restriction for faculty admin
        if admin.role == 'مسؤول كلية':
            admin_faculty_id = getattr(admin.faculty, 'faculty_id', None) or getattr(admin, 'faculty_id', None)
            solidarity_faculty_id = getattr(solidarity.faculty, 'faculty_id', None) or getattr(solidarity, 'faculty_id', None)

            if admin_faculty_id != solidarity_faculty_id:
                raise PermissionDenied("You can only view applications from your faculty.")

        return solidarity



    @staticmethod
    @transaction.atomic
    def approve_application(solidarity_id, admin):
        try:
            solidarity = Solidarities.objects.select_for_update().get(solidarity_id=solidarity_id)
            logger.info(f"Attempting to approve application ID {solidarity_id} with current status: {solidarity.req_status}")
        except Solidarities.DoesNotExist:
            raise ValidationError("Application not found.")

        if admin.role == 'مسؤول كلية' and solidarity.faculty_id != admin.faculty_id:
            raise ValidationError("You can only approve applications from your faculty.")
        if solidarity.req_status.lower() == 'مرفوض' :
            raise ValidationError(f"Cannot approve application with status: {solidarity.req_status}")

        solidarity.req_status = 'مقبول'
        solidarity.approved_by = admin
        solidarity.updated_at = timezone.now()
        solidarity.save()
        return {'success': True, 'message': 'Application approved successfully', 'solidarity': solidarity}
    

    @staticmethod
    @transaction.atomic
    def pre_approve_application(solidarity_id, admin):
        try:
            solidarity = Solidarities.objects.select_for_update().get(solidarity_id=solidarity_id)
            logger.info(f"Attempting to pre approve application ID {solidarity_id} with current status: {solidarity.req_status}")
        except Solidarities.DoesNotExist:
            raise ValidationError("Application not found.")

        if admin.role == 'مسؤول كلية' and solidarity.faculty_id != admin.faculty_id:
            raise ValidationError("You can only pre approve applications from your faculty.")
        if solidarity.req_status.lower() != 'منتظر' :
            raise ValidationError(f"Cannot pre approve application with status: {solidarity.req_status}")

        solidarity.req_status = 'موافقة مبدئية'
        solidarity.approved_by = admin
        solidarity.updated_at = timezone.now()
        solidarity.save()
        return {'success': True, 'message': 'Application pre approved successfully', 'solidarity': solidarity}

    @staticmethod
    @transaction.atomic
    def reject_application(solidarity_id, admin, rejection_reason=None):
        try:
            solidarity = Solidarities.objects.select_for_update().get(solidarity_id=solidarity_id)
        except Solidarities.DoesNotExist:
            raise ValidationError("Application not found.")
        if admin.role == 'مسؤول كلية' and solidarity.faculty_id != admin.faculty_id:
            raise ValidationError("You can only reject applications from your faculty.")
        if solidarity.req_status.lower() == 'مقبول' :
            raise ValidationError(f"Cannot reject application with status: {solidarity.req_status}")



        solidarity.req_status = 'مرفوض'
        solidarity.approved_by = admin
        solidarity.updated_at = timezone.now()
        solidarity.save()

        return {'success': True, 'message': 'Application rejected', 'solidarity': solidarity}

    @staticmethod ##############3
    def get_applications_for_review(admin, status=None, filters=None):
        queryset = Solidarities.objects.select_related('student', 'faculty', 'approved_by')
        if admin.role !='مسؤول كلية' :
            raise PermissionDenied("You can not view applications.")
        if admin.role.strip().lower() == 'مسؤول كلية':
            faculty = getattr(admin, 'faculty', None)
            if faculty:
                queryset = queryset.filter(faculty=admin.faculty)
            else:
                return Solidarities.objects.none()

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
    def get_all_applications(admin=None, filters=None):
        queryset = (
            Solidarities.objects
            .select_related('student', 'faculty', 'approved_by')
            #.filter(req_status='مقبول')
        )

        if admin and hasattr(admin, 'role'):
            if admin.role == 'مدير ادارة' and getattr(admin, 'dept_id', None):
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


    @staticmethod
    @transaction.atomic
    def change_to_approve(solidarity_id, admin):
        solidarity = Solidarities.objects.select_for_update().get(solidarity_id=solidarity_id)

        if admin.role != 'مشرف النظام':
            raise ValidationError("Only system supervisors can approve applications.")

        if solidarity.req_status == 'مقبول':
            raise ValidationError("Application is already approved.")

        solidarity.req_status = 'مقبول'
        solidarity.approved_by = admin
        solidarity.updated_at = timezone.now()
        solidarity.save()

        logger.info(f"Super admin {admin.name} approved application {solidarity_id}.")
        return {'message': 'Application approved successfully.'}


    @staticmethod
    @transaction.atomic
    def change_to_reject(solidarity_id, admin):
        solidarity = Solidarities.objects.select_for_update().get(solidarity_id=solidarity_id)

        if admin.role != 'مشرف النظام':
            raise ValidationError("Only system supervisors can reject applications.")

        if solidarity.req_status == 'مرفوض':
            raise ValidationError("Application is already rejected.")

        solidarity.req_status = 'مرفوض'
        solidarity.approved_by = admin
        solidarity.updated_at = timezone.now()
        solidarity.save()

        logger.info(f"Super admin {admin.name} rejected application {solidarity_id}.")
        return {'message': 'Application rejected successfully.'}