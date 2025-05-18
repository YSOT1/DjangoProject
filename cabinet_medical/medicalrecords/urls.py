from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_medical_record, name='create_medical_record'),
    path('view/<int:record_id>/', views.view_medical_record, name='view_medical_record'),
    path('add-consultation/<int:record_id>/', views.add_consultation, name='add_consultation'),
    path('add-test/<int:record_id>/', views.add_medical_test, name='add_medical_test'),
    path('patient-records/', views.patient_medical_records, name='patient_medical_records'),
    path('doctor-records/', views.doctor_patient_records, name='doctor_patient_records'),
    path('export-pdf/<int:record_id>/', views.export_medical_record_pdf, name='export_medical_record_pdf'),
    path('doctor/<int:doctor_id>/rate/', views.rate_doctor, name='rate_doctor'),
    path('doctor/<int:doctor_id>/ratings/', views.view_doctor_ratings, name='view_doctor_ratings'),
]
