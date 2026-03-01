from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.event.events.participants_management_views import EventParticipantViewSet
from apps.event.events.event_management_views import (
    EventManagementViewSet,
    EventARViewSet,
    EventActivationViewSet,
    EventGetterViewSet
)
from apps.event.events.event_student_views import StudentEventViewSet
from apps.event.export.plan_report_pdf_view import export_plan_pdf
from apps.event.export.event_report_pdf_view import EventReportViewSet
router = DefaultRouter()
router.register(r'manage-events', EventManagementViewSet, basename='faculty_events')
router.register(r'approve-events', EventARViewSet, basename='admin_events')
router.register(r'get-events', EventGetterViewSet, basename='event_getter')
router.register(r'activate-events', EventActivationViewSet, basename='event_activation')
router.register(r'student-events', StudentEventViewSet, basename='student_events')
router.register(r'manage-participants', EventParticipantViewSet, basename='manage_participants')
router.register(r'reports', EventReportViewSet, basename='event_reports') 
urlpatterns = [
    path('events/', include('apps.event.plans.urls')),
    path('event/', include(router.urls)),
    path('event/export-plan-pdf/<int:plan_id>/', export_plan_pdf, name='export_plan_pdf'),
]