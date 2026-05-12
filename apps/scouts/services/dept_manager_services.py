from django.utils import timezone
from django.db import transaction
from rest_framework import status as http_status
from ..models import Clans, ClanGroups, ScoutMembers, UniversityScoutProgramMembers,UniversityScoutPrograms,UniversityScoutMembers
# ============================================
# Shared Constants
# ============================================

class Roles:
    """All scout roles — reads from Model"""
    MEMBER = 'عضو'

    CLAN_LEADER = 'قائد العشيرة'
    ASSISTANT_MALE = 'مساعد قائد'
    ASSISTANT_FEMALE = 'مساعدة قائد'
    HEAD_ROVER = 'رائد أكبر'
    SECRETARY = 'سكرتير'
    EQUIPMENT_MANAGER = 'مسؤول عهدة'
    VETERAN = 'قائد السواعد'

    GROUP_LEADER_MALE = 'رائد رهط'
    GROUP_LEADER_FEMALE = 'رائدة رهط'
    GROUP_ASSISTANT_MALE = 'مساعد رائد'
    GROUP_ASSISTANT_FEMALE = 'مساعدة رائد'

    CLAN_LEVEL = [
        CLAN_LEADER, ASSISTANT_MALE, ASSISTANT_FEMALE,
        HEAD_ROVER, SECRETARY, EQUIPMENT_MANAGER, VETERAN,
    ]

    GROUP_LEVEL = [
        GROUP_LEADER_MALE, GROUP_LEADER_FEMALE,
        GROUP_ASSISTANT_MALE, GROUP_ASSISTANT_FEMALE,
    ]

    ALL_LEADERSHIP = CLAN_LEVEL + GROUP_LEVEL

    MALE_ONLY = [ASSISTANT_MALE, GROUP_LEADER_MALE, GROUP_ASSISTANT_MALE]
    FEMALE_ONLY = [ASSISTANT_FEMALE, GROUP_LEADER_FEMALE, GROUP_ASSISTANT_FEMALE]

class UniversityRoles:

    LEADER = 'قائد عشاير الجامعة'
    ASSISTANT = 'مساعد قائد العشاير'
    PROGRAM_EXECUTOR = 'منفذ برامج'
    FEMALE_LEADER = 'قائد الجوالات'
    SECRETARY = 'سكرتير العشاير'
    VETERAN = 'قائد السواعد'

    ALL = [
        LEADER,
        ASSISTANT,
        PROGRAM_EXECUTOR,
        FEMALE_LEADER,
        SECRETARY,
        VETERAN,
    ]

class Status:
    """All member statuses"""
    PENDING = 'منتظر'
    ACCEPTED = 'مقبول'
    REJECTED = 'مرفوض'


class ClanStatus:
    """All clan statuses"""
    ACTIVE = 'نشط'
    INACTIVE = 'غير نشط'
    VALID = [ACTIVE, INACTIVE]


# ============================================
# Exceptions
# ============================================

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
    if member.status != Status.ACCEPTED:
        raise ScoutValidationError(
            f"العضو غير مقبول — الحالة الحالية: {member.status}"
        )
    return member


def require_field(request, field_name, source='data'):
    """Get required field — rejects None AND empty strings"""
    if source == 'query':
        value = request.query_params.get(field_name)
    else:
        value = request.data.get(field_name)

    if not value and value != 0:
        raise ScoutValidationError(f"يجب تحديد {field_name}")
    return value


# ============================================
# Clan Listing & Filters
# ============================================

def get_all_clans(query_params):
    """Get all clans with DB-level filters"""
    clans = Clans.objects.select_related('faculty').all().order_by('name')

    filter_status = query_params.get('status')
    if filter_status:
        if filter_status not in ClanStatus.VALID:
            raise ScoutValidationError(
                f"حالة العشيرة يجب أن تكون '{ClanStatus.ACTIVE}' أو '{ClanStatus.INACTIVE}'"
            )
        clans = clans.filter(status=filter_status)

    return clans


def filter_serialized_clans(data, query_params):
    """
    Post-serialization filters for computed fields.
    (these require aggregation — can't easily do in DB with select_related)
    """
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
            [c for c in all_clans_data if c['status'] == ClanStatus.ACTIVE]
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
# Clan Members & Groups
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
    if new_status not in ClanStatus.VALID:
        raise ScoutValidationError(
            f"حالة العشيرة يجب أن تكون '{ClanStatus.ACTIVE}' أو '{ClanStatus.INACTIVE}'"
        )


def change_clan_status(clan, new_status):
    """Change clan status — fully atomic with lock"""
    with transaction.atomic():
        locked_clan = Clans.objects.select_for_update().get(
            clan_id=clan.clan_id
        )
        locked_clan.status = new_status
        locked_clan.updated_at = timezone.now()
        locked_clan.save()
        clan.status = new_status


def _validate_role_change_locked(member, new_role, clan):
    if new_role == Roles.MEMBER:
        return

    if member.student.gender == 'M' and new_role in Roles.FEMALE_ONLY:
        raise ScoutValidationError(
            "لا يمكن تعيين طالب ذكر في منصب مخصص للإناث"
        )
    if member.student.gender == 'F' and new_role in Roles.MALE_ONLY:
        raise ScoutValidationError(
            "لا يمكن تعيين طالبة أنثى في منصب مخصص للذكور"
        )

    if new_role in Roles.GROUP_LEVEL and not member.group:
        raise ScoutValidationError(
            "لا يمكن تعيين دور رهط لعضو غير موزع على رهط"
        )

    conflict_qs = ScoutMembers.objects.select_for_update().filter(
        clan=clan,
        role=new_role,
        status=Status.ACCEPTED
    ).exclude(
        scout_member_id=member.scout_member_id
    )

    if new_role in Roles.GROUP_LEVEL:
        conflict_qs = conflict_qs.filter(group=member.group)

    conflict = conflict_qs.first()
    if conflict:
        conflict_name = ScoutMembers.objects.select_related(
            'student'
        ).get(
            scout_member_id=conflict.scout_member_id
        ).student.name
        raise ScoutValidationError(
            f"هذا المنصب مشغول بالفعل بواسطة {conflict_name}"
        )

    has_other_leadership = ScoutMembers.objects.select_for_update().filter(
        student=member.student,
        clan=clan,
        status=Status.ACCEPTED,
        role__in=Roles.ALL_LEADERSHIP
    ).exclude(
        scout_member_id=member.scout_member_id
    ).exists()

    if has_other_leadership:
        raise ScoutValidationError(
            "هذا العضو لديه دور قيادي بالفعل"
        )


def change_member_role(member, new_role, clan):
    with transaction.atomic():
        locked_member = ScoutMembers.objects.select_for_update().get(
            scout_member_id=member.scout_member_id
        )

        locked_member.student = member.student
        locked_member.group = member.group

        if locked_member.status != Status.ACCEPTED:
            raise ScoutValidationError(
                f"العضو لم يعد مقبولاً — الحالة الحالية: {locked_member.status}"
            )
        _validate_role_change_locked(locked_member, new_role, clan)

        locked_member.role = new_role
        locked_member.updated_at = timezone.now()
        locked_member.save()

        member.role = new_role


def remove_member(member):
    info = {
        'name': member.student.name,
        'role': member.role,
        'student_id': member.student_id,
    }
    with transaction.atomic():
        locked = ScoutMembers.objects.select_for_update().get(
            scout_member_id=member.scout_member_id
        )
        locked.delete()
    return info
# ============================================
# University Scout Programs
# ============================================

def get_all_university_programs():

    return UniversityScoutPrograms.objects.all().order_by(
        'name'
    )


def create_university_program(data, admin_id):

    name = data.get('name')

    if not name:
        raise ScoutValidationError(
            "يجب تحديد اسم البرنامج"
        )

    exists = UniversityScoutPrograms.objects.filter(
        name=name
    ).exists()

    if exists:
        raise ScoutValidationError(
            "هذا البرنامج موجود بالفعل"
        )

    return UniversityScoutPrograms.objects.create(
        name=name,
        description=data.get('description'),
        created_by_id=admin_id,
        created_at=timezone.now(),
    )


# ============================================
# University Team Members
# ============================================

def get_university_team_members(query_params):

    members = UniversityScoutMembers.objects.select_related(
        'scout_member__student',
        'scout_member__clan__faculty',
    ).prefetch_related(
        'program_memberships__program'
    )

    role = query_params.get('role')

    if role:
        members = members.filter(
            university_role=role
        )

    faculty_id = query_params.get('faculty_id')

    if faculty_id:
        members = members.filter(
            scout_member__clan__faculty_id=faculty_id
        )

    program_id = query_params.get('program_id')

    if program_id:
        members = members.filter(
            program_memberships__program_id=program_id
        )

    return members.order_by('-created_at').distinct()


def add_to_university_scouts(
    scout_member_id,
    admin_id
):

    with transaction.atomic():

        member = ScoutMembers.objects.select_for_update().filter(
            scout_member_id=scout_member_id,
            status=Status.ACCEPTED
        ).first()

        if not member:
            raise ScoutValidationError(
                "العضو غير موجود أو غير مقبول"
            )

        exists = UniversityScoutMembers.objects.filter(
            scout_member=member
        ).exists()

        if exists:
            raise ScoutValidationError(
                "العضو موجود بالفعل في منتخب الجامعة"
            )

        return UniversityScoutMembers.objects.create(
            scout_member=member,
            university_role=None,
            selected_by_id=admin_id,
            created_at=timezone.now(),
        )


def assign_university_role(
    university_member_id,
    university_role
):

    with transaction.atomic():

        if not university_role:
            raise ScoutValidationError(
                "يجب تحديد الدور الجامعي"
            )

        if university_role not in UniversityRoles.ALL:
            raise ScoutValidationError(
                "الدور الجامعي غير صحيح"
            )

        membership = (
            UniversityScoutMembers.objects
            .select_for_update()
            .filter(
                university_member_id=university_member_id
            )
            .first()
        )

        if not membership:
            raise ScoutValidationError(
                "عضو المنتخب غير موجود"
            )

        role_exists = UniversityScoutMembers.objects.filter(
            university_role=university_role
        ).exclude(
            university_member_id=membership.university_member_id
        ).exists()

        if role_exists:
            raise ScoutValidationError(
                "هذا المنصب الجامعي مشغول بالفعل"
            )

        membership.university_role = university_role
        membership.updated_at = timezone.now()
        membership.save()

        return membership


def assign_member_to_program(
    university_member_id,
    program_id
):

    with transaction.atomic():

        membership = (
            UniversityScoutMembers.objects
            .select_for_update()
            .filter(
                university_member_id=university_member_id
            )
            .first()
        )

        if not membership:
            raise ScoutValidationError(
                "عضو المنتخب غير موجود"
            )

        program = UniversityScoutPrograms.objects.filter(
            program_id=program_id,
            is_active=True
        ).first()

        if not program:
            raise ScoutValidationError(
                "البرنامج غير موجود أو غير نشط"
            )

        exists = (
            UniversityScoutProgramMembers.objects.filter(
                university_member=membership,
                program=program
            ).exists()
        )

        if exists:
            raise ScoutValidationError(
                "العضو موجود بالفعل في هذا البرنامج"
            )

        return UniversityScoutProgramMembers.objects.create(
            university_member=membership,
            program=program,
            created_at=timezone.now(),
        )


def remove_university_team_member(university_member_id):

    member = UniversityScoutMembers.objects.filter(
        university_member_id=university_member_id
    ).first()

    if not member:
        raise ScoutValidationError(
            "عضو المنتخب غير موجود"
        )

    member.delete()