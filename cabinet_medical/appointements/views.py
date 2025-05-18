from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Appointement
from utilisateurs.models import Patient, Doctor, Utilisateurs
from invoice.models import Invoice
from calendar import monthcalendar
import calendar

def book_appointment(request):
    if request.method == 'POST':
        try:
            # Handle both patient and secretary bookings
            if request.session['role'] == 'patient':
                patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
            elif request.session['role'] == 'secretaire':
                patient_id = request.POST.get('patient')
                if not patient_id:
                    messages.error(request, 'Please select a patient')
                    return redirect('book_appointment')
                patient = Patient.objects.get(id=patient_id)
            else:
                messages.error(request, 'Unauthorized access')
                return redirect('signin')

            doctor_id = request.POST.get('doctor')
            selected_time = request.POST.get('selected_time')
            
            if not selected_time:
                messages.error(request, 'Please select a time slot')
                return redirect('book_appointment')
            
            # Convert string to timezone-aware datetime
            date = timezone.make_aware(datetime.strptime(selected_time, '%Y-%m-%dT%H:%M'))
            
            # Check if the date is in the future
            if date <= timezone.now():
                messages.error(request, 'Please select a future date and time')
                return redirect('book_appointment')
            
            # Validate time slot (must be between 9 AM and 5 PM)
            hour = date.hour
            if hour < 9 or hour >= 17:
                messages.error(request, 'Appointments can only be booked between 9 AM and 5 PM')
                return redirect('book_appointment')
            
            # Check if the time slot is already booked
            existing_appointment = Appointement.objects.filter(
                doctor_id=doctor_id,
                date__date=date.date(),
                date__hour=date.hour,
                status='upcoming'
            ).exists()
            
            if existing_appointment:
                messages.error(request, 'This time slot is already booked')
                return redirect('book_appointment')
            
            # Create the appointment
            appointment = Appointement.objects.create(
                patient=patient,
                doctor_id=doctor_id,
                date=date,
                status='pending_payment'  # New status for unpaid appointments
            )

            # Create an invoice for the appointment
            invoice = Invoice.objects.create(
                patient=patient,
                doctor_id=doctor_id,
                appointment=appointment,
                amount=100.00,  # You can adjust this or make it dynamic based on your needs
                issued_date=timezone.now().date()
            )

            messages.success(request, 'Appointment booked successfully! Please complete the payment to confirm your appointment.')
            
            if request.session['role'] == 'patient':
                return redirect('process_payment', invoice_id=invoice.id)
            else:
                return redirect('secretaire_appointments')
                
        except Exception as e:
            messages.error(request, f'Error booking appointment: {str(e)}')
    
    # Get pre-selected doctor and date from query parameters
    selected_doctor_id = request.GET.get('doctor')
    selected_date = request.GET.get('date')
    
    # Generate available time slots for the selected date
    available_slots = []
    if selected_date and selected_doctor_id:
        try:
            # Parse the date string and ensure it's in the correct format
            selected_datetime = timezone.make_aware(datetime.strptime(selected_date.split('T')[0], '%Y-%m-%d'))
            
            # Get all appointments for the selected doctor and date
            existing_appointments = Appointement.objects.filter(
                doctor_id=selected_doctor_id,
                date__date=selected_datetime.date(),
                status='upcoming'
            ).values_list('date__hour', flat=True)
            
            # Generate time slots from 9 AM to 5 PM
            for hour in range(9, 17):
                slot_time = selected_datetime.replace(hour=hour, minute=0)
                available_slots.append({
                    'time': slot_time,
                    'is_available': hour not in existing_appointments
                })
        except (ValueError, IndexError) as e:
            messages.error(request, 'Invalid date format')
            selected_date = None
    
    # Get context data
    context = {
        'doctors': Doctor.objects.all(),
        'selected_doctor_id': selected_doctor_id,
        'selected_date': selected_date,
        'available_slots': available_slots,
        'today': timezone.now().date()
    }
    
    # Add patients list for secretary
    if request.session['role'] == 'secretaire':
        context['patients'] = Patient.objects.all()
    
    return render(request, 'book_appointment.html', context)

def cancel_appointment(request, appointment_id):
    try:
        appointment = Appointement.objects.get(id=appointment_id)
        if request.session['role'] == 'patient' and appointment.patient.utilisateur_id != request.session['user_id']:
            messages.error(request, 'You can only cancel your own appointments')
            return redirect('patient_appointments')
        
        appointment.status = 'cancelled'  # Use the string value directly
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully')
    except Exception as e:
        messages.error(request, f'Error cancelling appointment: {str(e)}')
    
    if request.session['role'] == 'patient':
        return redirect('patient_appointments')
    elif request.session['role'] == 'doctor':
        return redirect('doctor_appointments')
    else:
        return redirect('secretaire_appointments')

def patient_appointments(request):
    if 'user_id' not in request.session or request.session['role'] != 'patient':
        messages.error(request, 'Please sign in as a patient')
        return redirect('signin')
    
    patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
    appointments = Appointement.objects.filter(
        patient=patient
    ).exclude(
        status='cancelled'
    ).order_by('date')
    return render(request, 'patient_appointments.html', {'appointments': appointments})

def doctor_appointments(request):
    if 'user_id' not in request.session or request.session['role'] != 'doctor':
        messages.error(request, 'Please sign in as a doctor')
        return redirect('signin')
    
    doctor = Doctor.objects.get(utilisateur_id=request.session['user_id'])
    appointments = Appointement.objects.filter(
        doctor=doctor
    ).exclude(
        status='cancelled'
    ).order_by('date')
    return render(request, 'doctor_appointments.html', {'appointments': appointments})

def secretaire_appointments(request):
    if 'user_id' not in request.session or request.session['role'] != 'secretaire':
        messages.error(request, 'Please sign in as a secretaire')
        return redirect('signin')
    
    appointments = Appointement.objects.all().exclude(
        status='cancelled'
    ).order_by('date')
    return render(request, 'secretaire_appointments.html', {'appointments': appointments})

def complete_appointment(request, appointment_id):
    if request.session['role'] not in ['doctor', 'secretaire']:
        messages.error(request, 'Unauthorized action')
        return redirect('signin')
    
    try:
        appointment = Appointement.objects.get(id=appointment_id)
        
        # Check if the appointment is paid
        if appointment.status == 'pending_payment':
            messages.error(request, 'Cannot complete appointment: Payment is pending')
            return redirect('doctor_appointments')
            
        appointment.status = 'completed'
        appointment.save()

        # Create an invoice for the completed appointment if it doesn't exist
        if not hasattr(appointment, 'invoice'):
            Invoice.objects.create(
                patient=appointment.patient,
                doctor=appointment.doctor,
                appointment=appointment,
                amount=100.00,  # You can adjust this or make it dynamic based on your needs
                issued_date=timezone.now().date()
            )
            messages.success(request, 'Appointment completed and invoice created')
        else:
            messages.success(request, 'Appointment marked as completed')
    except Exception as e:
        messages.error(request, f'Error completing appointment: {str(e)}')
    
    if request.session['role'] == 'doctor':
        return redirect('doctor_appointments')
    else:
        return redirect('secretaire_appointments')

def doctor_calendar(request):
    if 'user_id' not in request.session or request.session['role'] != 'doctor':
        messages.error(request, 'Please sign in as a doctor')
        return redirect('signin')
    
    doctor = Doctor.objects.get(utilisateur_id=request.session['user_id'])
    print(f"Doctor found: {doctor.utilisateur.username}")  # Debug log
    
    # Get the current date or use the date from query parameters
    today = timezone.now().date()
    view_type = request.GET.get('view', 'week')  # Default to week view
    selected_date = request.GET.get('date')
    
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today
    
    print(f"View type: {view_type}, Selected date: {selected_date}")  # Debug log
    
    # Calculate navigation dates
    if view_type == 'day':
        prev_date = selected_date - timedelta(days=1)
        next_date = selected_date + timedelta(days=1)
        prev_url = f'?view=day&date={prev_date.strftime("%Y-%m-%d")}'
        next_url = f'?view=day&date={next_date.strftime("%Y-%m-%d")}'
    else:
        # Calculate the start of the week (Monday)
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        prev_week_start = start_of_week - timedelta(days=7)
        next_week_start = start_of_week + timedelta(days=7)
        
        prev_url = f'?view=week&date={prev_week_start.strftime("%Y-%m-%d")}'
        next_url = f'?view=week&date={next_week_start.strftime("%Y-%m-%d")}'
    
    if view_type == 'day':
        # Get appointments for the selected day
        appointments = Appointement.objects.filter(
            doctor=doctor,
            date__date=selected_date
        ).exclude(
            status='cancelled'
        ).order_by('date')
        
        print(f"Day view - Found {appointments.count()} appointments")  # Debug log
        for apt in appointments:
            print(f"Appointment: {apt.date} - {apt.patient.utilisateur.username}")  # Debug log
        
        context = {
            'view_type': 'day',
            'selected_date': selected_date,
            'appointments': appointments,
            'time_slots': range(9, 17),  # 9 AM to 5 PM
            'prev_url': prev_url,
            'next_url': next_url
        }
        
    else:  # week view
        # Calculate the start of the week (Monday)
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        print(f"Week view - From {start_of_week} to {end_of_week}")  # Debug log
        
        # Get all appointments for the week
        appointments = Appointement.objects.filter(
            doctor=doctor,
            date__date__gte=start_of_week,
            date__date__lte=end_of_week
        ).exclude(
            status='cancelled'
        ).order_by('date')
        
        print(f"Week view - Found {appointments.count()} appointments")  # Debug log
        
        # Organize appointments by day
        week_appointments = {}
        for day in range(7):
            current_date = start_of_week + timedelta(days=day)
            week_appointments[current_date] = []
        
        for appointment in appointments:
            day = appointment.date.date()
            if day in week_appointments:
                week_appointments[day].append(appointment)
                print(f"Added appointment for {day}: {appointment.date} - {appointment.patient.utilisateur.username}")  # Debug log
        
        context = {
            'view_type': 'week',
            'start_of_week': start_of_week,
            'end_of_week': end_of_week,
            'week_appointments': week_appointments,
            'time_slots': range(9, 17),  # 9 AM to 5 PM
            'prev_url': prev_url,
            'next_url': next_url
        }
    
    return render(request, 'doctor_calendar.html', context)
