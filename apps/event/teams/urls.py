from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.event.teams.views import AdminTeamViewSet, StudentTeamViewSet

router = DefaultRouter()
router.register(r'student-teams', StudentTeamViewSet, basename='student_teams')
router.register(r'manage-teams', AdminTeamViewSet, basename='manage_teams')

urlpatterns = [
    path('', include(router.urls)),
]