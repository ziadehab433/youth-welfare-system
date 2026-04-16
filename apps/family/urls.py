from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.family.views.public import DepartmentViewSet, FacultyViewSet
from apps.family.views.faculty.families import FamilyFacultyAdminViewSet
from apps.family.views.faculty.events.approval import FacultyEventApprovalViewSet
from apps.family.views.faculty.events.participants import FacultyEventParticipantsViewSet
from apps.family.views.faculty.members import FamilyMembersViewSet
from apps.family.views.super_dept import SuperDeptFamilyViewSet
from apps.family.views.student import StudentFamilyViewSet

router = DefaultRouter()

router.register(r'faculty/families', FamilyFacultyAdminViewSet, basename='faculty_families')
router.register(r'faculty/events/approval', FacultyEventApprovalViewSet, basename='faculty_event_approval')
router.register(r'faculty/events/participants', FacultyEventParticipantsViewSet, basename='faculty_event_participants')
router.register(r'faculty/members', FamilyMembersViewSet, basename='faculty_members')


router.register(r'student', StudentFamilyViewSet, basename='student_family')
router.register(r'super_dept', SuperDeptFamilyViewSet, basename='super_dept_family')
router.register(r'departments', DepartmentViewSet, basename='departments')
router.register(r'faculties', FacultyViewSet, basename='faculties')
urlpatterns = [
    path('family/', include(router.urls)),
]