from django.urls import path
from apps.solidarity.api.views import (
    StudentSolidarityViewSet,
    FacultyAdminSolidarityViewSet,
    SuperDeptSolidarityViewSet,
)

# Students
student_apply = StudentSolidarityViewSet.as_view({'post': 'apply'})
student_status = StudentSolidarityViewSet.as_view({'get': 'status'})

# Faculty Admin
faculty_list = FacultyAdminSolidarityViewSet.as_view({'get': 'list_applications'})
faculty_get = FacultyAdminSolidarityViewSet.as_view({'get': 'get_application'})
faculty_pre_approve = FacultyAdminSolidarityViewSet.as_view({'post': 'pre_approve'})

faculty_approve = FacultyAdminSolidarityViewSet.as_view({'post': 'approve'})
faculty_reject = FacultyAdminSolidarityViewSet.as_view({'post': 'reject'})

# Super Admin & Dept Admin
super_all = SuperDeptSolidarityViewSet.as_view({'get': 'all_applications'})
super_student_detail = SuperDeptSolidarityViewSet.as_view({'get': 'student_application_detail'})
super_approve = SuperDeptSolidarityViewSet.as_view({'post' :'change_to_approve'})
super_reject = SuperDeptSolidarityViewSet.as_view({'post' :'change_to_reject'})


urlpatterns = [
    # Students
    path('solidarity/apply/', student_apply),
    path('solidarity/status/', student_status),

    # Faculty Admin
    path('solidarity/applications/', faculty_list),
    path('solidarity/applications/<int:pk>/', faculty_get),
     path('solidarity/applications/<int:pk>/pre_approve/', faculty_pre_approve),
    path('solidarity/applications/<int:pk>/approve/', faculty_approve),
    path('solidarity/applications/<int:pk>/reject/', faculty_reject),

    # Super Admin & Dept Admin
    path('solidarity/all-applications/', super_all),
    path('solidarity/student/<int:pk>/', super_student_detail),
    path('solidarity/<int:pk>/change_to_approve',super_approve),
    path('solidarity/<int:pk>/change_to_reject',super_reject),
]
