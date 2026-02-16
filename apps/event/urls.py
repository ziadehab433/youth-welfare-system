from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.event.events.views import EventManagementViewSet , EventARViewSet, EventActivationViewSet

router = DefaultRouter()

router.register(r'events', EventManagementViewSet, basename='faculty_events')
router.register(r'events', EventARViewSet, basename='admin_events')
router.register(r'events', EventActivationViewSet, basename='event_activation')
urlpatterns = [
    path('event/', include(router.urls)),
]