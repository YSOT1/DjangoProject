from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Insurance, PatientInsurance, ReimbursementFolder, ReimbursementDocument
from utilisateurs.models import Patient
from django.utils import timezone
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

@login_required
def patient_insurance_list(request):
    """View for patients to see their insurance policies."""
    try:
        if request.session['role'] != 'patient':
            messages.error(request, 'Access denied')
            return redirect('signin')
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        insurance_policies = PatientInsurance.objects.filter(patient=patient).select_related('insurance')
        
        context = {
            'insurance_policies': insurance_policies,
            'active_policies': insurance_policies.filter(is_active=True),
            'expired_policies': insurance_policies.filter(is_active=False)
        }
        return render(request, 'insurance/patient_insurance_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in patient_insurance_list: {str(e)}")
        messages.error(request, 'Error loading insurance policies')
        return redirect('patientDashboard')

@login_required
def add_insurance_policy(request):
    """View for patients to add a new insurance policy."""
    try:
        if request.session['role'] != 'patient':
            messages.error(request, 'Access denied')
            return redirect('signin')
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        
        if request.method == 'POST':
            insurance_id = request.POST.get('insurance')
            policy_number = request.POST.get('policy_number')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date') or None
            requires_authorization = request.POST.get('requires_authorization') == 'on'
            
            insurance = get_object_or_404(Insurance, id=insurance_id)
            
            # Check if policy already exists
            if PatientInsurance.objects.filter(
                patient=patient,
                insurance=insurance,
                policy_number=policy_number
            ).exists():
                messages.error(request, 'This policy number already exists for this insurance')
                return redirect('add_insurance_policy')
            
            # Create new policy
            PatientInsurance.objects.create(
                patient=patient,
                insurance=insurance,
                policy_number=policy_number,
                start_date=start_date,
                end_date=end_date,
                requires_authorization=requires_authorization
            )
            
            messages.success(request, 'Insurance policy added successfully')
            return redirect('patient_insurance_list')
        
        # GET request - show form
        insurances = Insurance.objects.all()
        context = {
            'insurances': insurances
        }
        return render(request, 'insurance/add_insurance_policy.html', context)
        
    except Exception as e:
        logger.error(f"Error in add_insurance_policy: {str(e)}")
        messages.error(request, 'Error adding insurance policy')
        return redirect('patient_insurance_list')

@login_required
def patient_list(request):
    """View for secretaries to see the list of patients."""
    try:
        # Check if user is logged in and is a secretary
        if 'user_id' not in request.session or request.session['role'] != 'secretaire':
            logger.error("Access denied: User not logged in or not a secretary")
            messages.error(request, 'Please sign in as a secretary')
            return redirect('signin')
        
        # Get all patients with their related user data and insurance policies
        patients = Patient.objects.select_related('utilisateur').prefetch_related('insurance_policies').all()
        
        # Log the number of patients found
        logger.info(f"Found {patients.count()} patients")
        
        context = {
            'patients': patients,
            'title': 'Patient List'
        }
        return render(request, 'insurance/patient_list.html', context)
        
    except Exception as e:
        logger.error(f"Error fetching patients list: {str(e)}", exc_info=True)
        messages.error(request, 'Error loading patients list. Please try again.')
        return redirect('secretaireDashboard')

@login_required
def manage_patient_insurance(request, patient_id):
    """View for secretaries to manage patient insurance policies."""
    try:
        # Check if user is logged in and is a secretary
        if 'user_id' not in request.session or request.session['role'] != 'secretaire':
            logger.error("Access denied: User not logged in or not a secretary")
            messages.error(request, 'Please sign in as a secretary')
            return redirect('signin')
        
        # Get patient and their insurance policies
        try:
            patient = get_object_or_404(Patient, id=patient_id)
            insurance_policies = PatientInsurance.objects.filter(patient=patient).select_related('insurance')
            
            # Log successful patient retrieval
            logger.info(f"Retrieved patient {patient.utilisateur.username} with {insurance_policies.count()} insurance policies")
            
        except Patient.DoesNotExist:
            logger.error(f"Patient with ID {patient_id} not found")
            messages.error(request, 'Patient not found')
            return redirect('insurance_patient_list')
        except Exception as e:
            logger.error(f"Error fetching patient or insurance policies: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading patient information')
            return redirect('insurance_patient_list')
        
        # Handle POST requests
        if request.method == 'POST':
            try:
                action = request.POST.get('action')
                policy_id = request.POST.get('policy_id')
                
                if action == 'toggle_active':
                    policy = get_object_or_404(PatientInsurance, id=policy_id)
                    policy.is_active = not policy.is_active
                    policy.save()
                    messages.success(request, f'Policy status updated to {"active" if policy.is_active else "inactive"}')
                
                elif action == 'delete':
                    policy = get_object_or_404(PatientInsurance, id=policy_id)
                    policy.delete()
                    messages.success(request, 'Policy deleted successfully')
                
                elif action == 'add_policy':
                    insurance_id = request.POST.get('insurance')
                    policy_number = request.POST.get('policy_number')
                    start_date = request.POST.get('start_date')
                    end_date = request.POST.get('end_date') or None
                    requires_authorization = request.POST.get('requires_authorization') == 'on'
                    
                    if not all([insurance_id, policy_number, start_date]):
                        messages.error(request, 'Please fill in all required fields')
                        return redirect('manage_patient_insurance', patient_id=patient_id)
                    
                    insurance = get_object_or_404(Insurance, id=insurance_id)
                    
                    # Check if policy already exists
                    if PatientInsurance.objects.filter(
                        patient=patient,
                        insurance=insurance,
                        policy_number=policy_number
                    ).exists():
                        messages.error(request, 'This policy number already exists for this insurance')
                    else:
                        # Create new policy
                        PatientInsurance.objects.create(
                            patient=patient,
                            insurance=insurance,
                            policy_number=policy_number,
                            start_date=start_date,
                            end_date=end_date,
                            requires_authorization=requires_authorization
                        )
                        messages.success(request, 'Insurance policy added successfully')
            except Exception as e:
                logger.error(f"Error processing POST request: {str(e)}", exc_info=True)
                messages.error(request, 'Error processing your request')
                return redirect('manage_patient_insurance', patient_id=patient_id)
        
        # Prepare context for rendering
        try:
            context = {
                'patient': patient,
                'insurance_policies': insurance_policies,
                'insurances': Insurance.objects.all(),
                'title': f'Manage Insurance - {patient.utilisateur.username}'
            }
            return render(request, 'insurance/manage_patient_insurance.html', context)
        except Exception as e:
            logger.error(f"Error preparing context: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading page')
            return redirect('insurance_patient_list')
        
    except Exception as e:
        logger.error(f"Unexpected error in manage_patient_insurance: {str(e)}", exc_info=True)
        messages.error(request, 'An unexpected error occurred')
        return redirect('secretaireDashboard')

@login_required
def reimbursement_folders(request):
    """View for patients to see their reimbursement folders."""
    try:
        if request.session['role'] != 'patient':
            messages.error(request, 'Access denied')
            return redirect('signin')
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        folders = ReimbursementFolder.objects.filter(patient=patient).select_related('insurance_policy__insurance')
        
        context = {
            'folders': folders,
            'active_policies': PatientInsurance.objects.filter(patient=patient, is_active=True)
        }
        return render(request, 'reimbursement_folders.html', context)
        
    except Exception as e:
        logger.error(f"Error in reimbursement_folders: {str(e)}")
        messages.error(request, 'Error loading reimbursement folders')
        return redirect('patientDashboard')

@login_required
def create_reimbursement_folder(request):
    """View for patients to create a new reimbursement folder."""
    try:
        if request.session['role'] != 'patient':
            messages.error(request, 'Access denied')
            return redirect('signin')
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        logger.info(f"Creating reimbursement folder for patient: {patient.utilisateur.username}")
        
        if request.method == 'POST':
            insurance_policy_id = request.POST.get('insurance_policy')
            title = request.POST.get('title')
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            
            if not all([insurance_policy_id, title, description, amount]):
                messages.error(request, 'Please fill in all required fields')
                return redirect('create_reimbursement_folder')
            
            insurance_policy = get_object_or_404(PatientInsurance, id=insurance_policy_id, patient=patient)
            
            folder = ReimbursementFolder.objects.create(
                patient=patient,
                insurance_policy=insurance_policy,
                title=title,
                description=description,
                amount=amount
            )
            
            # Handle document uploads
            files = request.FILES.getlist('documents')
            for file in files:
                ReimbursementDocument.objects.create(
                    folder=folder,
                    title=file.name,
                    file=file
                )
            
            messages.success(request, 'Reimbursement folder created successfully')
            return redirect('reimbursement_folders')
        
        # GET request - show form
        active_policies = PatientInsurance.objects.filter(patient=patient, is_active=True)
        logger.info(f"Found {active_policies.count()} active policies for patient {patient.utilisateur.username}")
        for policy in active_policies:
            logger.info(f"Policy: {policy.insurance.name} - {policy.policy_number}")
        
        context = {
            'active_policies': active_policies
        }
        return render(request, 'create_reimbursement_folder.html', context)
        
    except Exception as e:
        logger.error(f"Error in create_reimbursement_folder: {str(e)}")
        messages.error(request, 'Error creating reimbursement folder')
        return redirect('reimbursement_folders')

@login_required
def view_reimbursement_folder(request, folder_id):
    """View for patients to view a specific reimbursement folder."""
    try:
        if request.session['role'] != 'patient':
            messages.error(request, 'Access denied')
            return redirect('signin')
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        folder = get_object_or_404(ReimbursementFolder, id=folder_id, patient=patient)
        
        context = {
            'folder': folder,
            'documents': folder.documents.all()
        }
        return render(request, 'view_reimbursement_folder.html', context)
        
    except Exception as e:
        logger.error(f"Error in view_reimbursement_folder: {str(e)}")
        messages.error(request, 'Error loading reimbursement folder')
        return redirect('reimbursement_folders')

@login_required
def submit_reimbursement_folder(request, folder_id):
    """View for patients to submit a reimbursement folder."""
    try:
        if request.session['role'] != 'patient':
            messages.error(request, 'Access denied')
            return redirect('signin')
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        folder = get_object_or_404(ReimbursementFolder, id=folder_id, patient=patient)
        
        if folder.status != 'draft':
            messages.error(request, 'Only draft folders can be submitted')
            return redirect('view_reimbursement_folder', folder_id=folder_id)
        
        if folder.submit():
            messages.success(request, 'Reimbursement folder submitted successfully')
        else:
            messages.error(request, 'Error submitting reimbursement folder')
        
        return redirect('view_reimbursement_folder', folder_id=folder_id)
        
    except Exception as e:
        logger.error(f"Error in submit_reimbursement_folder: {str(e)}")
        messages.error(request, 'Error submitting reimbursement folder')
        return redirect('reimbursement_folders')

@login_required
def add_document_to_folder(request, folder_id):
    """View for patients to add documents to a reimbursement folder."""
    try:
        if request.session['role'] != 'patient':
            messages.error(request, 'Access denied')
            return redirect('signin')
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        folder = get_object_or_404(ReimbursementFolder, id=folder_id, patient=patient)
        
        if folder.status != 'draft':
            messages.error(request, 'Documents can only be added to draft folders')
            return redirect('view_reimbursement_folder', folder_id=folder_id)
        
        if request.method == 'POST':
            title = request.POST.get('title')
            file = request.FILES.get('file')
            description = request.POST.get('description', '')
            
            if not all([title, file]):
                messages.error(request, 'Please provide a title and file')
                return redirect('view_reimbursement_folder', folder_id=folder_id)
            
            ReimbursementDocument.objects.create(
                folder=folder,
                title=title,
                file=file,
                description=description
            )
            
            messages.success(request, 'Document added successfully')
            return redirect('view_reimbursement_folder', folder_id=folder_id)
        
        return redirect('view_reimbursement_folder', folder_id=folder_id)
        
    except Exception as e:
        logger.error(f"Error in add_document_to_folder: {str(e)}")
        messages.error(request, 'Error adding document')
        return redirect('reimbursement_folders')

@login_required
def delete_document(request, document_id):
    """View for patients to delete a document from a reimbursement folder."""
    try:
        if request.session['role'] != 'patient':
            messages.error(request, 'Access denied')
            return redirect('signin')
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        document = get_object_or_404(ReimbursementDocument, id=document_id, folder__patient=patient)
        
        if document.folder.status != 'draft':
            messages.error(request, 'Documents can only be deleted from draft folders')
            return redirect('view_reimbursement_folder', folder_id=document.folder.id)
        
        folder_id = document.folder.id
        document.delete()
        messages.success(request, 'Document deleted successfully')
        
        return redirect('view_reimbursement_folder', folder_id=folder_id)
        
    except Exception as e:
        logger.error(f"Error in delete_document: {str(e)}")
        messages.error(request, 'Error deleting document')
        return redirect('reimbursement_folders')
