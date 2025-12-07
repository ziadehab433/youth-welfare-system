from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.solidarity.models import Solidarities, Logs, SolidarityDocs
import logging
from rest_framework.exceptions import PermissionDenied, NotFound
from django.conf import settings
from apps.solidarity.utils import save_uploaded_file
from django.db.models import Q
from apps.solidarity.models import Solidarities, SolidarityDocs
from django.db.models import F, Value, Sum, DecimalField, Count 
from django.db.models.functions import Coalesce
from youth_welfare import settings
from django.db import connection

from django.db.models import Sum, Count, F, Value
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.db.models import Count, Sum, Case, When, Value, DecimalField, F, IntegerField
from django.db.models.functions import Coalesce
from ..utils import get_arabic_discount_type

    
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
    def assign_discounts(admin, solidarity, discount_data):
        """
        Assign discounts to a solidarity application
        Converts English discount types to Arabic for storage
        
        Args:
            admin: The admin performing the action
            solidarity: The solidarity instance
            discount_data: List with 'discount_type' (English) and 'discount_value'
        
        Returns:
            Updated solidarity instance
        """
    # Validate request status( fac admin can not assign discount until preapprove)
        status = solidarity.req_status.lower().strip()
        if status != 'موافقة مبدئية':
            logger.warning(f"Discount assignment rejected for {solidarity.solidarity_id}: "
                        f"Invalid status '{status}'")
            raise ValidationError({
                'req_status': f"Request status must be 'موافقة مبدئية', got '{solidarity.req_status}'"
            })
        
        total_discount = 0
        arabic_discount_types = []
        
        try:
            for discount in discount_data:
                # Get discount_value
                value = float(discount.get('discount_value', 0))
                total_discount += value
                
                # Convert English type to Arabic
                english_type = discount.get('discount_type')
                arabic_type = get_arabic_discount_type(english_type)
                
                if arabic_type and arabic_type not in arabic_discount_types:
                    arabic_discount_types.append(arabic_type)
            
            
            solidarity.total_discount = total_discount
            solidarity.discount_type = arabic_discount_types
            solidarity.approved_by = admin
            solidarity.updated_at = timezone.now()
            
            solidarity.save(update_fields=['total_discount', 'discount_type', 'approved_by', 'updated_at'])
            solidarity.refresh_from_db()
            
            logger.info(f"Saved solidarity {solidarity.solidarity_id}: "
                    f"total_discount={solidarity.total_discount}, "
                    f"discount_type={solidarity.discount_type}")
            
            return solidarity
            
        except Exception as e:
            logger.error(f"Error assigning discounts to solidarity {solidarity.solidarity_id}: {str(e)}")
            raise


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
        
        if admin and hasattr(admin, 'role') and admin.role == 'مدير ادارة':
            if getattr(admin, 'dept_id', None):
                faculty_ids = admin.dept.faculties_set.values_list('faculty_id', flat=True)
                queryset = queryset.filter(faculty_id__in=faculty_ids)
            else:
                return Solidarities.objects.none()

        if not filters:
            return queryset.order_by('-created_at')

        q_objects = Q()
        simple_filters = {}
        
        if filters.get('faculty'):
            simple_filters['faculty_id'] = filters['faculty']
        if filters.get('status'):
            simple_filters['req_status'] = filters['status']
        if filters.get('student_id'):
            simple_filters['student__student_id'] = filters['student_id']
        if filters.get('housing_status'):
            simple_filters['housing_status__iexact'] = filters['housing_status']
        if filters.get('grade'):
            q_objects &= Q(grade__icontains=filters['grade'])
        if filters.get('father_status'):
            q_objects &= Q(father_status__icontains=filters['father_status'])
        if filters.get('mother_status'):
            q_objects &= Q(mother_status__icontains=filters['mother_status'])
        if filters.get('disabilities'):
            q_objects &= Q(disabilities__icontains=filters['disabilities'])
            
        queryset = queryset.filter(**simple_filters)
        
        if filters.get('total_income'):
            income = filters['total_income'].lower()
            if income == 'low':
                q_objects &= Q(total_income__lt=3000)
            elif income == 'moderate':
                q_objects &= Q(total_income__gte=3000, total_income__lte=5000)
            elif income == 'high':
                q_objects &= Q(total_income__gt=5000)

        if filters.get('family_numbers'):
            numbers = filters['family_numbers'].lower()
            if numbers == 'few':
                q_objects &= Q(family_numbers__lt=3)
            elif numbers == 'moderate':
                q_objects &= Q(family_numbers__gte=3, family_numbers__lte=4)
            elif numbers == 'many':
                q_objects &= Q(family_numbers__gt=4)
                
        if q_objects:
            queryset = queryset.filter(q_objects)

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
    











    @staticmethod
    def get_student_application_detail(solidarity_id, student):
        try:
            solidarity = (
                Solidarities.objects
                .select_related('student', 'faculty')
                .get(pk=solidarity_id, student=student) 
            )
        except Solidarities.DoesNotExist:
            raise NotFound("Application not found or does not belong to the student.")
        
        return solidarity

    @staticmethod
    def get_approved_for_faculty_admin(admin):
        # 1. Permission and Base Queryset filtering
        if getattr(admin, 'role', None) != 'مسؤول كلية' or not hasattr(admin, 'faculty'):
            return Solidarities.objects.none(), {'total_approved': 0, 'total_discount': 0}

        qs = Solidarities.objects.select_related('student', 'faculty').filter(faculty=admin.faculty)
        qs = qs.filter(req_status='مقبول')
        annotated = qs.annotate(
            student_name=F('student__name'),
            student_pk=F('student__student_id'), 
            total_discount_coalesced=Coalesce(
                F('total_discount'),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ).values(
            'solidarity_id',
            'student_name',
            'student_pk',
            'total_income',
            'total_discount_coalesced'
        ).order_by('-created_at')
        # NOTE: Using the original 'qs' for counting and aggregation is more reliable.
        total_approved = qs.count()
        total_discount = qs.aggregate(
            total=Coalesce(
                Sum('total_discount'),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )['total'] or 0

        return annotated, {'total_approved': total_approved, 'total_discount': total_discount}
    
 

    @staticmethod
    def get_faculty_summary_for_dept_manager(admin):
        if getattr(admin, 'role', '') not in [ 'مدير ادارة' , 'مشرف النظام']:
            raise PermissionDenied("مسموح لمدير الادارة فقط")
        qs = Solidarities.objects.all()
        summary_qs = qs.values('faculty__faculty_id', 'faculty__name').annotate(
            approved_count=Count(
                Case(When(req_status='مقبول', then=1), output_field=IntegerField())
            ),
            pending_count=Count(
                Case(When(req_status='منتظر', then=1), output_field=IntegerField())
            ),
            total_approved_amount=Coalesce(
                Sum(
                    Case(
                        When(req_status='مقبول', then=F('total_discount')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    )
                ),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ).order_by('faculty__name')
        rows = []
        totals = {'total_approved_amount': Decimal('0.00'), 'total_approved_count': 0, 'total_pending_count': 0}

        for r in summary_qs:
            ta = r.get('total_approved_amount') or Decimal('0.00')
            ac = int(r.get('approved_count') or 0)
            pc = int(r.get('pending_count') or 0)
            rows.append({
                'faculty_id': r.get('faculty__faculty_id'),
                'faculty_name': r.get('faculty__name'),
                'total_approved_amount': ta,
                'approved_count': ac,
                'pending_count': pc,
            })
            totals['total_approved_amount'] += Decimal(str(ta))
            totals['total_approved_count'] += ac
            totals['total_pending_count'] += pc

        return rows, totals