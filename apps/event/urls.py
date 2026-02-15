










from django.urls import path, include

urlpatterns = [
    path('events/', include('apps.event.plans.urls')),
]