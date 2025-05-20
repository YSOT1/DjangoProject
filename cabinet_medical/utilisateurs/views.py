from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import Utilisateurs, Doctor, Patient, Secretaire
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from medicalrecords.models import MedicalRecord
import logging
from functools import wraps
from django.utils import timezone
from appointements.models import Appointement
from django.db.models import Sum
from invoice.models import Invoice

# Set up logging
logger = logging.getLogger(__name__)

def custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.error(request, 'Please sign in to access this page')
            return redirect('signin')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = Utilisateurs.objects.get(username=username)
            if check_password(password, user.password):
                # Create new session
                request.session.create()
                
                # Store user info in session
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                request.session['role'] = user.role.lower()  # Store role in lowercase
                
                # Set session expiry
                request.session.set_expiry(86400)  # 24 hours
                
                # Save session immediately
                request.session.save()

                # Redirect based on role
                if user.role.lower() == 'doctor':
                    return redirect('doctorDashboard')
                elif user.role.lower() == 'patient':
                    return redirect('patientDashboard')
                elif user.role.lower() == 'secretaire':
                    return redirect('secretaireDashboard')
            else:
                messages.error(request, 'Invalid password')
        except Utilisateurs.DoesNotExist:
            messages.error(request, 'User not found')
        
        return render(request, 'signin.html')

    return render(request, 'signin.html')

def signup(request):
    if request.method == 'POST':
        try:
            # Get form data
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role').lower()  # Convert role to lowercase

            # Create base user
            user = Utilisateurs.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                role=role
            )

            # Create role-specific record
            if role == 'doctor':
                Doctor.objects.create(
                    utilisateur=user,
                    specialite=request.POST.get('specialite'),
                    immatriculation=request.POST.get('immatriculation'),
                    rating=0
                )
            elif role == 'patient':
                birth_date = request.POST.get('birth_date')
                if birth_date:
                    birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                
                Patient.objects.create(
                    utilisateur=user,
                    birth_date=birth_date,
                    address=request.POST.get('address'),
                    phone=request.POST.get('phone')
                )
            elif role == 'secretaire':
                Secretaire.objects.create(utilisateur=user)

            messages.success(request, 'Account created successfully!')
            return redirect('signin')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'signup.html')

    return render(request, 'signup.html')

@custom_login_required
def patientDashboard(request):
    try:
        if request.session['role'] != 'patient':
            logger.error(f"Access denied: User not logged in or not a patient")
            messages.error(request, 'Please sign in as a patient')
            return redirect('signin')
        
        # Get the patient instance
        user = Utilisateurs.objects.get(id=request.session['user_id'])
        patient = Patient.objects.get(utilisateur=user)
        
        # Get today's date
        today = timezone.now().date()
        
        # Get upcoming appointments count
        upcoming_appointments = Appointement.objects.filter(
            patient=patient,
            date__gte=today,
            status__in=['upcoming', 'pending_payment']
        ).count()
        
        # Get total visits
        total_visits = Appointement.objects.filter(
            patient=patient,
            status='completed'
        ).count()
        
        # Get total spent
        total_spent = Invoice.objects.filter(
            patient=patient,
            is_paid=True
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get last visit
        last_visit = Appointement.objects.filter(
            patient=patient,
            status='completed'
        ).order_by('-date').first()
        
        # Get recent appointments
        recent_appointments = Appointement.objects.filter(
            patient=patient
        ).select_related('doctor', 'doctor__utilisateur').order_by('-date')[:5]
        
        # Get medical record
        medical_record = MedicalRecord.objects.filter(patient=patient).first()
        
        # Get recent invoices
        recent_invoices = Invoice.objects.filter(
            patient=patient,
            is_paid=True
        ).select_related('doctor', 'doctor__utilisateur').order_by('-issued_date')[:5]
        
        context = {
            'today': today,
            'upcoming_appointments': upcoming_appointments,
            'total_visits': total_visits,
            'total_spent': total_spent,
            'last_visit': last_visit.date.strftime('%b %d, %Y') if last_visit else None,
            'recent_appointments': recent_appointments,
            'medical_record': medical_record,
            'recent_invoices': recent_invoices
        }
        
        return render(request, 'patientDashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in patient dashboard: {str(e)}")
        messages.error(request, f'Error accessing dashboard: {str(e)}')
        return redirect('signin')

def doctorDashboard(request):
    try:
        if 'user_id' not in request.session or request.session['role'] != 'doctor':
            messages.error(request, 'Please sign in as a doctor')
            return redirect('signin')
        
        # Get the doctor instance
        doctor = Doctor.objects.get(utilisateur_id=request.session['user_id'])
        
        # Get today's date
        today = timezone.now().date()
        
        # Get today's appointments count
        today_appointments = Appointement.objects.filter(
            doctor=doctor,
            date__date=today
        ).count()
        
        # Get total patients count
        total_patients = Appointement.objects.filter(
            doctor=doctor
        ).values('patient').distinct().count()
        
        # Get monthly earnings
        month_start = today.replace(day=1)
        monthly_earnings = Invoice.objects.filter(
            doctor=doctor,
            issued_date__gte=month_start,
            is_paid=True
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get recent appointments
        recent_appointments = Appointement.objects.filter(
            doctor=doctor
        ).select_related('patient', 'patient__utilisateur').order_by('-date')[:5]
        
        context = {
            'today': today,
            'today_appointments': today_appointments,
            'total_patients': total_patients,
            'monthly_earnings': monthly_earnings,
            'rating': doctor.rating,
            'recent_appointments': recent_appointments
        }
        
        return render(request, 'doctorDashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in doctor dashboard: {str(e)}")
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('signin')

def secretaireDashboard(request):
    """View for secretary dashboard."""
    try:
        if 'user_id' not in request.session or request.session['role'] != 'secretaire':
            logger.error("Access denied: User not logged in or not a secretary")
            messages.error(request, 'Please sign in as a secretary')
            return redirect('signin')
        
        today = timezone.now().date()
        
        # Get today's appointments
        today_appointments = Appointement.objects.filter(
            date__date=today
        ).count()
        
        # Get total patients
        total_patients = Patient.objects.count()
        
        # Get new patients (patients with appointments today)
        new_patients = Appointement.objects.filter(
            date__date=today
        ).values('patient').distinct().count()
        
        # Get pending appointments
        pending_appointments = Appointement.objects.filter(
            status='pending'
        ).count()
        
        # Get today's schedule
        today_schedule = Appointement.objects.filter(
            date__date=today
        ).select_related('doctor__utilisateur', 'patient__utilisateur').order_by('date')
        
        context = {
            'today': today,
            'today_appointments': today_appointments,
            'total_patients': total_patients,
            'new_patients': new_patients,
            'pending_appointments': pending_appointments,
            'today_schedule': today_schedule
        }
        
        return render(request, 'secretaireDashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in secretaireDashboard: {str(e)}")
        messages.error(request, 'Error loading dashboard')
        return redirect('signin')

def doctor_list(request):
    try:
        if 'user_id' not in request.session or request.session['role'] != 'patient':
            logger.error("Access denied: User not logged in or not a patient")
            messages.error(request, 'Please sign in as a patient')
            return redirect('signin')
        
        # Get all doctors
        doctors = Doctor.objects.all().select_related('utilisateur')
        
        # Get search parameters
        search_query = request.GET.get('search', '')
        speciality = request.GET.get('speciality', '')
        min_rating = request.GET.get('rating', '')
        
        # Apply filters
        if search_query:
            doctors = doctors.filter(utilisateur__username__icontains=search_query)
        
        if speciality:
            doctors = doctors.filter(specialite=speciality)
        
        if min_rating:
            doctors = doctors.filter(rating__gte=min_rating)
        
        # Get unique specialities for the filter dropdown
        specialities = Doctor.objects.values_list('specialite', flat=True).distinct()
        
        context = {
            'doctors': doctors,
            'specialities': specialities,
        }
        
        return render(request, 'doctor_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in doctor_list: {str(e)}")
        messages.error(request, f'Error loading doctors: {str(e)}')
        return redirect('patientDashboard')

def home(request):
    return render(request, 'home.html')

def manage_patients(request):
    try:
        if 'user_id' not in request.session or request.session['role'] != 'secretaire':
            logger.error("Access denied: User not logged in or not a secretary")
            messages.error(request, 'Please sign in as a secretary')
            return redirect('signin')
        
        # Get all patients
        patients = Patient.objects.all().select_related('utilisateur')
        
        # Get search parameters
        search_query = request.GET.get('search', '')
        
        # Apply filters
        if search_query:
            patients = patients.filter(utilisateur__username__icontains=search_query)
        
        context = {
            'patients': patients,
        }
        
        return render(request, 'manage_patients.html', context)
        
    except Exception as e:
        logger.error(f"Error in manage_patients: {str(e)}")
        messages.error(request, f'Error loading patients: {str(e)}')
        return redirect('secretaireDashboard')

def view_schedules(request):
    try:
        if 'user_id' not in request.session or request.session['role'] != 'secretaire':
            logger.error("Access denied: User not logged in or not a secretary")
            messages.error(request, 'Please sign in as a secretary')
            return redirect('signin')
        
        # Get all doctors
        doctors = Doctor.objects.all().select_related('utilisateur')
        
        # Get search parameters
        search_query = request.GET.get('search', '')
        speciality = request.GET.get('speciality', '')
        
        # Apply filters
        if search_query:
            doctors = doctors.filter(utilisateur__username__icontains=search_query)
        
        if speciality:
            doctors = doctors.filter(specialite=speciality)
        
        # Get unique specialities for the filter dropdown
        specialities = Doctor.objects.values_list('specialite', flat=True).distinct()

        # Get today's date
        today = timezone.now().date()
        
        # Get appointments for each doctor
        doctors_with_appointments = []
        for doctor in doctors:
            # Get today's appointments for this doctor
            appointments = Appointement.objects.filter(
                doctor=doctor,
                date__date=today
            ).select_related('patient', 'patient__utilisateur').order_by('date')
            
            # Create time slots for the day (9 AM to 5 PM)
            time_slots = []
            current_time = timezone.make_aware(datetime.combine(today, datetime.min.time().replace(hour=9)))
            end_time = timezone.make_aware(datetime.combine(today, datetime.min.time().replace(hour=17)))
            
            while current_time < end_time:
                # Check if there's an appointment at this time
                appointment = appointments.filter(date__hour=current_time.hour).first()
                
                time_slots.append({
                    'time': current_time,
                    'is_booked': appointment is not None,
                    'appointment': appointment
                })
                
                # Move to next hour
                current_time += timezone.timedelta(hours=1)
            
            doctors_with_appointments.append({
                'doctor': doctor,
                'time_slots': time_slots
            })
        
        context = {
            'doctors_with_appointments': doctors_with_appointments,
            'specialities': specialities,
            'today': today
        }
        
        return render(request, 'view_schedules.html', context)
        
    except Exception as e:
        logger.error(f"Error in view_schedules: {str(e)}")
        messages.error(request, f'Error loading schedules: {str(e)}')
        return redirect('secretaireDashboard')

def edit_doctor_profile(request):
    try:
        if 'user_id' not in request.session or request.session['role'] != 'doctor':
            messages.error(request, 'Please sign in as a doctor')
            return redirect('signin')
        
        # Get the doctor instance
        doctor = Doctor.objects.get(utilisateur_id=request.session['user_id'])
        
        if request.method == 'POST':
            # Update user information
            user = doctor.utilisateur
            user.email = request.POST.get('email')
            if request.POST.get('password'):  # Only update password if provided
                user.password = make_password(request.POST.get('password'))
            user.save()
            
            # Update doctor information
            doctor.specialite = request.POST.get('specialite')
            doctor.immatriculation = request.POST.get('immatriculation')
            doctor.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('doctorDashboard')
        
        context = {
            'doctor': doctor,
            'user': doctor.utilisateur
        }
        return render(request, 'edit_doctor_profile.html', context)
        
    except Exception as e:
        logger.error(f"Error in edit_doctor_profile: {str(e)}")
        messages.error(request, f'Error updating profile: {str(e)}')
        return redirect('doctorDashboard')
