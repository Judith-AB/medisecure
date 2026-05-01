from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import MedicalRecord
from .forms import MedicalRecordForm
from security.models import SecurityLog

@login_required
def record_list(request):
    profile = request.user.profile

    if profile.is_patient():
        # A01 - patients only see their OWN records
        records = MedicalRecord.objects.filter(
            patient=request.user
        ).select_related('doctor')

    elif profile.is_doctor():
        # doctors see records they created
        records = MedicalRecord.objects.filter(
            doctor=request.user
        ).select_related('patient')

    else:
        # admin sees all
        records = MedicalRecord.objects.all().select_related('patient', 'doctor')

    return render(request, 'records/list.html', {'records': records})

@login_required
def record_detail(request, pk):
    record = get_object_or_404(MedicalRecord, pk=pk)
    profile = request.user.profile

    # A01 - strict ownership check
    is_allowed = (
        record.patient == request.user or
        record.doctor == request.user or
        profile.is_admin()
    )

    if not is_allowed:
        # A09 - log this access attempt
        SecurityLog.log(
            request,
            'ACCESS_DENIED',
            f"{request.user.username} tried to access record #{pk} belonging to {record.patient.username}",
            is_threat=True
        )
        messages.error(request, "Access denied. You cannot view this medical record.")
        return redirect('record_list')

    return render(request, 'records/detail.html', {'record': record})

@login_required
def create_record(request):
    # A01 - only doctors and admins can create records
    profile = request.user.profile
    if profile.is_patient():
        SecurityLog.log(
            request,
            'ACCESS_DENIED',
            f"Patient {request.user.username} tried to create a medical record",
            is_threat=True
        )
        messages.error(request, "Only doctors can create medical records.")
        return redirect('record_list')

    form = MedicalRecordForm()
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.doctor = request.user
            record.save()
            SecurityLog.log(
                request,
                'REGISTER',
                f"Medical record created for patient {record.patient.username} by Dr.{request.user.username}"
            )
            messages.success(request, "Medical record created successfully.")
            return redirect('record_detail', pk=record.pk)

    return render(request, 'records/create.html', {'form': form})

@login_required
def delete_record(request, pk):
    record = get_object_or_404(MedicalRecord, pk=pk)
    profile = request.user.profile

    # A01 - only the creating doctor or admin can delete
    if record.doctor != request.user and not profile.is_admin():
        SecurityLog.log(
            request,
            'ACCESS_DENIED',
            f"{request.user.username} tried to delete record #{pk}",
            is_threat=True
        )
        messages.error(request, "You cannot delete this record.")
        return redirect('record_list')

    if request.method == 'POST':
        record.delete()
        messages.success(request, "Record deleted.")
        return redirect('record_list')

    return render(request, 'records/delete_confirm.html', {'record': record})