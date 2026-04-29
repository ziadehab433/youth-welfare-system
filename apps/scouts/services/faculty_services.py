from django.utils import timezone
from django.db import transaction
from rest_framework import status as http_status
from ..models import Clans, ClanGroups, ScoutMembers
from apps.accounts.models import Students


# ============================================
# Constants
# ============================================
STATUS_PENDING = 'منتظر'
STATUS_ACCEPTED = 'مقبول'
STATUS_REJECTED = 'مرفوض'

MEMBER_ROLE = 'عضو'

GROUP_LEVEL_ROLES = [r[0] for r in ScoutMembers.GROUP_LEVEL_ROLES]
CLAN_LEVEL_ROLES = [r[0] for r in ScoutMembers.CLAN_LEVEL_ROLES]
ALL_LEADERSHIP_ROLES = CLAN_LEVEL_ROLES + GROUP_LEVEL_ROLES


class ScoutValidationError(Exception):
    def __init__(self, message, status_code=http_status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ============================================
# Lookups
# ============================================

def get_clan_or_error(admin):
    clan = Clans.objects.filter(faculty_id=admin.faculty_id).first()
    if not clan:
        raise ScoutValidationError(
            "لا توجد عشيرة لهذه الكلية",
            http_status.HTTP_404_NOT_FOUND
        )
    return clan


def get_member_or_error(member_id, clan):
    if member_id is None:
        raise ScoutValidationError("يجب تحديد رقم العضو")

    member = ScoutMembers.objects.select_related(
        'student', 'group'
    ).filter(
        scout_member_id=member_id,
        clan=clan
    ).first()

    if not member:
        raise ScoutValidationError(
            "هذا العضو غير موجود في عشيرتك",
            http_status.HTTP_404_NOT_FOUND
        )
    return member


def get_accepted_member_or_error(member_id, clan):
    member = get_member_or_error(member_id, clan)
    if member.status != STATUS_ACCEPTED:
        raise ScoutValidationError(
            f"العضو غير مقبول — الحالة الحالية: {member.status}"
        )
    return member


def get_group_or_error(group_id, clan):
    if group_id is None:
        raise ScoutValidationError("يجب تحديد رقم الرهط")

    group = ClanGroups.objects.filter(
        group_id=group_id,
        clan=clan
    ).first()

    if not group:
        raise ScoutValidationError(
            "هذا الرهط غير موجود في عشيرتك",
            http_status.HTTP_404_NOT_FOUND
        )
    return group


def require_field(request, field_name):
    """Get required field — rejects None AND empty strings"""
    value = request.data.get(field_name)
    if not value and value != 0:
        raise ScoutValidationError(f"يجب تحديد {field_name}")
    return value


# ============================================
# Clan Operations
# ============================================

def create_clan(serializer, admin_obj):
    with transaction.atomic():
        return serializer.save(
            created_by_id=admin_obj.admin_id,
            created_at=timezone.now()
        )


def update_clan(serializer):
    with transaction.atomic():
        return serializer.save(updated_at=timezone.now())


# ============================================
# Group Operations
# ============================================

def create_group(serializer):
    with transaction.atomic():
        return serializer.save(created_at=timezone.now())


def update_group(serializer):
    with transaction.atomic():
        return serializer.save(updated_at=timezone.now())


def delete_group(group):
    with transaction.atomic():
        now = timezone.now()
        affected = ScoutMembers.objects.filter(group=group).update(
            group=None, updated_at=now
        )
        group.delete()
    return affected


# ============================================
# Member Operations
# ============================================

def get_filtered_members(clan, query_params):
    members = clan.members.select_related('student', 'group').all()

    filter_status = query_params.get('status')
    if filter_status:
        members = members.filter(status=filter_status)

    filter_role = query_params.get('role')
    if filter_role:
        members = members.filter(role=filter_role)

    filter_group = query_params.get('group_id')
    if filter_group:
        members = members.filter(group_id=filter_group)

    if query_params.get('unassigned') == 'true':
        members = members.filter(group__isnull=True, status=STATUS_ACCEPTED)

    total = members.count()
    return members.order_by('-created_at'), total


def review_member(member, action_type, rejection_reason, admin_id):
    if member.status != STATUS_PENDING:
        raise ScoutValidationError(
            f"لا يمكن مراجعة هذا الطلب — الحالة الحالية: {member.status}"
        )

    with transaction.atomic():
        now = timezone.now()
        if action_type == 'approve':
            member.status = STATUS_ACCEPTED
            member.joined_at = now
        else:
            member.status = STATUS_REJECTED
            member.rejection_reason = rejection_reason

        member.reviewed_by_id = admin_id
        member.reviewed_at = now
        member.updated_at = now
        member.save()


def assign_member_to_group(member, group):
    with transaction.atomic():
        member.group = group
        member.updated_at = timezone.now()
        member.save()


def validate_role_change(member, new_role, clan):
    if new_role == MEMBER_ROLE:
        return

    if new_role in GROUP_LEVEL_ROLES and not member.group:
        raise ScoutValidationError(
            "لا يمكن تعيين دور رهط لعضو غير موزع على رهط"
        )

    conflict_qs = ScoutMembers.objects.select_related('student').filter(
        clan=clan,
        role=new_role,
        status=STATUS_ACCEPTED
    ).exclude(
        scout_member_id=member.scout_member_id
    )

    if new_role in GROUP_LEVEL_ROLES:
        conflict_qs = conflict_qs.filter(group=member.group)

    holder = conflict_qs.first()
    if holder:
        raise ScoutValidationError(
            f"هذا المنصب مشغول بالفعل بواسطة {holder.student.name}"
        )

    has_leadership = ScoutMembers.objects.filter(
        student=member.student,
        clan=clan,
        status=STATUS_ACCEPTED,
        role__in=ALL_LEADERSHIP_ROLES
    ).exclude(
        scout_member_id=member.scout_member_id
    ).exists()

    if has_leadership:
        raise ScoutValidationError(
            "هذا العضو لديه دور قيادي بالفعل"
        )


def change_member_role(member, new_role):
    with transaction.atomic():
        member.role = new_role
        member.updated_at = timezone.now()
        member.save()


def transfer_member(member, new_group):
    old_role = member.role
    role_was_reset = False

    with transaction.atomic():
        if member.role in GROUP_LEVEL_ROLES:
            member.role = MEMBER_ROLE
            role_was_reset = True
        member.group = new_group
        member.updated_at = timezone.now()
        member.save()

    return role_was_reset, old_role


def remove_member(member):
    info = {
        'name': member.student.name,
        'role': member.role,
        'student_id': member.student_id,
    }
    with transaction.atomic():
        member.delete()
    return info


def add_student_by_nid(nid, clan):
    student = Students.objects.filter(nid=nid).first()
    if not student:
        raise ScoutValidationError(
            "لا يوجد طالب بهذا الرقم القومي",
            http_status.HTTP_404_NOT_FOUND
        )

    if student.faculty_id != clan.faculty_id:
        raise ScoutValidationError(
            "هذا الطالب ينتمي إلى كلية أخرى"
        )

    existing = ScoutMembers.objects.filter(
        student_id=student.student_id,
        clan=clan
    ).first()

    if existing:
        if existing.status == STATUS_ACCEPTED:
            raise ScoutValidationError(
                f"{student.name} عضو بالفعل في العشيرة"
            )
        if existing.status == STATUS_PENDING:
            raise ScoutValidationError(
                f"{student.name} لديه طلب انضمام قيد المراجعة"
            )

    return student, existing


def reactivate_rejected_member(existing, admin_id):
    with transaction.atomic():
        now = timezone.now()
        existing.status = STATUS_ACCEPTED
        existing.role = MEMBER_ROLE
        existing.group = None
        existing.rejection_reason = None
        existing.reviewed_by_id = admin_id
        existing.reviewed_at = now
        existing.joined_at = now
        existing.updated_at = now
        existing.save()


def create_member_directly(student, clan, admin_id):
    with transaction.atomic():
        now = timezone.now()
        ScoutMembers.objects.create(
            student=student,
            clan=clan,
            role=MEMBER_ROLE,
            status=STATUS_ACCEPTED,
            reviewed_by_id=admin_id,
            reviewed_at=now,
            joined_at=now,
            created_at=now,
        )