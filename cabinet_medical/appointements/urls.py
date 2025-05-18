from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.book_appointment, name='book_appointment'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('complete/<int:appointment_id>/', views.complete_appointment, name='complete_appointment'),
    path('patient/', views.patient_appointments, name='patient_appointments'),
    path('doctor/', views.doctor_appointments, name='doctor_appointments'),
    path('secretaire/', views.secretaire_appointments, name='secretaire_appointments'),
    path('doctor/calendar/', views.doctor_calendar, name='doctor_calendar'),
]
