from django.urls import path
from . import views

urlpatterns = [
    path('faculty/plans/<int:plan_id>/export-pdf/', views.export_plan_pdf, name='plan_pdf'),
]