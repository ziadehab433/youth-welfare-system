from django.utils import timezone
from django.db import transaction
from rest_framework import status as http_status
from ..models import Clans, ScoutMembers


# ============================================
# Constants
# ============================================
STATUS_PENDING = 'منتظر'
STATUS_ACCEPTED = 'مقبول'
STATUS_REJECTED = 'مرفوض'

CLAN_STATUS_ACTIVE = 'نشط'

MEMBER_ROLE = 'عضو'

GROUP_LEADERSHIP_ROLES = [r[0] for r in ScoutMembers.GROUP_LEVEL_ROLES]


class ScoutValidationError(Exception):
    def __init__(self, message, status_code=http_status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ============================================
# Clan
# ============================================

def get_student_clan(faculty_id):
    """Get active clan for the student's faculty — returns None if not found"""
    return Clans.objects.filter(
        faculty_id=faculty_id,
        status=CLAN_STATUS_ACTIVE
    ).first()


def get_student_clan_or_error(faculty_id):
    """Get active clan for student's faculty — raises error if not found"""
    clan = Clans.objects.filter(
        faculty_id=faculty_id,
        status=CLAN_STATUS_ACTIVE
    ).first()

    if not clan:
        raise ScoutValidationError(
            "لا توجد عشيرة متاحة لكليتك حالياً",
            http_status.HTTP_404_NOT_FOUND
        )
    return clan


# ============================================
# Membership Queries
# ============================================

def get_membership_with_details(student_id):
    """Get membership with clan and group details"""
    return ScoutMembers.objects.select_related(
        'clan', 'group'
    ).filter(
        student_id=student_id
    ).first()


def get_accepted_membership(student_id):
    """Get accepted membership or raise error"""
    membership = ScoutMembers.objects.select_related(
        'clan', 'group'
    ).filter(
        student_id=student_id,
        status=STATUS_ACCEPTED
    ).first()

    if not membership:
        raise ScoutValidationError(
            "ليس لديك عضوية مقبولة في أي عشيرة",
            http_status.HTTP_403_FORBIDDEN
        )
    return membership


# ============================================
# Join
# ============================================

def join_clan(student_id, clan):
    with transaction.atomic():
        existing = ScoutMembers.objects.select_for_update().filter(
            student_id=student_id,
            clan=clan
        ).first()

        if not existing:
            ScoutMembers.objects.create(
                student_id=student_id,
                clan=clan,
                role=MEMBER_ROLE,
                status=STATUS_PENDING,
                created_at=timezone.now(),
            )
            return 'new', None

        if existing.status == STATUS_PENDING:
            raise ScoutValidationError(
                "لديك طلب انضمام قيد المراجعة بالفعل"
            )

        if existing.status == STATUS_ACCEPTED:
            raise ScoutValidationError(
                "أنت عضو بالفعل في العشيرة"
            )

        if existing.status == STATUS_REJECTED:
            existing.status = STATUS_PENDING
            existing.role = MEMBER_ROLE
            existing.group = None
            existing.rejection_reason = None
            existing.reviewed_by = None
            existing.reviewed_at = None
            existing.joined_at = None
            existing.updated_at = timezone.now()
            existing.save()
            return 'reapply', existing

        raise ScoutValidationError(
            "حالة العضوية غير معروفة"
        )


# ============================================
# Dashboard
# ============================================

def get_dashboard_data(membership):
    """Build the full dashboard response data — single query optimized"""
    dashboard = {
        'membership': {
            'role': membership.role,
            'status': membership.status,
            'joined_at': membership.joined_at,
        },
        'clan': {
            'clan_id': membership.clan.clan_id,
            'name': membership.clan.name,
            'description': membership.clan.description,
        },
        'group': None,
        'group_leaders': None,
        'group_members': [],
    }

    if not membership.group:
        return dashboard

    # Group info
    dashboard['group'] = {
        'group_id': membership.group.group_id,
        'name': membership.group.name,
    }

    group_mates = ScoutMembers.objects.select_related(
        'student'
    ).filter(
        group=membership.group,
        status=STATUS_ACCEPTED,
    ).exclude(
        scout_member_id=membership.scout_member_id
    )

    leaders = {}
    members = []

    for mate in group_mates:
        if mate.role in GROUP_LEADERSHIP_ROLES:
            leaders[mate.role] = {
                'name': mate.student.name,
                'email': mate.student.email,
                'phone': mate.student.phone_number,
            }
        members.append({
            'name': mate.student.name,
            'role': mate.role,
            'gender': mate.student.gender,
        })

    dashboard['group_leaders'] = leaders
    dashboard['group_members'] = members

    return dashboard