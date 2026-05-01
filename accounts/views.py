from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from .forms import RegisterForm, SecureLoginForm, ProfileUpdateForm
from .models import UserProfile
from security.models import SecurityLog
import time

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300

@never_cache
@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(
                user=user,
                role=form.cleaned_data['role'],
                phone=form.cleaned_data.get('phone', ''),
                specialization=form.cleaned_data.get('specialization', ''),
            )
            SecurityLog.log(request, 'REGISTER', f"New {form.cleaned_data['role']} registered: {user.username}")
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Account created.")
            return redirect('dashboard')
    return render(request, 'accounts/register.html', {'form': form})

@never_cache
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    # A04 - brute force protection
    attempts = request.session.get('login_attempts', 0)
    lockout_until = request.session.get('lockout_until', 0)

    if lockout_until > time.time():
        remaining = int(lockout_until - time.time())
        SecurityLog.log(request, 'BRUTE_FORCE', f"Login attempted during lockout")
        return render(request, 'accounts/login.html', {
            'form': SecureLoginForm(),
            'locked': True,
            'remaining': remaining
        })

    form = SecureLoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            request.session['login_attempts'] = 0
            request.session.cycle_key()  # A07 - prevent session fixation
            login(request, user)
            SecurityLog.log(request, 'LOGIN_SUCCESS', f"User logged in: {user.username}")
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            attempts += 1
            request.session['login_attempts'] = attempts
            SecurityLog.log(request, 'LOGIN_FAILED', f"Failed login attempt #{attempts} for: {request.POST.get('username','?')}")
            if attempts >= MAX_ATTEMPTS:
                request.session['lockout_until'] = time.time() + LOCKOUT_SECONDS
                request.session['login_attempts'] = 0
                SecurityLog.log(request, 'ACCOUNT_LOCKED', f"Account locked after {MAX_ATTEMPTS} failed attempts")
                messages.error(request, "Too many failed attempts. Locked for 5 minutes.")
            else:
                messages.error(request, f"Invalid credentials. {MAX_ATTEMPTS - attempts} attempt(s) left.")

    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    if request.method == 'POST':  # A07 - POST-only logout
        SecurityLog.log(request, 'LOGOUT', f"User logged out: {request.user.username}")
        logout(request)
        messages.success(request, "Logged out securely.")
        return redirect('home')
    return render(request, 'accounts/logout_confirm.html')

@login_required
@never_cache
def dashboard_view(request):
    profile = request.user.profile
    context = {'profile': profile}
    if profile.is_patient():
        from appointments.models import Appointment
        context['appointments'] = Appointment.objects.filter(patient=request.user).order_by('-date')[:5]
    elif profile.is_doctor():
        from appointments.models import Appointment
        context['appointments'] = Appointment.objects.filter(doctor=request.user).order_by('-date')[:5]
    return render(request, 'accounts/dashboard.html', context)

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = ProfileUpdateForm(instance=profile, initial={
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
    })
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('profile')
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})