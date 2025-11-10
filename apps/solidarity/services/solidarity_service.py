import os
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.solidarity.models import Solidarities, Logs, SolidarityDocs
import logging
from rest_framework.exceptions import PermissionDenied, NotFound
from django.conf import settings
from apps.solidarity.api.utils import save_uploaded_file
from django.db.models import Q
from apps.solidarity.models import Solidarities, SolidarityDocs

from youth_welfare import settings
from django.db import connection


logger = logging.getLogger(__name__)
DOC_TYPE_MAP = {
    'social_research_file': 'بحث احتماعي',
    'salary_proof_file': 'اثبات دخل',
    'father_id_file': 'ص.ب ولي امر',
    'student_id_file': 'ص.ب شخصية',
    'land_ownership_file': 'حبازة زراعية',
    'sd_file' : 'تكافل و كرامة'
}

class SolidarityService:


    @staticmethod
    def has_pending_application(student):
              return Solidarities.objects.filter(student=student, req_status='منتظر').exists()

    @staticmethod
    def has_application(student):
              return Solidarities.objects.filter(student=student, req_status='مقبول').exists()
    

    @staticmethod
    @transaction.atomic
    def create_application(student, application_data, uploaded_docs=None):
        if SolidarityService.has_pending_application(student) or SolidarityService.has_application(student):
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

        # Handle files
        # if uploaded_docs:
        #     upload_dir = os.path.join(settings.MEDIA_ROOT, f"uploads/solidarity/{solidarity.solidarity_id}/")
        #     os.makedirs(upload_dir, exist_ok=True)

        #     for doc_type_key, file_obj in uploaded_docs.items():
        #         arabic_doc_type = DOC_TYPE_MAP.get(doc_type_key)
        #         if not arabic_doc_type:
        #             raise ValidationError(f"Invalid document type: {doc_type_key}")

        #         file_path = os.path.join(upload_dir, file_obj.name)

        #         with open(file_path, 'wb+') as destination:
        #             for chunk in file_obj.chunks():
        #                 destination.write(chunk)

        #         SolidarityDocs.objects.create(
        #             solidarity=solidarity,
        #             doc_type=arabic_doc_type,
        #             file_name=file_obj.name,
        #             file_path=file_path.replace(settings.MEDIA_ROOT + '/', ''),  # relative path
        #             mime_type=file_obj.content_type,
        #             file_size=file_obj.size,
        #             uploaded_at=timezone.now()
        #         )

        if uploaded_docs:
            for doc_type_key, file_obj in uploaded_docs.items():
                arabic_doc_type = DOC_TYPE_MAP.get(doc_type_key)
                if not arabic_doc_type:
                        raise ValidationError(f"Invalid document type: {doc_type_key}")

                SolidarityDocs.objects.create(
                    solidarity=solidarity,
                    doc_type=arabic_doc_type,
                    file=file_obj,                        # <-- this is all you need!
                    mime_type=file_obj.content_type,
                    file_size=file_obj.size,
                    uploaded_at=timezone.now()
                )

        logger.info(f"Application {solidarity.solidarity_id} created for {student.name}")
        return solidarity

    


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
        if admin.role not in ['مسؤول كلية'] :
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


    #for super & dept admins
    @staticmethod
    def get_app_dtl(solidarity_id, admin):
        print(f"admin id : {admin.admin_id}")
        print(f"admin role is : {admin.role}")
        if admin.role not in ['مشرف النظام', 'مدير ادارة']:
            raise PermissionDenied("You can not view applications .")
        try:
            solidarity = (
                Solidarities.objects
                .select_related('student', 'faculty', 'approved_by')
                .get(pk=solidarity_id)
            )
        except Solidarities.DoesNotExist:
            raise NotFound("Application not found.")



        return solidarity

    @staticmethod
    def get_docs_by_solidarity_id(solidarity_id):
        return SolidarityDocs.objects.filter(solidarity_id=solidarity_id)


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
    @transaction.atomic
    def assign_discounts(admin, solidarity, discount_data):
        total_discount = 0
        
        for item in discount_data:
            discount_value = item['discount_value'] 
            total_discount += discount_value

        solidarity.total_discount = total_discount
        solidarity.approved_by = admin
        solidarity.updated_at = timezone.now()
        solidarity.save()

        return solidarity

    @staticmethod
    @transaction.atomic
    def update_faculty_discounts(admin, data):
        faculty = admin.faculty  # كلية الأدمن الحالي
        for field, value in data.items():
           setattr(faculty, field, value)
    
        faculty.save()
        return faculty


    @staticmethod
    def get_all_applications(admin=None, filters=None):
        queryset = Solidarities.objects.select_related('student', 'faculty', 'approved_by')

        if admin and hasattr(admin, 'role'):
            if admin.role == 'مدير ادارة' and getattr(admin, 'dept_id', None):
                faculty_ids = [f.faculty_id for f in admin.dept.faculties_set.all()]
                queryset = queryset.filter(faculty_id__in=faculty_ids)

        if filters:
            faculty = filters.get('faculty')
            if faculty:
                queryset = queryset.filter(faculty_id=faculty)

            status = filters.get('status')
            if status:
                queryset = queryset.filter(req_status=status)

            student_id = filters.get('student_id')
            if student_id:
                queryset = queryset.filter(student__student_id=student_id)

            total_income = filters.get('total_income')
            if total_income:
                total_income = total_income.lower()
                if total_income == 'low':
                    queryset = queryset.filter(total_income__lt=3000)
                elif total_income == 'moderate':
                    queryset = queryset.filter(total_income__gte=3000, total_income__lte=5000)
                elif total_income == 'high':
                    queryset = queryset.filter(total_income__gt=5000)

            family_numbers = filters.get('family_numbers')
            if family_numbers:
                family_numbers = family_numbers.lower()
                if family_numbers == 'few':
                    queryset = queryset.filter(family_numbers__lt=3)
                elif family_numbers == 'moderate':
                    queryset = queryset.filter(family_numbers__gte=3, family_numbers__lte=4)
                elif family_numbers == 'many':
                    queryset = queryset.filter(family_numbers__gt=4)

            disabilities = filters.get('disabilities')
            if disabilities:
                queryset = queryset.filter(disabilities__icontains=disabilities)

            housing_status = filters.get('housing_status')
            if housing_status:
                queryset = queryset.filter(housing_status__iexact=housing_status)

            grade = filters.get('grade')
            if grade:
                queryset = queryset.filter(grade__icontains=grade)

            father_status = filters.get('father_status')
            if father_status:
                queryset = queryset.filter(father_status__icontains=father_status)

            mother_status = filters.get('mother_status')
            if mother_status:
                queryset = queryset.filter(mother_status__icontains=mother_status)

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
    



    # for read logs

    @staticmethod
    def log_data_access(actor_id, actor_type, action, target_type, solidarity_id=None , ip_address=None):
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs (actor_id, actor_type, action, target_type, solidarity_id, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [actor_id, actor_type, action, target_type, solidarity_id, ip_address])




    @staticmethod
    def get_all_logs(filters=None):
        queryset = Logs.objects.select_related('actor', 'solidarity').order_by('-logged_at')

        if filters:
            if filters.get('actor_id'):
                queryset = queryset.filter(actor__admin_id=filters['actor_id'])
            if filters.get('action'):
                queryset = queryset.filter(action__icontains=filters['action'])
            if filters.get('target_type'):
                queryset = queryset.filter(target_type=filters['target_type'])
                
        return queryset