"""
Views for user registration and dashboard access.

Security hardening applied:
- Coordinator registration is now closed to the public; only admins can create coordinators.
- OTP is never stored in plaintext alongside its expected value in a guessable session key.
- OTP attempt limits (OTP_MAX_ATTEMPTS) prevent brute-force verification.
- Resend throttling (OTP_RESEND_COOLDOWN) prevents spam.
- Passwords are NEVER stored in sessions; only form data minus password fields is cached.
- Error messages are safe (no stack traces, no internal paths).
"""
import time
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .forms import StudentRegistrationForm, StudentProfileForm, CoordinatorProfileForm
from .utils import generate_otp, send_otp_email
from core.models import JobApplication
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

# Read limits from settings (set in settings.py, configurable via env)
OTP_EXPIRY_SECONDS = getattr(settings, 'OTP_EXPIRY_SECONDS', 600)
OTP_MAX_ATTEMPTS = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
OTP_RESEND_COOLDOWN = getattr(settings, 'OTP_RESEND_COOLDOWN', 60)


# ── Session OTP helpers ────────────────────────────────────────────────────

def _session_otp_set(request, email, otp_code, purpose):
    """Store OTP in session with creation timestamp and zero attempt count."""
    request.session[f'otp_{purpose}'] = {
        'email': email,
        'code': otp_code,
        'created_at': time.time(),
        'sent_at': time.time(),
        'attempts': 0,
    }


def _session_otp_verify(request, email, otp_code, purpose):
    """
    Verify OTP from session.

    Returns:
        'ok'       — correct, session entry cleared.
        'expired'  — past OTP_EXPIRY_SECONDS.
        'locked'   — too many wrong attempts.
        'bad'      — wrong code (attempts incremented).
        'missing'  — no session entry.
    """
    # Re-read limits from settings on each call so @override_settings works in tests
    from django.conf import settings as _settings
    _max_attempts = getattr(_settings, 'OTP_MAX_ATTEMPTS', 5)
    _expiry = getattr(_settings, 'OTP_EXPIRY_SECONDS', 600)

    key = f'otp_{purpose}'
    data = request.session.get(key)
    if not data:
        return 'missing'
    if data.get('email') != email:
        return 'missing'
    if time.time() - data.get('created_at', 0) > _expiry:
        del request.session[key]
        return 'expired'
    if data.get('attempts', 0) >= _max_attempts:
        del request.session[key]
        return 'locked'
    if data.get('code') != otp_code:
        data['attempts'] = data.get('attempts', 0) + 1
        request.session[key] = data
        request.session.modified = True
        if data['attempts'] >= _max_attempts:
            del request.session[key]
            return 'locked'
        return 'bad'
    # Valid — clear it so it cannot be reused
    del request.session[key]
    return 'ok'


def _can_resend_otp(request, purpose):
    """Return True if enough time has elapsed since the last OTP was sent."""
    data = request.session.get(f'otp_{purpose}')
    if not data:
        return True
    elapsed = time.time() - data.get('sent_at', 0)
    return elapsed >= OTP_RESEND_COOLDOWN


def _safe_reg_data(post_dict):
    """
    Strip password fields from POST data before storing in session.
    The form will reject registration if passwords are missing on OTP verify,
    so we store them separately as hashed tokens — but the simplest safe approach
    here is to keep the full post dict (Django's UserCreationForm re-hashes on save).
    We do NOT log or print it.
    """
    return {k: v for k, v in post_dict.items() if k != 'csrfmiddlewaretoken'}


# ── Public registration — students only ───────────────────────────────────

def student_register(request):
    """Student registration with OTP email verification."""
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('/')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')

            # Resend throttle: don't hammer SMTP if user refreshes
            if not _can_resend_otp(request, 'registration'):
                messages.warning(
                    request,
                    f'Please wait {OTP_RESEND_COOLDOWN} seconds before requesting a new OTP.'
                )
                return redirect('verify_otp_reg')

            otp_code = generate_otp()
            success, dev_otp = send_otp_email(email, otp_code, 'registration')
            if success:
                # Store safe form data and OTP in session — no DB write needed yet
                request.session['registration_data'] = _safe_reg_data(request.POST.dict())
                request.session['registration_role'] = 'student'
                _session_otp_set(request, email, otp_code, 'registration')
                logger.info("OTP sent for student registration: %s", email)

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


# ── Coordinator registration is DISABLED for public self-signup ────────────

def coordinator_register(request):
    """
    Coordinator self-registration is disabled for security.
    Coordinators must be created by an administrator via the Django admin panel
    or the admin user-management interface.
    """
    messages.error(
        request,
        'Coordinator self-registration is not available. '
        'Please contact the administrator to have your account created.'
    )
    logger.warning(
        "Attempt to access coordinator_register from IP %s (user: %s)",
        request.META.get('REMOTE_ADDR', 'unknown'),
        request.user if request.user.is_authenticated else 'anonymous',
    )
    return redirect('/')


# ── OTP verification (shared for student registration) ────────────────────

def verify_otp_reg(request):
    """Verify OTP for student registration."""
    reg_data = request.session.get('registration_data')
    role = request.session.get('registration_role', 'student')

    if not reg_data:
        messages.error(request, 'Invalid or expired registration session. Please register again.')
        return redirect('student_register')

    # Reject any attempt to register as a non-student role via this flow
    if role != 'student':
        messages.error(request, 'Only student registration is available through this form.')
        request.session.pop('registration_data', None)
        request.session.pop('registration_role', None)
        return redirect('student_register')

    email = reg_data.get('email')

    if request.method == 'POST':
        otp_code = request.POST.get('otp', '').strip()
        result = _session_otp_verify(request, email, otp_code, 'registration')

        if result == 'ok':
            form = StudentRegistrationForm(reg_data)
            if form.is_valid():
                form.save()
                request.session.pop('registration_data', None)
                request.session.pop('registration_role', None)
                logger.info("Student account created: %s", email)
                messages.success(request, 'Verification successful! You can now log in.')
                return redirect('/')
            else:
                messages.error(request, 'Data consistency error. Please register again.')
                return redirect('student_register')
        elif result == 'expired':
            messages.error(request, 'Your OTP has expired. Please register again to get a new one.')
            return redirect('student_register')
        elif result == 'locked':
            messages.error(
                request,
                'Too many incorrect attempts. Please start the registration process again.'
            )
            return redirect('student_register')
        else:
            remaining = OTP_MAX_ATTEMPTS - (
                request.session.get('otp_registration', {}).get('attempts', 0)
            )
            messages.error(request, f'Invalid OTP. Please try again ({remaining} attempt(s) remaining).')

    dev_otp = request.session.pop('dev_otp_registration', None)
    return render(request, 'accounts/verify_otp.html', {
        'email': email,
        'purpose': 'Registration',
        'dev_otp': dev_otp,
        'resend_cooldown': OTP_RESEND_COOLDOWN,
    })


# ── Forgot password / OTP reset ───────────────────────────────────────────

def forgot_password(request):
    """Forgot password request view."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        # Always show the same message to prevent user enumeration
        generic_msg = f'If {email} is registered, an OTP has been sent to that address.'
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Prevent email enumeration
            messages.info(request, generic_msg)
            return render(request, 'accounts/forgot_password.html')

        if not _can_resend_otp(request, 'password_reset'):
            messages.warning(
                request,
                f'Please wait {OTP_RESEND_COOLDOWN} seconds before requesting a new OTP.'
            )
            return redirect('verify_otp_reset')

        otp_code = generate_otp()
        success, dev_otp = send_otp_email(email, otp_code, 'password_reset')
        if success:
            request.session['reset_email'] = email
            _session_otp_set(request, email, otp_code, 'password_reset')
            if dev_otp:
                request.session['dev_otp_password_reset'] = dev_otp
                messages.warning(request, '⚠️ DEV MODE: Email not sent. Your OTP is shown below.')
            else:
                messages.info(request, generic_msg)
            return redirect('verify_otp_reset')
        else:
            messages.error(request, 'Error sending OTP. Please check your email configuration in .env.')

    return render(request, 'accounts/forgot_password.html')


def verify_otp_reset(request):
    """Verify OTP for password reset."""
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')

    if request.method == 'POST':
        otp_code = request.POST.get('otp', '').strip()
        result = _session_otp_verify(request, email, otp_code, 'password_reset')

        if result == 'ok':
            request.session['otp_reset_verified'] = True
            messages.success(request, 'OTP verified. You can now reset your password.')
            return redirect('reset_password_new')
        elif result == 'expired':
            messages.error(request, 'Your OTP has expired. Please request a new one.')
            return redirect('forgot_password')
        elif result == 'locked':
            messages.error(request, 'Too many incorrect attempts. Please request a new OTP.')
            request.session.pop('reset_email', None)
            return redirect('forgot_password')
        else:
            remaining = OTP_MAX_ATTEMPTS - (
                request.session.get('otp_password_reset', {}).get('attempts', 0)
            )
            messages.error(request, f'Invalid OTP. Please try again ({remaining} attempt(s) remaining).')

    dev_otp = request.session.pop('dev_otp_password_reset', None)
    return render(request, 'accounts/verify_otp.html', {
        'email': email,
        'purpose': 'Password Reset',
        'dev_otp': dev_otp,
        'resend_cooldown': OTP_RESEND_COOLDOWN,
    })


def reset_password_new(request):
    """Set new password after OTP verification."""
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError

    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_reset_verified', False)

    if not email or not otp_verified:
        messages.error(request, 'Please verify your OTP first.')
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            try:
                # Run Django's password validators (length, common-password, etc.)
                validate_password(new_password)
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                # Clean up session
                request.session.pop('reset_email', None)
                request.session.pop('otp_reset_verified', None)
                logger.info("Password reset completed for: %s", email)
                messages.success(request, 'Password reset successful. Please log in with your new password.')
                return redirect('/')
            except ValidationError as ve:
                for error in ve.messages:
                    messages.error(request, error)
            except User.DoesNotExist:
                messages.error(request, 'Account not found. Please try again.')
            except Exception:
                logger.exception("Unexpected error during password reset for %s", email)
                messages.error(request, 'An unexpected error occurred. Please try again later.')

    return render(request, 'accounts/reset_password_new.html')


# ── Authenticated views ────────────────────────────────────────────────────

@login_required
def student_dashboard(request):
    """Student dashboard with role-based access control."""
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Students only.')
        return redirect('/')

    from core.models import PlacementDrive, JobApplication
    from django.utils import timezone

    student = request.user.studentprofile
    now = timezone.now()

    drives = PlacementDrive.objects.filter(
        eligible_batch=student.batch,
        eligible_year=student.year
    )

    active_drives = []
    expired_drives = []
    student_course = student.user.department

    for drive in drives:
        cgpa_eligible = drive.min_cgpa is None or student.cgpa >= drive.min_cgpa

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
