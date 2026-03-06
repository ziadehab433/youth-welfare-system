from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from apps.event.models import Plans, Events
import logging

logger = logging.getLogger(__name__)


class PlanService:

    # ─────────────────────── helpers ───────────────────────

    @staticmethod
    def _is_faculty_admin(admin):
        return admin.role == 'مسؤول كلية'

    @staticmethod
    def _is_dept_manager(admin):
        return admin.role == 'مدير ادارة'

    @staticmethod
    def _can_manage_plan(admin, plan):
        if PlanService._is_faculty_admin(admin):
            if not admin.faculty:
                raise ValidationError("المسؤول غير مرتبط بأي كلية")
            if plan.faculty_id != admin.faculty_id:
                raise ValidationError("لا يمكنك التعديل على خطة تابعة لكلية أخرى")
            return True

        if PlanService._is_dept_manager(admin):
            if plan.faculty_id is not None:
                raise ValidationError("مدير الإدارة يمكنه التعديل على الخطط العامة فقط")
            return True

        raise ValidationError("ليس لديك صلاحية التعديل على هذه الخطة")

    # ─────────────────────── list / detail ───────────────────────

    @staticmethod
    def get_all_plans(admin):
        """
        Get plans filtered by admin role:
        - مسؤول كلية: only plans created by them
        - مدير ادارة: only plans created by them
        - مدير كلية: all plans in their faculty
        - مدير عام: only global plans (faculty_id is null)
        - مشرف النظام: all plans
        """
        queryset = Plans.objects.select_related('faculty', 'dept', 'created_by')
        
        role = admin.role
        
        if role == 'مسؤول كلية':
            # Faculty admin: only their own plans
            queryset = queryset.filter(created_by=admin)
            logger.info(f"Faculty admin {admin.admin_id} accessing their own plans")
        
        elif role == 'مدير ادارة':
            # Department manager: only their own plans
            queryset = queryset.filter(created_by=admin)
            logger.info(f"Department manager {admin.admin_id} accessing their own plans")
        
        elif role == 'مدير كلية':
            # Faculty head: all plans in their faculty
            if not admin.faculty:
                logger.warning(f"Faculty head {admin.admin_id} has no faculty assigned")
                raise ValidationError("مدير الكلية غير مرتبط بأي كلية")
            queryset = queryset.filter(faculty=admin.faculty)
            logger.info(f"Faculty head {admin.admin_id} accessing plans for faculty {admin.faculty_id}")
        
        elif role == 'مدير عام':
            # General manager: only global plans (no faculty)
            queryset = queryset.filter(faculty__isnull=True)
            logger.info(f"General manager {admin.admin_id} accessing global plans")
        
        elif role == 'مشرف النظام':
            # System admin: all plans (no filter)
            logger.info(f"System admin {admin.admin_id} accessing all plans")
            pass
        
        else:
            # Unknown role: no access
            logger.warning(f"Admin {admin.admin_id} with unknown role '{role}' attempted to access plans")
            raise ValidationError("ليس لديك صلاحية عرض الخطط")
        
        return queryset.order_by('-created_at')

    @staticmethod
    def get_plan_detail(admin, plan_id):
        """
        Get plan detail with role-based access control.
        Same filtering rules as get_all_plans.
        """
        plan = get_object_or_404(
            Plans.objects
            .select_related('faculty', 'dept', 'created_by')
            .prefetch_related(
                'events',
                'events__dept',
                'events__faculty',
                'events__created_by',
                'events__family',
            ),
            pk=plan_id,
        )
        
        role = admin.role
        
        # Apply same access rules as list
        if role == 'مسؤول كلية':
            if plan.created_by_id != admin.admin_id:
                logger.warning(f"Faculty admin {admin.admin_id} denied access to plan {plan_id} (not creator)")
                raise ValidationError("ليس لديك صلاحية عرض هذه الخطة - يمكنك فقط عرض الخطط التي أنشأتها")
        
        elif role == 'مدير ادارة':
            if plan.created_by_id != admin.admin_id:
                logger.warning(f"Department manager {admin.admin_id} denied access to plan {plan_id} (not creator)")
                raise ValidationError("ليس لديك صلاحية عرض هذه الخطة - يمكنك فقط عرض الخطط التي أنشأتها")
        
        elif role == 'مدير كلية':
            if not admin.faculty:
                logger.warning(f"Faculty head {admin.admin_id} has no faculty assigned")
                raise ValidationError("مدير الكلية غير مرتبط بأي كلية")
            if plan.faculty_id != admin.faculty_id:
                logger.warning(f"Faculty head {admin.admin_id} denied access to plan {plan_id} (different faculty)")
                raise ValidationError("ليس لديك صلاحية عرض هذه الخطة - هذه الخطة تابعة لكلية أخرى")
        
        elif role == 'مدير عام':
            if plan.faculty_id is not None:
                logger.warning(f"General manager {admin.admin_id} denied access to plan {plan_id} (not global)")
                raise ValidationError("ليس لديك صلاحية عرض هذه الخطة - يمكنك فقط عرض الخطط العامة")
        
        elif role == 'مشرف النظام':
            # System admin: full access
            logger.info(f"System admin {admin.admin_id} accessing plan {plan_id}")
            pass
        
        else:
            logger.warning(f"Admin {admin.admin_id} with unknown role '{role}' attempted to access plan {plan_id}")
            raise ValidationError("ليس لديك صلاحية عرض هذه الخطة")
        
        logger.info(f"Admin {admin.admin_id} ({role}) successfully accessed plan {plan_id}")
        return plan

    # ─────────────────────── create ───────────────────────

    @staticmethod
    def create_plan(admin, validated_data):
        if PlanService._is_faculty_admin(admin):
            if not admin.faculty:
                raise ValidationError("المسؤول غير مرتبط بأي كلية")
            validated_data['faculty'] = admin.faculty

        elif PlanService._is_dept_manager(admin):
            pass
        else:
            raise ValidationError("ليس لديك صلاحية إنشاء خطة")

        # ✅ Auto-set created_by from the logged-in admin
        validated_data['created_by'] = admin

        plan = Plans.objects.create(**validated_data)
        return plan

    # ─────────────────────── update ───────────────────────

    @staticmethod
    def update_plan(admin, plan_id, validated_data):
        plan = get_object_or_404(Plans, pk=plan_id)
        PlanService._can_manage_plan(admin, plan)

        for attr, value in validated_data.items():
            setattr(plan, attr, value)
        plan.save()
        return plan

    # ─────────────────────── add event ───────────────────────

    @staticmethod
    def add_event_to_plan(admin, plan_id, validated_data):
        plan = get_object_or_404(Plans, pk=plan_id)
        PlanService._can_manage_plan(admin, plan)

        event_id = validated_data.pop('event_id')
        event = get_object_or_404(Events, pk=event_id)

        if event.plan_id is not None and event.plan_id != plan.plan_id:
            raise ValidationError("هذا النشاط مُضاف بالفعل إلى خطة أخرى")

        if plan.faculty_id is not None:
            if event.faculty_id != plan.faculty_id:
                raise ValidationError(
                    "لا يمكن إضافة نشاط من كلية مختلفة إلى خطة خاصة بكلية محددة"
                )

        dept_id = validated_data.pop('dept_id', None)
        if dept_id is not None:
            from apps.solidarity.models import Departments
            event.dept = get_object_or_404(Departments, pk=dept_id)

        for attr, value in validated_data.items():
            setattr(event, attr, value)

        event.plan = plan
        event.active = True
        event.save()
        return event

    # ─────────────────────── remove event ───────────────────────

    @staticmethod
    def remove_event_from_plan(admin, plan_id, event_id):
        plan = get_object_or_404(Plans, pk=plan_id)
        PlanService._can_manage_plan(admin, plan)

        event = get_object_or_404(Events, pk=event_id)

        if event.plan_id != plan.plan_id:
            raise ValidationError("هذا النشاط لا ينتمي إلى هذه الخطة")

        event.plan = None
        event.active = False
        event.save(update_fields=['plan_id', 'active'])
        return event