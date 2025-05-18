from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("signin", views.signin, name="signin"),
    path("signup", views.signup, name="signup"),
    path("patientDashboard", views.patientDashboard, name="patientDashboard"),
    path("doctorDashboard", views.doctorDashboard, name="doctorDashboard"),
    path("secretaireDashboard", views.secretaireDashboard, name="secretaireDashboard"),
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("manage-patients/", views.manage_patients, name="manage_patients"),
    path("view-schedules/", views.view_schedules, name="view_schedules"),
    path("edit-profile/", views.edit_doctor_profile, name="edit_doctor_profile"),
]