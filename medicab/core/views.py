from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Utilisateur

def landing_page(request):
    return render(request, 'core/landing.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.role == 'patient':
                return redirect('patient_dashboard')
            elif user.role == 'doctor':
                return redirect('doctor_dashboard')
            elif user.role == 'secretaire':
                return redirect('secretaire_dashboard')
        else:
            return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('landing')

def register_view(request):
    return render(request, 'core/register.html')  # TODO: implement with form

@login_required
def patient_dashboard(request):
    return render(request, 'core/patient_dashboard.html')

@login_required
def doctor_dashboard(request):
    return render(request, 'core/doctor_dashboard.html')

@login_required
def secretaire_dashboard(request):
    return render(request, 'core/secretaire_dashboard.html')
