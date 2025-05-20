from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MedicalRecord, Consultation, MedicalTest, DoctorRating
from utilisateurs.models import Patient, Doctor, Utilisateurs
from django.utils import timezone
import logging
from appointements.models import Appointement
from datetime import datetime
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.db import models
from django.db.models import Avg
from .forms import DoctorRatingForm
from utilisateurs.views import custom_login_required

# Set up logging
logger = logging.getLogger(__name__)

# Create your views here.

@login_required
def create_medical_record(request):
    try:
        # Get user from session
        if 'user_id' not in request.session or request.session['role'] != 'patient':
            logger.error(f"Access denied: User not logged in or not a patient")
            messages.error(request, 'Please sign in as a patient')
            return redirect('patientDashboard')
        
        # Get the patient instance
        user = Utilisateurs.objects.get(id=request.session['user_id'])
        patient = Patient.objects.get(utilisateur=user)
        
        # Check if patient already has a medical record
        if MedicalRecord.objects.filter(patient=patient).exists():
            logger.error(f"Patient {patient.utilisateur.username} already has a medical record")
            messages.error(request, 'You already have a medical record.')
            return redirect('patientDashboard')
        
        if request.method == 'POST':
            medical_record = MedicalRecord.objects.create(
                patient=patient,
                blood_type=request.POST.get('blood_type'),
                height=request.POST.get('height'),
                weight=request.POST.get('weight'),
                allergies=request.POST.get('allergies'),
                chronic_diseases=request.POST.get('chronic_diseases'),
                family_history=request.POST.get('family_history')
            )
            logger.info(f"Medical record created successfully for patient {patient.utilisateur.username}")
            messages.success(request, 'Medical record created successfully.')
            return redirect('view_medical_record', record_id=medical_record.id)
        
        context = {
            'blood_types': MedicalRecord.BloodType.choices
        }
        return render(request, 'create_medical_record.html', context)
    
    except Exception as e:
        logger.error(f"Error creating medical record: {str(e)}")
        messages.error(request, f'Error creating medical record: {str(e)}')
        return redirect('patientDashboard')

@custom_login_required
def view_medical_record(request, record_id):
    try:
        medical_record = get_object_or_404(MedicalRecord, id=record_id)
        
        # Check if user has permission to view this record
        if 'user_id' not in request.session:
            logger.error("User not logged in")
            messages.error(request, 'Please sign in to view medical records.')
            return redirect('signin')
            
        user = Utilisateurs.objects.get(id=request.session['user_id'])
        
        if request.session['role'] == 'patient':
            patient = Patient.objects.get(utilisateur=user)
            if medical_record.patient != patient:
                logger.error(f"Patient {user.username} tried to access another patient's record")
                messages.error(request, 'You do not have permission to view this record.')
                return redirect('patientDashboard')
        elif request.session['role'] == 'doctor':
            doctor = Doctor.objects.get(utilisateur=user)
            # Check if doctor has any appointments with this patient
            has_appointment = Appointement.objects.filter(
                doctor=doctor,
                patient=medical_record.patient
            ).exists()
            
            if not has_appointment:
                logger.error(f"Doctor {user.username} tried to access a patient's record without appointment")
                messages.error(request, 'You do not have permission to view this record.')
                return redirect('doctorDashboard')
        else:
            logger.error(f"Unauthorized user {user.username} tried to access medical record")
            messages.error(request, 'Access denied.')
            return redirect('signin')
        
        consultations = medical_record.consultations.all().order_by('-date')
        tests = medical_record.tests.all().order_by('-test_date')
        
        context = {
            'medical_record': medical_record,
            'consultations': consultations,
            'tests': tests,
            'is_doctor': request.session['role'] == 'doctor'
        }
        return render(request, 'view_medical_record.html', context)
        
    except Exception as e:
        logger.error(f"Error viewing medical record: {str(e)}")
        messages.error(request, f'Error viewing medical record: {str(e)}')
        return redirect('signin')

@login_required
def add_consultation(request, record_id):
    try:
        if 'user_id' not in request.session or request.session['role'] != 'doctor':
            logger.error("Access denied: User not logged in or not a doctor")
            messages.error(request, 'Only doctors can add consultations.')
            return redirect('signin')
        
        medical_record = get_object_or_404(MedicalRecord, id=record_id)
        user = Utilisateurs.objects.get(id=request.session['user_id'])
        doctor = Doctor.objects.get(utilisateur=user)
        
        if request.method == 'POST':
            # Convert follow_up_date string to datetime if provided
            follow_up_date = None
            if request.POST.get('follow_up_date'):
                follow_up_date = timezone.make_aware(
                    datetime.strptime(request.POST.get('follow_up_date'), '%Y-%m-%dT%H:%M')
                )
            
            consultation = Consultation.objects.create(
                medical_record=medical_record,
                doctor=doctor,
                symptoms=request.POST.get('symptoms'),
                diagnosis=request.POST.get('diagnosis'),
                prescription=request.POST.get('prescription'),
                notes=request.POST.get('notes'),
                follow_up_date=follow_up_date
            )
            logger.info(f"Consultation added successfully for patient {medical_record.patient.utilisateur.username}")
            messages.success(request, 'Consultation added successfully.')
            return redirect('view_medical_record', record_id=record_id)
        
        return render(request, 'add_consultation.html', {'medical_record': medical_record})
        
    except Exception as e:
        logger.error(f"Error adding consultation: {str(e)}")
        messages.error(request, f'Error adding consultation: {str(e)}')
        return redirect('doctorDashboard')

@login_required
def add_medical_test(request, record_id):
    try:
        if 'user_id' not in request.session or request.session['role'] != 'doctor':
            logger.error("Access denied: User not logged in or not a doctor")
            messages.error(request, 'Only doctors can add medical tests.')
            return redirect('signin')
        
        medical_record = get_object_or_404(MedicalRecord, id=record_id)
        user = Utilisateurs.objects.get(id=request.session['user_id'])
        doctor = Doctor.objects.get(utilisateur=user)
        
        if request.method == 'POST':
            test = MedicalTest.objects.create(
                medical_record=medical_record,
                doctor=doctor,
                test_type=request.POST.get('test_type'),
                test_results=request.POST.get('test_results'),
                notes=request.POST.get('notes')
            )
            
            if 'test_file' in request.FILES:
                test.test_file = request.FILES['test_file']
                test.save()
            
            logger.info(f"Medical test added successfully for patient {medical_record.patient.utilisateur.username}")
            messages.success(request, 'Medical test added successfully.')
            return redirect('view_medical_record', record_id=record_id)
        
        context = {
            'medical_record': medical_record,
            'test_types': MedicalTest.TestType.choices
        }
        return render(request, 'add_medical_test.html', context)
        
    except Exception as e:
        logger.error(f"Error adding medical test: {str(e)}")
        messages.error(request, f'Error adding medical test: {str(e)}')
        return redirect('doctorDashboard')

@login_required
def patient_medical_records(request):
    if not hasattr(request.user, 'patient'):
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    patient = get_object_or_404(Patient, utilisateur=request.user)
    medical_record = MedicalRecord.objects.filter(patient=patient).first()
    
    if not medical_record:
        return redirect('create_medical_record')
    
    return redirect('view_medical_record', record_id=medical_record.id)

@custom_login_required
def doctor_patient_records(request):
    try:
        # Get user from session
        if request.session['role'] != 'doctor':
            logger.error(f"Access denied: User not logged in or not a doctor")
            messages.error(request, 'Please sign in as a doctor')
            return redirect('signin')
        
        # Get the doctor instance
        user = Utilisateurs.objects.get(id=request.session['user_id'])
        doctor = Doctor.objects.get(utilisateur=user)
        
        logger.info(f"Fetching appointments for doctor: {doctor.utilisateur.username}")
        
        # Get all appointments for this doctor
        appointments = Appointement.objects.filter(
            doctor=doctor,
            status__in=['upcoming', 'completed']  # Only show active and completed appointments
        ).select_related(
            'patient',
            'patient__utilisateur'
        ).order_by('-date')
        
        logger.info(f"Found {appointments.count()} total appointments")
        
        # Create a list of patients with their medical records
        patients_data = []
        seen_patients = set()
        
        for appointment in appointments:
            logger.info(f"Processing appointment: {appointment.id} - Status: {appointment.status}")
            patient = appointment.patient
            if patient.id not in seen_patients:
                seen_patients.add(patient.id)
                # Get the patient's medical record
                medical_record = MedicalRecord.objects.filter(patient=patient).first()
                logger.info(f"Patient {patient.utilisateur.username} - Has medical record: {medical_record is not None}")
                
                # Get the next upcoming appointment for this patient
                next_appointment = Appointement.objects.filter(
                    doctor=doctor,
                    patient=patient,
                    status='upcoming',
                    date__gte=timezone.now()
                ).order_by('date').first()
                
                patients_data.append({
                    'patient': patient,
                    'medical_record': medical_record,
                    'next_appointment': next_appointment.date if next_appointment else None
                })
        
        logger.info(f"Processed {len(patients_data)} unique patients")
        
        context = {
            'patients_data': patients_data
        }
        return render(request, 'doctor_patient_records.html', context)
        
    except Exception as e:
        logger.error(f"Error in doctor_patient_records: {str(e)}")
        messages.error(request, f'Error loading patient records: {str(e)}')
        return redirect('doctorDashboard')

def export_medical_record_pdf(request, record_id):
    try:
        logger.info(f"Starting PDF export for record {record_id}")
        medical_record = get_object_or_404(MedicalRecord, id=record_id)
        logger.info(f"Found medical record for patient {medical_record.patient.utilisateur.username}")
        
        # Check if user has permission to export this record
        if 'user_id' not in request.session:
            logger.error("User not logged in for PDF export")
            messages.error(request, 'Please sign in to export medical records.')
            return redirect('signin')
        
        user = Utilisateurs.objects.get(id=request.session['user_id'])
        logger.info(f"User {user.username} attempting to export record")
        has_permission = False
        
        if request.session['role'] == 'patient':
            patient = Patient.objects.get(utilisateur=user)
            if medical_record.patient == patient:
                has_permission = True
                logger.info("Patient has permission to export their own record")
        elif request.session['role'] == 'doctor':
            doctor = Doctor.objects.get(utilisateur=user)
            # Check if doctor has any appointments with this patient
            has_appointment = Appointement.objects.filter(
                doctor=doctor,
                patient=medical_record.patient
            ).exists()
            if has_appointment:
                has_permission = True
                logger.info("Doctor has permission to export record due to existing appointment")
        
        if not has_permission:
            logger.error(f"Unauthorized user {user.username} tried to export medical record ID {record_id}")
            messages.error(request, 'You do not have permission to export this record.')
            if request.session['role'] == 'patient':
                return redirect('patientDashboard')
            elif request.session['role'] == 'doctor':
                return redirect('doctorDashboard')
            else:
                return redirect('signin')
        
        consultations = medical_record.consultations.all().order_by('-date')
        tests = medical_record.tests.all().order_by('-test_date')
        logger.info(f"Found {consultations.count()} consultations and {tests.count()} tests")
        
        context = {
            'medical_record': medical_record,
            'consultations': consultations,
            'tests': tests,
            'request': request,
        }
        
        try:
            template = get_template('medical_record_pdf.html')
            logger.info("Template loaded successfully")
            html = template.render(context)
            logger.info("Template rendered successfully")
        except Exception as template_error:
            logger.error(f"Template error: {str(template_error)}")
            messages.error(request, f'Error loading template: {str(template_error)}')
            return redirect('view_medical_record', record_id=record_id)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="medical_record_{medical_record.patient.utilisateur.username}.pdf"'
        
        logger.info("Starting PDF generation")
        try:
            p = pisa.CreatePDF(html, dest=response)
            if p.err:
                logger.error(f"Error generating PDF: {p.err}")
                messages.error(request, 'Error generating PDF.')
                return redirect('view_medical_record', record_id=record_id)
        except Exception as pdf_error:
            logger.error(f"PDF generation error: {str(pdf_error)}")
            messages.error(request, f'Error generating PDF: {str(pdf_error)}')
            return redirect('view_medical_record', record_id=record_id)
        
        logger.info(f"PDF generated successfully for record {record_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in export_medical_record_pdf: {str(e)}")
        messages.error(request, f'Error exporting medical record: {str(e)}')
        # Redirect based on user role if possible, otherwise to signin
        if 'role' in request.session:
            if request.session['role'] == 'patient':
                return redirect('patientDashboard')
            elif request.session['role'] == 'doctor':
                return redirect('doctorDashboard')
        return redirect('signin')

@login_required
def rate_doctor(request, doctor_id):
    """View for patients to rate a doctor."""
    try:
        if request.session['role'] != 'patient':
            messages.error(request, 'Access denied')
            return redirect('signin')
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        # Get the patient's medical record
        medical_record = MedicalRecord.objects.filter(patient=patient).first()
        
        # Check if patient has already rated this doctor
        existing_rating = DoctorRating.objects.filter(patient=patient, doctor=doctor).first()
        
        if request.method == 'POST':
            form = DoctorRatingForm(request.POST)
            if form.is_valid():
                if existing_rating:
                    # Update existing rating
                    existing_rating.rating = form.cleaned_data['rating']
                    existing_rating.comment = form.cleaned_data['comment']
                    existing_rating.save()
                    messages.success(request, 'Your rating has been updated')
                else:
                    # Create new rating
                    rating = form.save(commit=False)
                    rating.patient = patient
                    rating.doctor = doctor
                    rating.save()
                    messages.success(request, 'Thank you for rating the doctor')
                
                # Calculate and update doctor's average rating
                average_rating = DoctorRating.objects.filter(doctor=doctor).aggregate(Avg('rating'))['rating__avg']
                if average_rating is not None:
                    doctor.rating = round(average_rating)
                    doctor.save()
                    logger.info(f"Updated doctor {doctor.utilisateur.username}'s rating to {doctor.rating}")
                
                # Redirect to medical record if it exists, otherwise to dashboard
                if medical_record:
                    return redirect('view_medical_record', record_id=medical_record.id)
                return redirect('patientDashboard')
        else:
            if existing_rating:
                form = DoctorRatingForm(instance=existing_rating)
            else:
                form = DoctorRatingForm()
        
        context = {
            'form': form,
            'doctor': doctor,
            'existing_rating': existing_rating,
            'medical_record': medical_record
        }
        return render(request, 'rate_doctor.html', context)
        
    except Exception as e:
        logger.error(f"Error in rate_doctor: {str(e)}")
        messages.error(request, 'Error submitting rating')
        return redirect('patientDashboard')

@login_required
def view_doctor_ratings(request, doctor_id):
    try:
        doctor = get_object_or_404(Doctor, id=doctor_id)
        ratings = DoctorRating.objects.filter(doctor=doctor).order_by('-created_at')
        
        # Calculate average rating
        average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Get the current user's role and ID
        user_role = request.session.get('role')
        user_id = request.session.get('user_id')
        
        # Check if the current user has rated this doctor
        user_rating = None
        if user_role == 'patient':
            try:
                patient = Patient.objects.get(utilisateur_id=user_id)
                user_rating = DoctorRating.objects.filter(patient=patient, doctor=doctor).first()
            except Patient.DoesNotExist:
                pass
        
        context = {
            'doctor': doctor,
            'ratings': ratings,
            'average_rating': average_rating,
            'user_rating': user_rating,
            'is_patient': user_role == 'patient'
        }
        return render(request, 'view_doctor_ratings.html', context)
        
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor not found.')
        if request.session['role'] == 'patient':
            return redirect('patientDashboard')
        elif request.session['role'] == 'doctor':
            return redirect('doctorDashboard')
        return redirect('signin')
    except Exception as e:
        logger.error(f"Error in view_doctor_ratings: {str(e)}")
        messages.error(request, 'An error occurred while loading the ratings.')
        if request.session['role'] == 'patient':
            return redirect('patientDashboard')
        elif request.session['role'] == 'doctor':
            return redirect('doctorDashboard')
        return redirect('signin')
