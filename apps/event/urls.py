from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.event.events.views import EventManagementViewSet , EventARViewSet, EventActivationViewSet, EventGetterViewSet

router = DefaultRouter()

router.register(r'manage-events', EventManagementViewSet, basename='faculty_events')
router.register(r'approve-events', EventARViewSet, basename='admin_events')
router.register(r'get-events', EventGetterViewSet, basename='event_getter') 
router.register(r'activate-events', EventActivationViewSet, basename='event_activation')

urlpatterns = [
    path('event/', include(router.urls)),
]
urlpatterns = [
    path('event/', include(router.urls)),
]