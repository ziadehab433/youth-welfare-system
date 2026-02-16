from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from apps.event.models import Plans, Events


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
        """
        Check if the admin is allowed to manage (update / add-event / remove-event) this plan.
        - مسؤول كلية  → only plans that belong to their faculty
        - مدير ادارة   → only global plans (faculty IS NULL)
        """
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
    def get_all_plans():
        """Any admin can see all plans."""
        return Plans.objects.select_related('faculty').all().order_by('-created_at')

    @staticmethod
    def get_plan_detail(plan_id):
        """Return a single plan with its related events."""
        plan = get_object_or_404(
            Plans.objects.select_related('faculty').prefetch_related(
                'events',
                'events__dept',
                'events__faculty',
                'events__created_by',
                'events__family',
            ),
            pk=plan_id,
        )
        return plan

    # ─────────────────────── create ───────────────────────

    @staticmethod
    def create_plan(admin, validated_data):
        """
        - مسؤول كلية  → faculty is auto-set to their own faculty.
        - مدير ادارة   → faculty is taken from payload (or NULL for global).
        """
        if PlanService._is_faculty_admin(admin):
            if not admin.faculty:
                raise ValidationError("المسؤول غير مرتبط بأي كلية")
            validated_data['faculty'] = admin.faculty

        elif PlanService._is_dept_manager(admin):
            # faculty may or may not be provided — both are valid
            pass
        else:
            raise ValidationError("ليس لديك صلاحية إنشاء خطة")

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

        # event already in another plan?
        if event.plan_id is not None and event.plan_id != plan.plan_id:
            raise ValidationError("هذا النشاط مُضاف بالفعل إلى خطة أخرى")

        # # already in this plan?
        # if event.plan_id == plan.plan_id:
        #     raise ValidationError("هذا النشاط مُضاف بالفعل إلى هذه الخطة")

        # faculty-level plan → event must belong to same faculty
        if plan.faculty_id is not None:
            if event.faculty_id != plan.faculty_id:
                raise ValidationError(
                    "لا يمكن إضافة نشاط من كلية مختلفة إلى خطة خاصة بكلية محددة"
                )

        # Handle dept_id separately (FK field)
        dept_id = validated_data.pop('dept_id', None)
        if dept_id is not None:
            from apps.solidarity.models import Departments
            event.dept = get_object_or_404(Departments, pk=dept_id)

        # Update any other provided fields on the event
        for attr, value in validated_data.items():
            setattr(event, attr, value)

        # Link to plan and activate
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