from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Appointment
from .forms import BookAppointmentForm, UpdateAppointmentForm
from security.models import SecurityLog

@login_required
def book_appointment(request):
    # A01 - only patients can book
    if not request.user.profile.is_patient():
        SecurityLog.log(request, 'ACCESS_DENIED',
            f"Non-patient tried to book appointment: {request.user.username}",
            is_threat=True)
        messages.error(request, "Only patients can book appointments.")
        return redirect('dashboard')

    form = BookAppointmentForm()
    if request.method == 'POST':
        form = BookAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user  # always set to logged-in user
            appointment.save()
            SecurityLog.log(request, 'REGISTER',
                f"Appointment booked by {request.user.username} with Dr.{appointment.doctor.username}")
            messages.success(request, "Appointment booked successfully!")
            return redirect('my_appointments')

    return render(request, 'appointments/book.html', {'form': form})

@login_required
def my_appointments(request):
    profile = request.user.profile
    if profile.is_patient():
        appointments = Appointment.objects.filter(
            patient=request.user
        ).select_related('doctor').order_by('-date')
    elif profile.is_doctor():
        appointments = Appointment.objects.filter(
            doctor=request.user
        ).select_related('patient').order_by('-date')
    else:
        appointments = Appointment.objects.all().order_by('-date')

    return render(request, 'appointments/list.html', {'appointments': appointments})

@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    # A01 - strict ownership check
    profile = request.user.profile
    is_owner = (
        appointment.patient == request.user or
        appointment.doctor == request.user or
        profile.is_admin()
    )
    if not is_owner:
        SecurityLog.log(request, 'ACCESS_DENIED',
            f"{request.user.username} tried to access appointment #{pk} (not theirs)",
            is_threat=True)
        messages.error(request, "Access denied. This is not your appointment.")
        return redirect('my_appointments')

    form = None
    if request.user == appointment.doctor or profile.is_admin():
        form = UpdateAppointmentForm(instance=appointment)
        if request.method == 'POST':
            form = UpdateAppointmentForm(request.POST, instance=appointment)
            if form.is_valid():
                form.save()
                messages.success(request, "Appointment updated.")
                return redirect('appointment_detail', pk=pk)

    return render(request, 'appointments/detail.html', {
        'appointment': appointment,
        'form': form,
    })

@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    # A01 - only the patient who owns it can cancel
    if appointment.patient != request.user:
        SecurityLog.log(request, 'ACCESS_DENIED',
            f"{request.user.username} tried to cancel appointment #{pk} (not theirs)",
            is_threat=True)
        messages.error(request, "You can only cancel your own appointments.")
        return redirect('my_appointments')

    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, "Appointment cancelled.")
        return redirect('my_appointments')

    return render(request, 'appointments/cancel_confirm.html', {'appointment': appointment})