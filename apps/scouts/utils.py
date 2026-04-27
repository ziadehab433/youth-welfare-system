from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from .models import Clans, ClanGroups, ScoutMembers


# ============================================
# Permission Checks
# ============================================

def is_faculty_admin(admin_data):
    if admin_data.get('role') != 'مسؤول كلية':
        raise PermissionDenied("ليس لديك صلاحية للقيام بهذا الإجراء")


def is_dept_manager(admin_data):
    if admin_data.get('role') != 'مدير ادارة':
        raise PermissionDenied("ليس لديك صلاحية للقيام بهذا الإجراء")


def is_faculty_admin_or_dept_manager(admin_data):
    if admin_data.get('role') not in ['مسؤول كلية', 'مدير ادارة']:
        raise PermissionDenied("ليس لديك صلاحية للقيام بهذا الإجراء")


# ============================================
# Clan Helpers
# ============================================

def get_admin_clan(admin_data):
    faculty_id = admin_data.get('faculty_id')
    if not faculty_id:
        raise NotFound("لم يتم تحديد الكلية الخاصة بك")

    try:
        return Clans.objects.get(faculty_id=faculty_id)
    except Clans.DoesNotExist:
        raise NotFound("لا توجد عشيرة مرتبطة بكليتك")


def get_clan_or_404(clan_id):
    try:
        return Clans.objects.get(clan_id=clan_id)
    except Clans.DoesNotExist:
        raise NotFound("العشيرة غير موجودة")


# ============================================
# Group Helpers
# ============================================

def get_group_or_404(group_id):
    try:
        return ClanGroups.objects.get(group_id=group_id)
    except ClanGroups.DoesNotExist:
        raise NotFound("الرهط غير موجود")


def validate_group_belongs_to_clan(group, clan):
    if group.clan_id != clan.clan_id:
        raise ValidationError("هذا الرهط لا ينتمي إلى هذه العشيرة")


# ============================================
# Member Helpers
# ============================================

def get_member_or_404(scout_member_id):
    try:
        return ScoutMembers.objects.select_related(
            'student', 'clan', 'group'
        ).get(scout_member_id=scout_member_id)
    except ScoutMembers.DoesNotExist:
        raise NotFound("العضو غير موجود")


def validate_member_belongs_to_clan(member, clan):
    if member.clan_id != clan.clan_id:
        raise ValidationError("هذا العضو لا ينتمي إلى هذه العشيرة")


def validate_member_is_pending(member):
    if member.status != 'منتظر':
        raise ValidationError("لا يمكن مراجعة هذا الطلب لأنه تمت مراجعته مسبقاً")


def validate_member_is_accepted(member):
    if member.status != 'مقبول':
        raise ValidationError("يجب قبول العضو أولاً قبل القيام بهذا الإجراء")


# ============================================
# Role Validation
# ============================================

UNIQUE_CLAN_ROLES = [
    'CLAN_LEADER',
    'ASSISTANT_MALE',
    'ASSISTANT_FEMALE',
    'HEAD_ROVER',
    'SECRETARY',
    'EQUIPMENT_MANAGER',
    'VETERAN',
]

UNIQUE_GROUP_ROLES = [
    'GROUP_LEADER_MALE',
    'GROUP_LEADER_FEMALE',
    'GROUP_ASSISTANT_MALE',
    'GROUP_ASSISTANT_FEMALE',
]

ALL_LEADERSHIP_ROLES = UNIQUE_CLAN_ROLES + UNIQUE_GROUP_ROLES


def validate_unique_role(clan, role, group=None, exclude_member_id=None):
    """
    Ensure no duplicate leadership roles:
    - Clan-level roles: one per clan
    - Group-level roles: one per group
    """
    if role == 'MEMBER':
        return

    query = ScoutMembers.objects.filter(
        clan=clan,
        role=role,
        status='مقبول'
    )

    if exclude_member_id:
        query = query.exclude(scout_member_id=exclude_member_id)

    if role in UNIQUE_CLAN_ROLES:
        if query.exists():
            raise ValidationError(
                f"يوجد عضو آخر يشغل منصب {dict(ScoutMembers.ROLE_CHOICES).get(role)} بالفعل"
            )

    if role in UNIQUE_GROUP_ROLES:
        if not group:
            raise ValidationError(
                "يجب تعيين العضو في رهط قبل إسناد هذا المنصب"
            )
        if query.filter(group=group).exists():
            raise ValidationError(
                f"يوجد عضو آخر يشغل منصب {dict(ScoutMembers.ROLE_CHOICES).get(role)} في هذا الرهط بالفعل"
            )


def validate_single_leadership_role(member, new_role, clan):
    """Ensure a member doesn't hold multiple leadership roles"""
    if new_role == 'MEMBER':
        return

    existing_leadership = ScoutMembers.objects.filter(
        student=member.student,
        clan=clan,
        status='مقبول',
        role__in=ALL_LEADERSHIP_ROLES
    ).exclude(
        scout_member_id=member.scout_member_id
    ).exists()

    if existing_leadership:
        raise ValidationError(
            "هذا العضو يشغل منصباً قيادياً آخر بالفعل"
        )


# ============================================
# Statistics Helpers
# ============================================

def get_clan_stats(clan):
    members = clan.members.all()

    return {
        'total_members': members.count(),
        'accepted_count': members.filter(status='مقبول').count(),
        'pending_count': members.filter(status='منتظر').count(),
        'rejected_count': members.filter(status='مرفوض').count(),
        'groups_count': clan.groups.count(),
        'unassigned_count': members.filter(
            status='مقبول',
            group__isnull=True
        ).count(),
    }


def get_clan_structure(clan):
    leaders = clan.members.filter(
        status='مقبول'
    ).exclude(
        role='MEMBER'
    ).select_related('student', 'group')

    structure = {
        'clan_level': {},
        'group_level': {},
    }

    for member in leaders:
        role_data = {
            'scout_member_id': member.scout_member_id,
            'name': member.student.name,
            'gender': member.student.gender,
            'group': member.group.name if member.group else None,
        }

        if member.role in UNIQUE_CLAN_ROLES:
            structure['clan_level'][member.role] = role_data
        elif member.role in UNIQUE_GROUP_ROLES:
            group_name = member.group.name if member.group else 'غير محدد'
            if group_name not in structure['group_level']:
                structure['group_level'][group_name] = {}
            structure['group_level'][group_name][member.role] = role_data

    return structure


# ============================================
# Response Helpers
# ============================================

def success_response(message, data=None, status_code=200):
    response = {
        'success': True,
        'message': message,
    }
    if data is not None:
        response['data'] = data
    return response


def error_response(message, errors=None, status_code=400):
    response = {
        'success': False,
        'message': message,
    }
    if errors is not None:
        response['errors'] = errors
    return response


# ============================================
# Log Action Names (Arabic)
# ============================================

SCOUT_LOG_ACTIONS = {
    # Clan
    'create_clan': 'إنشاء عشيرة',
    'update_clan': 'تعديل بيانات العشيرة',
    'change_clan_status': 'تغيير حالة العشيرة',

    # Groups
    'create_group': 'إنشاء رهط',
    'update_group': 'تعديل بيانات الرهط',
    'delete_group': 'حذف رهط',

    # Members
    'approve_member': 'قبول طلب انضمام',
    'reject_member': 'رفض طلب انضمام',
    'assign_group': 'توزيع عضو على رهط',
    'change_role': 'تغيير دور عضو',
    'transfer_member': 'نقل عضو بين رهوط',
    'remove_member': 'إزالة عضو من العشيرة',
    'add_by_nid': 'إضافة عضو بالرقم القومي',
}

SCOUT_TARGET_TYPE = 'جوالة'