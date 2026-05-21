"""
Views for user registration and dashboard access
"""
import time
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import StudentRegistrationForm, CoordinatorRegistrationForm, StudentProfileForm, CoordinatorProfileForm
from .utils import generate_otp, send_otp_email
from core.models import JobApplication
from django.contrib.auth import get_user_model
User = get_user_model()

OTP_EXPIRY_SECONDS = 600  # 10 minutes


def _session_otp_set(request, email, otp_code, purpose):
    """Store OTP in session with creation timestamp."""
    request.session[f'otp_{purpose}'] = {
        'email': email,
        'code': otp_code,
        'created_at': time.time(),
    }


def _session_otp_verify(request, email, otp_code, purpose):
    """
    Verify OTP from session. Returns True and clears session entry on success.
    Returns False if missing, expired, email mismatch, or wrong code.
    """
    key = f'otp_{purpose}'
    data = request.session.get(key)
    if not data:
        return False
    if data.get('email') != email:
        return False
    if time.time() - data.get('created_at', 0) > OTP_EXPIRY_SECONDS:
        del request.session[key]
        return False
    if data.get('code') != otp_code:
        return False
    # Valid — clear it so it cannot be reused
    del request.session[key]
    return True


def student_register(request):
    """
    Student registration view with OTP
    """
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in. Please logout if you wish to register a new account.")
        return redirect('/')
    
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            otp_code = generate_otp()
            success, dev_otp = send_otp_email(email, otp_code, 'registration')
            if success:
                # Store form data and OTP in session — no DB needed
                request.session['registration_data'] = request.POST.dict()
                request.session['registration_role'] = 'student'
                _session_otp_set(request, email, otp_code, 'registration')
                # In dev mode, stash the OTP so the verify page can show it
                if dev_otp:
                    request.session['dev_otp_registration'] = dev_otp
                    messages.warning(request, '⚠️ DEV MODE: Email not sent. Your OTP is shown below.')
                else:
                    messages.info(request, f'A 6-digit OTP has been sent to {email}. Please check your inbox.')
                return redirect('verify_otp_reg')
            else:
                messages.error(request, 'Failed to send OTP. Please check your email configuration in .env.')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = StudentRegistrationForm()

    return render(request, 'student_register.html', {'form': form})


def coordinator_register(request):
    """
    Coordinator registration view with OTP
    """
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in. Please logout if you wish to register a new account.")
        return redirect('/')
    
    if request.method == 'POST':
        form = CoordinatorRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            otp_code = generate_otp()
            success, dev_otp = send_otp_email(email, otp_code, 'registration')
            if success:
                request.session['registration_data'] = request.POST.dict()
                request.session['registration_role'] = 'coordinator'
                _session_otp_set(request, email, otp_code, 'registration')
                if dev_otp:
                    request.session['dev_otp_registration'] = dev_otp
                    messages.warning(request, '⚠️ DEV MODE: Email not sent. Your OTP is shown below.')
                else:
                    messages.info(request, f'A 6-digit OTP has been sent to {email}. Please check your inbox.')
                return redirect('verify_otp_reg')
            else:
                messages.error(request, 'Failed to send OTP. Please check your email configuration in .env.')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = CoordinatorRegistrationForm()

    return render(request, 'coordinator_register.html', {'form': form})


def verify_otp_reg(request):
    """Verify OTP for both student and coordinator registration"""
    reg_data = request.session.get('registration_data')
    role = request.session.get('registration_role')
    
    if not reg_data:
        messages.error(request, 'Invalid registration session.')
        return redirect('/')
    
    email = reg_data.get('email')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp')
        if _session_otp_verify(request, email, otp_code, 'registration'):
            # Re-initialize form with session data
            if role == 'student':
                form = StudentRegistrationForm(reg_data)
            else:
                form = CoordinatorRegistrationForm(reg_data)

            if form.is_valid():
                form.save()
                # Clear session
                request.session.pop('registration_data', None)
                request.session.pop('registration_role', None)
                messages.success(request, 'Verification successful! You can now login.')
                return redirect('/')
            else:
                messages.error(request, 'Data consistency error. Please register again.')
                return redirect('student_register' if role == 'student' else 'coordinator_register')
        else:
            messages.error(request, 'Invalid or expired OTP. Please try again.')

    # Pop the dev OTP from session (show once, then gone)
    dev_otp = request.session.pop('dev_otp_registration', None)
    return render(request, 'accounts/verify_otp.html', {
        'email': email,
        'purpose': 'Registration',
        'dev_otp': dev_otp,
    })


def forgot_password(request):
    """Forgot password request view"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp_code = generate_otp()
            success, dev_otp = send_otp_email(email, otp_code, 'password_reset')
            if success:
                request.session['reset_email'] = email
                _session_otp_set(request, email, otp_code, 'password_reset')
                if dev_otp:
                    request.session['dev_otp_password_reset'] = dev_otp
                    messages.warning(request, '⚠️ DEV MODE: Email not sent. Your OTP is shown below.')
                else:
                    messages.info(request, f'A 6-digit OTP has been sent to {email}. Please check your inbox.')
                return redirect('verify_otp_reset')
            else:
                messages.error(request, 'Error sending OTP. Please check your email configuration in .env.')
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address.')

    return render(request, 'accounts/forgot_password.html')


def verify_otp_reset(request):
    """Verify OTP for password reset"""
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')
        
    if request.method == 'POST':
        otp_code = request.POST.get('otp')
        if _session_otp_verify(request, email, otp_code, 'password_reset'):
            # Mark OTP as verified in session so reset_password_new knows it's legitimate
            request.session['otp_reset_verified'] = True
            messages.success(request, 'OTP verified. You can now reset your password.')
            return redirect('reset_password_new')
        else:
            messages.error(request, 'Invalid or expired OTP. Please try again.')

    dev_otp = request.session.pop('dev_otp_password_reset', None)
    return render(request, 'accounts/verify_otp.html', {
        'email': email,
        'purpose': 'Password Reset',
        'dev_otp': dev_otp,
    })


def reset_password_new(request):
    """Set new password after OTP verification"""
    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_reset_verified', False)

    # Guard: must have passed OTP verification
    if not email or not otp_verified:
        messages.error(request, 'Please verify your OTP first.')
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                # Clean up session
                request.session.pop('reset_email', None)
                request.session.pop('otp_reset_verified', None)
                messages.success(request, 'Password reset successful. Please login with your new password.')
                return redirect('/')
            except Exception as e:
                messages.error(request, f'Error resetting password: {str(e)}')
        else:
            messages.error(request, 'Passwords do not match.')

    return render(request, 'accounts/reset_password_new.html')


@login_required
def student_dashboard(request):
    """
    Student dashboard with role-based access control
    """
    # Check if user is a student
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('/')
    
    from core.models import PlacementDrive, JobApplication
    from django.utils import timezone
    
    student = request.user.studentprofile
    now = timezone.now()
    
    # Get all drives for the student's batch and year
    drives = PlacementDrive.objects.filter(
        eligible_batch=student.batch,
        eligible_year=student.year
    )
    
    active_drives = []
    expired_drives = []
    student_course = student.user.department
    
    for drive in drives:
        # Check CGPA eligibility
        cgpa_eligible = True
        if drive.min_cgpa is not None:
            if student.cgpa < drive.min_cgpa:
                cgpa_eligible = False
        
        # Check Department eligibility
        dept_eligible = False
        if drive.is_for_all_departments:
            dept_eligible = True
        elif student_course and drive.eligible_departments.filter(id=student_course.id).exists():
            dept_eligible = True
        elif not drive.eligible_departments.exists():
            dept_eligible = True
            
        if cgpa_eligible and dept_eligible:
            if drive.registration_deadline > now:
                active_drives.append(drive)
            else:
                expired_drives.append(drive)
    
    # Get applications to show status on dashboard if needed
    applications = JobApplication.objects.filter(student=student)
    applied_drive_ids = list(applications.values_list('drive_id', flat=True))
    accepted_application = applications.filter(is_accepted=True).first()

    context = {
        'user': request.user,
        'active_drives': active_drives,
        'expired_drives': expired_drives,
        'applied_drive_ids': applied_drive_ids,
        'accepted_application': accepted_application,
        'active_count': len(active_drives),
        'expired_count': len(expired_drives),
    }
    
    return render(request, 'student_dashboard.html', context)


@login_required
def student_profile(request):
    if request.user.role != 'student':
        messages.error(request, 'Access denied.')
        return redirect('/')
    
    profile = request.user.studentprofile
    applications = JobApplication.objects.filter(student=profile).select_related('drive')
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('student_profile')
    else:
        form = StudentProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
        'applications': applications,
        'resume': getattr(request.user, 'resume', None)
    }
    return render(request, 'student_profile.html', context)


@login_required
def coordinator_profile(request):
    if request.user.role != 'coordinator':
        messages.error(request, 'Access denied.')
        return redirect('/')
    
    if request.method == 'POST':
        form = CoordinatorProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('coordinator_profile')
    else:
        form = CoordinatorProfileForm(instance=request.user)
    
    return render(request, 'coordinator_profile.html', {'form': form})
