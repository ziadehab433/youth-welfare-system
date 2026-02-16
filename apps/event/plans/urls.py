from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlansViewSet

router = DefaultRouter()
router.register(r'plans', PlansViewSet, basename='plans')

urlpatterns = router.urls