from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from .models import Invoice, Payment
from utilisateurs.models import Doctor
import logging
import traceback

logger = logging.getLogger(__name__)

def process_payment(request, invoice_id):
    try:
        logger.info("=== Starting Payment Process ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Session data: {dict(request.session)}")
        
        # Get invoice
        try:
            invoice = get_object_or_404(Invoice, id=invoice_id)
            logger.info(f"Found invoice: {invoice.id} for patient {invoice.patient.utilisateur.username}")
        except Exception as e:
            logger.error(f"Error finding invoice: {str(e)}")
            messages.error(request, 'Invoice not found.')
            return redirect('patientDashboard')
        
        # Check if user has permission to pay this invoice
        if 'user_id' not in request.session:
            logger.warning("No user_id in session")
            messages.error(request, 'Please sign in to make a payment.')
            return redirect('signin')
            
        user = request.session['user_id']
        logger.info(f"User ID from session: {user}")
        
        if invoice.patient.utilisateur.id != user:
            logger.warning(f"Permission denied: User {user} trying to pay invoice for patient {invoice.patient.utilisateur.id}")
            messages.error(request, 'You do not have permission to pay this invoice.')
            return redirect('patientDashboard')
            
        if invoice.is_paid:
            logger.info(f"Invoice {invoice_id} is already paid")
            messages.info(request, 'This invoice has already been paid.')
            return redirect('patientDashboard')
            
        if request.method == 'POST':
            logger.info("Processing POST request for payment")
            payment_method = request.POST.get('payment_method')
            logger.info(f"Payment method selected: {payment_method}")
            
            if not payment_method:
                logger.error("No payment method provided")
                messages.error(request, 'Please select a payment method.')
                return render(request, 'payment.html', {
                    'invoice': invoice,
                    'payment_methods': Payment.PaymentMethod.choices
                })
            
            try:
                # For MVP testing: Simulate a successful payment
                logger.info("Creating payment record...")
                payment = Payment.objects.create(
                    invoice=invoice,
                    amount=invoice.amount,
                    payment_method=payment_method,
                    status='completed',
                    transaction_id=f"TEST_{invoice.id}_{int(timezone.now().timestamp())}",
                    payment_date=timezone.now()
                )
                logger.info(f"Created test payment record: {payment.id}")
                
                # Mark invoice as paid
                logger.info("Marking invoice as paid...")
                invoice.is_paid = True
                invoice.save()
                logger.info("Invoice marked as paid")
                
                # Update appointment status
                logger.info("Updating appointment status...")
                try:
                    appointment = invoice.appointment
                    logger.info(f"Found appointment: {appointment.id}")
                    appointment.status = 'upcoming'
                    appointment.save()
                    logger.info("Appointment status updated to upcoming")
                except Exception as e:
                    logger.error(f"Error updating appointment: {str(e)}")
                    # Continue anyway since payment was successful
                
                messages.success(request, 'Payment completed successfully! Your appointment is now confirmed.')
                return redirect('patient_appointments')
                
            except Exception as e:
                logger.error(f"Error during payment processing: {str(e)}\n{traceback.format_exc()}")
                messages.error(request, f'Error processing payment: {str(e)}')
                return render(request, 'payment.html', {
                    'invoice': invoice,
                    'payment_methods': Payment.PaymentMethod.choices
                })
            
        logger.info("Rendering payment form")
        return render(request, 'payment.html', {
            'invoice': invoice,
            'payment_methods': Payment.PaymentMethod.choices
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in payment process: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, f'Error processing payment: {str(e)}')
        return redirect('patientDashboard')

def doctor_financial_dashboard(request):
    try:
        logger.info("=== Starting Financial Dashboard View ===")
        logger.info(f"Session data: {dict(request.session)}")
        
        # Check if user is logged in and is a doctor
        if 'user_id' not in request.session:
            logger.warning("User not logged in - No user_id in session")
            messages.error(request, 'Please sign in to access the dashboard.')
            return redirect('signin')
            
        if request.session.get('role') != 'doctor':
            logger.warning(f"User {request.session['user_id']} is not a doctor. Role: {request.session.get('role')}")
            messages.error(request, 'Only doctors can access this dashboard.')
            return redirect('signin')
            
        # Get the doctor instance
        try:
            doctor = Doctor.objects.get(utilisateur_id=request.session['user_id'])
            logger.info(f"Found doctor: {doctor.utilisateur.username}")
        except Doctor.DoesNotExist:
            logger.error(f"Doctor not found for user {request.session['user_id']}")
            messages.error(request, 'Doctor profile not found.')
            return redirect('signin')
        except Exception as e:
            logger.error(f"Error finding doctor: {str(e)}\n{traceback.format_exc()}")
            messages.error(request, 'Error loading doctor profile.')
            return redirect('signin')
        
        # Get date ranges
        today = timezone.now().date()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)
        
        logger.info(f"Date ranges - Today: {today}, Month Start: {month_start}, Year Start: {year_start}")
        
        try:
            # Initialize default values
            monthly_earnings = 0
            yearly_earnings = 0
            total_patients = 0
            new_patients = 0
            monthly_trend = []
            recent_payments = []

            # Get all invoices for the doctor
            all_invoices = Invoice.objects.filter(doctor=doctor)
            logger.info(f"Found {all_invoices.count()} total invoices for doctor")

            if all_invoices.exists():
                # Monthly statistics
                monthly_invoices = all_invoices.filter(issued_date__gte=month_start)
                logger.info(f"Found {monthly_invoices.count()} invoices for current month")
                
                monthly_earnings = monthly_invoices.filter(is_paid=True).aggregate(
                    total=Sum('amount')
                )['total'] or 0
                
                # Yearly statistics
                yearly_invoices = all_invoices.filter(issued_date__gte=year_start)
                logger.info(f"Found {yearly_invoices.count()} invoices for current year")
                
                yearly_earnings = yearly_invoices.filter(is_paid=True).aggregate(
                    total=Sum('amount')
                )['total'] or 0
                
                # Patient statistics
                total_patients = all_invoices.values('patient').distinct().count()
                new_patients = monthly_invoices.values('patient').distinct().count()
                
                # Monthly earnings trend (last 6 months)
                six_months_ago = today - timedelta(days=180)
                monthly_trend = []
                
                # Calculate monthly earnings manually
                current_date = six_months_ago
                while current_date <= today:
                    month_start = current_date.replace(day=1)
                    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                    
                    month_earnings = all_invoices.filter(
                        issued_date__gte=month_start,
                        issued_date__lte=month_end,
                        is_paid=True
                    ).aggregate(
                        total=Sum('amount')
                    )['total'] or 0
                    
                    monthly_trend.append({
                        'month': month_start,
                        'total': month_earnings
                    })
                    
                    current_date = (month_start + timedelta(days=32)).replace(day=1)
                
                # Recent payments
                recent_payments = Payment.objects.filter(
                    invoice__doctor=doctor,
                    status='completed'
                ).select_related('invoice', 'invoice__patient').order_by('-payment_date')[:5]
            
            logger.info(f"Statistics calculated - Monthly earnings: {monthly_earnings}, Yearly earnings: {yearly_earnings}")
            logger.info(f"Patient stats - Total: {total_patients}, New: {new_patients}")
            logger.info(f"Found {len(recent_payments)} recent payments")
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}\n{traceback.format_exc()}")
            messages.error(request, 'Error calculating financial statistics.')
            return redirect('doctorDashboard')
        
        context = {
            'monthly_earnings': monthly_earnings,
            'yearly_earnings': yearly_earnings,
            'total_patients': total_patients,
            'new_patients': new_patients,
            'monthly_trend': monthly_trend,
            'recent_payments': recent_payments,
            'doctor': doctor,
            'has_data': bool(all_invoices.exists())
        }
        
        logger.info("Context prepared successfully")
        
        try:
            return render(request, 'doctor_financial_dashboard.html', context)
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}\n{traceback.format_exc()}")
            messages.error(request, 'Error displaying financial dashboard.')
            return redirect('doctorDashboard')
        
    except Exception as e:
        logger.error(f"Unexpected error in financial dashboard: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, 'Error loading financial dashboard. Please try again later.')
        return redirect('doctorDashboard')

def get_earnings_chart_data(request):
    try:
        logger.info("Fetching earnings chart data")
        
        if 'user_id' not in request.session or request.session.get('role') != 'doctor':
            logger.warning("Unauthorized access attempt to earnings chart data")
            return JsonResponse({'error': 'Unauthorized'}, status=403)
            
        doctor = get_object_or_404(Doctor, utilisateur_id=request.session['user_id'])
        
        # Get earnings for the last 12 months
        twelve_months_ago = timezone.now().date() - timedelta(days=365)
        monthly_earnings = Invoice.objects.filter(
            doctor=doctor,
            issued_date__gte=twelve_months_ago,
            is_paid=True
        ).extra(
            select={'month': "DATE_TRUNC('month', issued_date)"}
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        data = {
            'labels': [entry['month'].strftime('%B %Y') for entry in monthly_earnings],
            'earnings': [float(entry['total']) for entry in monthly_earnings]
        }
        
        logger.info("Successfully fetched earnings chart data")
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error getting earnings chart data: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Server error'}, status=500)
