from django.utils import timezone
from django.db import transaction
from rest_framework import status as http_status
from ..models import Clans, ClanGroups, ScoutMembers


class ScoutValidationError(Exception):
    def __init__(self, message, status_code=http_status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ============================================
# Lookups
# ============================================

def get_clan_or_error(clan_id):
    if not clan_id:
        raise ScoutValidationError("يجب تحديد رقم العشيرة")

    clan = Clans.objects.select_related('faculty').filter(
        clan_id=clan_id
    ).first()

    if not clan:
        raise ScoutValidationError(
            "العشيرة غير موجودة",
            http_status.HTTP_404_NOT_FOUND
        )
    return clan


def get_member_or_error(member_id, clan):
    if not member_id:
        raise ScoutValidationError("يجب تحديد رقم العضو")

    member = ScoutMembers.objects.select_related(
        'student', 'group'
    ).filter(
        scout_member_id=member_id,
        clan=clan
    ).first()

    if not member:
        raise ScoutValidationError(
            "هذا العضو غير موجود في هذه العشيرة",
            http_status.HTTP_404_NOT_FOUND
        )
    return member


def get_accepted_member_or_error(member_id, clan):
    member = get_member_or_error(member_id, clan)
    if member.status != 'مقبول':
        raise ScoutValidationError(
            f"العضو غير مقبول — الحالة الحالية: {member.status}"
        )
    return member


def require_field(request, field_name, source='data'):
    """Get required field from request.data or request.query_params"""
    if source == 'query':
        value = request.query_params.get(field_name)
    else:
        value = request.data.get(field_name)

    if value is None:
        raise ScoutValidationError(f"يجب تحديد {field_name}")
    return value


# ============================================
# Clan Listing & Filters
# ============================================

def get_all_clans(query_params):
    """Get all clans with optional status filter"""
    clans = Clans.objects.select_related('faculty').all().order_by('name')

    filter_status = query_params.get('status')
    if filter_status:
        clans = clans.filter(status=filter_status)

    return clans


def filter_serialized_clans(data, query_params):
    """Apply post-serialization filters (meets_minimum, structure_complete)"""
    meets_min = query_params.get('meets_minimum')
    if meets_min == 'true':
        data = [c for c in data if c['accepted_count'] >= c['min_members']]
    elif meets_min == 'false':
        data = [c for c in data if c['accepted_count'] < c['min_members']]

    structure_filter = query_params.get('structure_complete')
    if structure_filter == 'true':
        data = [c for c in data if c['is_structure_complete']]
    elif structure_filter == 'false':
        data = [c for c in data if not c['is_structure_complete']]

    return data


def build_clans_summary(all_clans_data):
    """Build summary stats from serialized clan data"""
    return {
        'total_clans': len(all_clans_data),
        'active_clans': len(
            [c for c in all_clans_data if c['status'] == 'active']
        ),
        'total_members': sum(
            c['members_count'] for c in all_clans_data
        ),
        'total_accepted': sum(
            c['accepted_count'] for c in all_clans_data
        ),
        'total_pending': sum(
            c['pending_count'] for c in all_clans_data
        ),
    }


# ============================================
# Clan Members & Groups (Read)
# ============================================

def get_filtered_members(clan, query_params):
    """Get clan members with optional filters"""
    members = clan.members.select_related(
        'student', 'group'
    ).all()

    filter_status = query_params.get('status')
    if filter_status:
        members = members.filter(status=filter_status)

    filter_role = query_params.get('role')
    if filter_role:
        members = members.filter(role=filter_role)

    return members.order_by('-created_at')


def get_clan_groups(clan):
    """Get all groups ordered by display_order"""
    return clan.groups.all().order_by('display_order')


# ============================================
# Administrative Interventions
# ============================================

def validate_clan_status(new_status):
    if new_status not in ['active', 'inactive']:
        raise ScoutValidationError(
            "حالة العشيرة يجب أن تكون 'active' أو 'inactive'"
        )


def change_clan_status(clan, new_status):
    with transaction.atomic():
        clan.status = new_status
        clan.updated_at = timezone.now()
        clan.save()


def validate_role_change(member, new_role, clan):
    """Full role change validation (gender + uniqueness + single leadership)"""
    if new_role == 'MEMBER':
        return

    # Gender validation
    MALE_ONLY = ['ASSISTANT_MALE', 'GROUP_LEADER_MALE', 'GROUP_ASSISTANT_MALE']
    FEMALE_ONLY = ['ASSISTANT_FEMALE', 'GROUP_LEADER_FEMALE', 'GROUP_ASSISTANT_FEMALE']

    if member.student.gender == 'M' and new_role in FEMALE_ONLY:
        raise ScoutValidationError(
            "لا يمكن تعيين طالب ذكر في منصب مخصص للإناث"
        )
    if member.student.gender == 'F' and new_role in MALE_ONLY:
        raise ScoutValidationError(
            "لا يمكن تعيين طالبة أنثى في منصب مخصص للذكور"
        )

    # Group-level role requires group
    GROUP_ROLES = [
        'GROUP_LEADER_MALE', 'GROUP_LEADER_FEMALE',
        'GROUP_ASSISTANT_MALE', 'GROUP_ASSISTANT_FEMALE',
    ]
    CLAN_ROLES = [
        'CLAN_LEADER', 'ASSISTANT_MALE', 'ASSISTANT_FEMALE',
        'HEAD_ROVER', 'SECRETARY', 'EQUIPMENT_MANAGER', 'VETERAN',
    ]

    if new_role in GROUP_ROLES and not member.group:
        raise ScoutValidationError(
            "لا يمكن تعيين دور رهط لعضو غير موزع على رهط"
        )

    # Uniqueness check
    conflict_qs = ScoutMembers.objects.filter(
        clan=clan, role=new_role, status='مقبول'
    ).exclude(scout_member_id=member.scout_member_id)

    if new_role in GROUP_ROLES:
        conflict_qs = conflict_qs.filter(group=member.group)

    holder = conflict_qs.select_related('student').first()
    if holder:
        raise ScoutValidationError(
            f"هذا المنصب مشغول بالفعل بواسطة {holder.student.name}"
        )

    # Single leadership check
    has_other_leadership = ScoutMembers.objects.filter(
        student=member.student, clan=clan, status='مقبول'
    ).exclude(
        role='MEMBER'
    ).exclude(
        scout_member_id=member.scout_member_id
    ).exists()

    if has_other_leadership:
        raise ScoutValidationError(
            "هذا العضو لديه دور قيادي بالفعل"
        )


def change_member_role(member, new_role):
    with transaction.atomic():
        member.role = new_role
        member.updated_at = timezone.now()
        member.save()


def remove_member(member):
    info = {
        'name': member.student.name,
        'role': member.role,
        'student_id': member.student_id,
    }
    with transaction.atomic():
        member.delete()
    return info