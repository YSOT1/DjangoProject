from django.urls import path
from . import views

urlpatterns = [
    path('my-insurance/', views.patient_insurance_list, name='patient_insurance_list'),
    path('add-insurance/', views.add_insurance_policy, name='add_insurance_policy'),
    path('patients/', views.patient_list, name='insurance_patient_list'),
    path('manage-insurance/<int:patient_id>/', views.manage_patient_insurance, name='manage_patient_insurance'),
    # Reimbursement folder URLs
    path('reimbursements/', views.reimbursement_folders, name='reimbursement_folders'),
    path('reimbursements/create/', views.create_reimbursement_folder, name='create_reimbursement_folder'),
    path('reimbursements/<int:folder_id>/', views.view_reimbursement_folder, name='view_reimbursement_folder'),
    path('reimbursements/<int:folder_id>/submit/', views.submit_reimbursement_folder, name='submit_reimbursement_folder'),
    path('reimbursements/<int:folder_id>/add-document/', views.add_document_to_folder, name='add_document_to_folder'),
    path('reimbursements/documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
]
