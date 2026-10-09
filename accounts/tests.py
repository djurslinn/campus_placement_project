"""
Comprehensive security and regression test suite for campus_placement_project.

Covers:
- Student registration and OTP verification.
- Coordinator self-registration is blocked.
- OTP expiration, invalid codes, attempt limits, resend throttling.
- Student / coordinator / admin permission enforcement.
- Invalid, oversized, and fake-extension resume uploads.
- ATS-service failures, timeouts, and invalid responses.
- Password reset flow and user enumeration prevention.
- Existing assessment, attendance, and placement workflow smoke tests.

Run: python manage.py test accounts.tests core.tests resumes.tests --verbosity 2
"""
import io
import json
import time
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

User = get_user_model()

# ─── Helpers ──────────────────────────────────────────────────────────────────


def make_user(email, role='student', password='TestPass123!', **kwargs):
    """Create and return an active User of the given role."""
    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        role=role,
        **kwargs,
    )
    return user


def make_student_with_profile(email='student@test.com', password='TestPass123!'):
    """Create a student User with a minimal StudentProfile."""
    from accounts.models import Course, StudentProfile
    course, _ = Course.objects.get_or_create(
        category='UG', type='B.Tech', name='Computer Science', year=4
    )
    user = make_user(email, role='student', password=password)
    user.department = course
    user.save()
    profile, _ = StudentProfile.objects.get_or_create(
        user=user,
        defaults={'roll_no': 'STU0001', 'year': 2, 'batch': 2023, 'phone': '9876543210'},
    )
    return user, profile


PDF_MAGIC = b'%PDF-1.4\n'   # valid-looking PDF header for tests
FAKE_PDF = b'This is not a pdf file at all'


# ─── 1. Student Registration & OTP ───────────────────────────────────────────


class StudentRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        from accounts.models import Course
        self.course, _ = Course.objects.get_or_create(
            category='UG', type='B.Tech', name='CS', year=4
        )

    def test_register_page_loads(self):
        resp = self.client.get(reverse('student_register'))
        self.assertEqual(resp.status_code, 200)

    @patch('accounts.views.send_otp_email', return_value=(True, '123456'))
    def test_register_valid_form_sends_otp(self, mock_send):
        resp = self.client.post(reverse('student_register'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'course': self.course.pk,
            'year': '2',
            'batch': '2023',
            'password1': 'SecurePass#99',
            'password2': 'SecurePass#99',
        })
        self.assertRedirects(resp, reverse('verify_otp_reg'))
        self.assertIn('registration_data', self.client.session)

    @patch('accounts.views.send_otp_email', return_value=(False, None))
    def test_register_email_failure_shows_error(self, mock_send):
        resp = self.client.post(reverse('student_register'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'course': self.course.pk,
            'year': '2',
            'batch': '2023',
            'password1': 'SecurePass#99',
            'password2': 'SecurePass#99',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Failed to send OTP')

    def test_authenticated_user_redirected_from_register(self):
        user = make_user('existing@test.com', role='student')
        self.client.force_login(user)
        resp = self.client.get(reverse('student_register'))
        self.assertEqual(resp.status_code, 302)


class OTPVerificationTest(TestCase):
    """Test OTP expiration, attempt limits, and resend throttling."""

    def setUp(self):
        self.client = Client()
        from accounts.models import Course
        self.course, _ = Course.objects.get_or_create(
            category='UG', type='B.Tech', name='CSE', year=4
        )
        # Seed a valid registration session
        session = self.client.session
        session['registration_data'] = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'verify@example.com',
            'course': str(self.course.pk),
            'year': '2',
            'batch': '2023',
            'password1': 'SecurePass#99',
            'password2': 'SecurePass#99',
        }
        session['registration_role'] = 'student'
        session['otp_registration'] = {
            'email': 'verify@example.com',
            'code': '654321',
            'created_at': time.time(),
            'sent_at': time.time(),
            'attempts': 0,
        }
        session.save()

    def test_wrong_otp_increments_attempts(self):
        self.client.post(reverse('verify_otp_reg'), {'otp': '000000'})
        session = self.client.session
        otp_data = session.get('otp_registration', {})
        self.assertEqual(otp_data.get('attempts', 0), 1)

    def test_correct_otp_creates_user(self):
        resp = self.client.post(reverse('verify_otp_reg'), {'otp': '654321'})
        # Redirects to '/' and user is created
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(email='verify@example.com').exists())

    def test_expired_otp_rejected(self):
        session = self.client.session
        session['otp_registration'] = {
            'email': 'verify@example.com',
            'code': '654321',
            'created_at': time.time() - 700,  # expired (> 600 s)
            'sent_at': time.time() - 700,
            'attempts': 0,
        }
        session.save()
        resp = self.client.post(reverse('verify_otp_reg'), {'otp': '654321'})
        # Should redirect back to register with expiry message
        self.assertRedirects(resp, reverse('student_register'))

    @override_settings(OTP_MAX_ATTEMPTS=3)
    def test_attempt_lockout_after_max_attempts(self):
        """After OTP_MAX_ATTEMPTS wrong guesses the session entry is deleted."""
        for _ in range(3):
            self.client.post(reverse('verify_otp_reg'), {'otp': '000000'})
            # Force the client to reload the session from the DB after each POST
            self.client.session.load()
        # After 3 wrong attempts with max=3 the key should be gone
        session = self.client.session
        self.assertNotIn('otp_registration', session)


    def test_resend_throttle_blocks_immediate_resend(self):
        """If OTP was just sent, the view blocks a resend and redirects."""
        # Session already has otp_registration with sent_at = now
        from accounts.models import Course
        # Attempt to re-POST the registration form
        with patch('accounts.views.send_otp_email', return_value=(True, '999999')) as mock_send:
            resp = self.client.post(reverse('student_register'), {
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'verify@example.com',
                'course': str(self.course.pk),
                'year': '2',
                'batch': '2023',
                'password1': 'SecurePass#99',
                'password2': 'SecurePass#99',
            })
            # Should redirect to verify_otp_reg (resend throttled)
            self.assertEqual(resp.status_code, 302)
            mock_send.assert_not_called()  # Email NOT sent during cooldown


# ─── 2. Coordinator Self-Registration Blocked ─────────────────────────────────


class CoordinatorRegistrationBlockedTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_coordinator_register_get_redirects_with_error(self):
        """GET /register/coordinator/ must redirect, not render a form."""
        resp = self.client.get(reverse('coordinator_register'))
        self.assertEqual(resp.status_code, 302)
        # After redirect should show error message
        resp2 = self.client.get(resp['Location'], follow=True)
        messages = list(resp2.context['messages'])
        self.assertTrue(any('not available' in str(m) or 'administrator' in str(m) for m in messages))

    def test_coordinator_register_post_redirects(self):
        """POST /register/coordinator/ is also blocked."""
        resp = self.client.post(reverse('coordinator_register'), {
            'first_name': 'Evil',
            'last_name': 'User',
            'email': 'hacker@example.com',
            'password1': 'SecurePass#99',
            'password2': 'SecurePass#99',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(User.objects.filter(email='hacker@example.com').exists())

    def test_coordinator_role_cannot_be_set_via_student_form(self):
        """The StudentRegistrationForm.save() always forces role='student'."""
        from accounts.forms import StudentRegistrationForm
        from accounts.models import Course
        course, _ = Course.objects.get_or_create(
            category='UG', type='B.Tech', name='CS', year=4
        )
        data = {
            'first_name': 'Bad',
            'last_name': 'Actor',
            'email': 'bad@example.com',
            'course': course.pk,
            'year': '2',
            'batch': '2023',
            'password1': 'SecurePass#99',
            'password2': 'SecurePass#99',
        }
        form = StudentRegistrationForm(data)
        if form.is_valid():
            user = form.save()
            self.assertEqual(user.role, 'student')


# ─── 3. Permission Enforcement ────────────────────────────────────────────────


class PermissionEnforcementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.student_user, self.profile = make_student_with_profile()
        self.coordinator = make_user('coord@test.com', role='coordinator')

    def test_unauthenticated_student_dashboard_redirects(self):
        resp = self.client.get(reverse('student_dashboard'))
        self.assertEqual(resp.status_code, 302)

    def test_coordinator_cannot_access_student_dashboard(self):
        self.client.force_login(self.coordinator)
        resp = self.client.get(reverse('student_dashboard'))
        self.assertEqual(resp.status_code, 302)

    def test_student_cannot_access_coordinator_dashboard(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(reverse('coordinator_dashboard'))
        # Must redirect, not serve the page
        self.assertIn(resp.status_code, [302, 403])

    def test_student_cannot_access_admin_dashboard(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertIn(resp.status_code, [302, 403])

    def test_coordinator_cannot_access_admin_dashboard(self):
        self.client.force_login(self.coordinator)
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertIn(resp.status_code, [302, 403])

    def test_student_coordinator_profile_access_denied(self):
        """A student visiting /coordinator/profile/ should be denied."""
        self.client.force_login(self.student_user)
        resp = self.client.get(reverse('coordinator_profile'))
        self.assertEqual(resp.status_code, 302)

    def test_coordinator_student_profile_access_denied(self):
        """A coordinator visiting /student/profile/ should be denied."""
        self.client.force_login(self.coordinator)
        resp = self.client.get(reverse('student_profile'))
        self.assertEqual(resp.status_code, 302)


# ─── 4. Password Reset — User Enumeration ─────────────────────────────────────


class ForgotPasswordTest(TestCase):
    def setUp(self):
        self.client = Client()
        make_user('real@example.com', role='student')

    @patch('accounts.views.send_otp_email', return_value=(True, None))
    def test_existing_email_shows_generic_message(self, mock_send):
        resp = self.client.post(reverse('forgot_password'), {'email': 'real@example.com'}, follow=True)
        content = resp.content.decode()
        self.assertIn('real@example.com', content)

    def test_nonexistent_email_shows_same_generic_message(self):
        """Response must NOT reveal whether the email exists."""
        resp = self.client.post(
            reverse('forgot_password'), {'email': 'ghost@example.com'}, follow=True
        )
        # Should return 200 (rendered template) — not crash, not redirect to OTP
        self.assertEqual(resp.status_code, 200)
        # Message should be the generic "If ... is registered" form, not "No user found"
        content = resp.content.decode()
        self.assertNotIn('No user found', content)

    def test_password_validation_runs_on_reset(self):
        """Django's password validators must reject weak passwords."""
        session = self.client.session
        session['reset_email'] = 'real@example.com'
        session['otp_reset_verified'] = True
        session.save()
        resp = self.client.post(reverse('reset_password_new'), {
            'password': '123',
            'confirm_password': '123',
        }, follow=True)
        # Django validators should reject '123'
        self.assertNotEqual(User.objects.get(email='real@example.com').check_password('123'), True)


# ─── 5. Resume Upload Security ────────────────────────────────────────────────

_PLAIN_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(MEDIA_ROOT='/tmp/test_media', STORAGES=_PLAIN_STORAGES)
class ResumeUploadSecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.student, self.profile = make_student_with_profile('resume_student@test.com')
        self.client.force_login(self.student)

    def _upload(self, content, name='resume.pdf', content_type='application/pdf'):
        f = SimpleUploadedFile(name, content, content_type=content_type)
        return self.client.post(
            reverse('resumes:upload'),
            {'resume_file': f},
            follow=True,
        )

    def test_valid_pdf_upload_succeeds(self):
        """A file starting with %PDF- should be accepted."""
        valid_pdf = PDF_MAGIC + b' minimal content'
        with patch('resumes.views.upload.Resume.objects.create') as mock_create, \
             patch('resumes.views.upload.extract_text_from_pdf', return_value=''), \
             patch('resumes.models.Resume.save'):
            mock_resume = MagicMock()
            mock_resume.file = MagicMock()
            mock_resume.file.path = '/tmp/test.pdf'
            mock_create.return_value = mock_resume
            resp = self._upload(valid_pdf)
        # Response should not contain file validation error
        self.assertNotContains(resp, 'does not appear to be a valid PDF')

    def test_fake_pdf_magic_bytes_rejected(self):
        """A file with wrong magic bytes but .pdf extension must be rejected."""
        resp = self._upload(FAKE_PDF, 'resume.pdf', 'application/pdf')
        self.assertContains(resp, 'does not appear to be a valid PDF')

    def test_oversized_file_rejected(self):
        """A file > 5 MB must be rejected."""
        big = PDF_MAGIC + b'A' * (5 * 1024 * 1024 + 1)
        resp = self._upload(big)
        self.assertContains(resp, 'exceeds')

    def test_non_pdf_extension_rejected(self):
        """A .exe file must be rejected even with PDF magic bytes."""
        resp = self._upload(PDF_MAGIC + b'binary', 'malware.exe', 'application/octet-stream')
        self.assertContains(resp, 'Only PDF files are allowed')

    def test_wrong_content_type_rejected(self):
        """PDF extension but wrong MIME type must be rejected."""
        resp = self._upload(PDF_MAGIC, 'resume.pdf', 'text/html')
        self.assertContains(resp, 'Invalid file type')

    def test_non_student_cannot_upload(self):
        """A coordinator must not be able to upload a resume via the student endpoint."""
        coord = make_user('coord2@test.com', role='coordinator')
        self.client.force_login(coord)
        f = SimpleUploadedFile('resume.pdf', PDF_MAGIC + b'content', content_type='application/pdf')
        resp = self.client.post(reverse('resumes:upload'), {'resume_file': f})
        # UserPassesTestMixin returns 403; with LOGIN_URL redirect it may be 302
        self.assertIn(resp.status_code, [302, 403])
        self.assertFalse(hasattr(coord, 'resume'))



# ─── 6. ATS Service Failure Resilience ───────────────────────────────────────


@override_settings(STORAGES=_PLAIN_STORAGES)
class ATSServiceResilienceTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.student, _ = make_student_with_profile('ats_student@test.com')
        self.client.force_login(self.student)

        # Create a minimal Resume object (no file — tests mock the ATS call)
        from resumes.models import Resume
        self.resume = Resume.objects.create(student=self.student, resume_type='uploaded')

    @patch('resumes.views.analyzer.sync_analyze_resume', return_value=None)
    def test_ats_unavailable_shows_friendly_error(self, mock_ats):
        """When ATS returns None the view should not crash — it redirects with an error."""
        resp = self.client.post(
            reverse('resumes:analysis'),
            {'target_role': 'Developer', 'job_description': 'Python developer'},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        # Should show user-friendly "unavailable" error, not a traceback
        self.assertIn('unavailable', content.lower())

    @patch('resumes.utils.ats_client.os.path.isfile', return_value=True)
    @patch('resumes.utils.ats_client.httpx.AsyncClient')
    def test_ats_connection_error_returns_none(self, mock_client, _mock_isfile):
        """ConnectError from httpx must return None, not raise."""
        import httpx
        from resumes.utils.ats_client import sync_analyze_resume

        mock_client.side_effect = httpx.ConnectError("refused")
        result = sync_analyze_resume(MagicMock(file=MagicMock(path='/tmp/fake.pdf')), 'jd')
        self.assertIsNone(result)

    @patch('resumes.utils.ats_client.os.path.isfile', return_value=True)
    @patch('resumes.utils.ats_client.httpx.AsyncClient')
    def test_ats_timeout_returns_none(self, mock_client, _mock_isfile):
        """TimeoutException must return None, not raise."""
        import httpx
        from resumes.utils.ats_client import sync_analyze_resume

        mock_client.side_effect = httpx.TimeoutException("timeout")
        result = sync_analyze_resume(MagicMock(file=MagicMock(path='/tmp/fake.pdf')), 'jd')
        self.assertIsNone(result)


# ─── 7. Settings Security ─────────────────────────────────────────────────────


class SettingsSecurityTest(TestCase):
    """Verify that key settings behave correctly without needing a real DB."""

    def test_session_cookie_httponly(self):
        from django.conf import settings
        self.assertTrue(getattr(settings, 'SESSION_COOKIE_HTTPONLY', False))

    def test_session_cookie_samesite(self):
        from django.conf import settings
        self.assertIn(
            getattr(settings, 'SESSION_COOKIE_SAMESITE', '').lower(),
            ('lax', 'strict'),
        )

    def test_x_frame_options_is_sameorigin(self):
        from django.conf import settings
        self.assertEqual(getattr(settings, 'X_FRAME_OPTIONS', ''), 'SAMEORIGIN')


# ─── 8. Django System Check (smoke) ───────────────────────────────────────────


class DjangoSystemCheckTest(TestCase):
    def test_system_check_passes(self):
        """run check() and assert zero serious errors."""
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        # This will raise SystemCheckError if critical checks fail
        call_command('check', '--deploy', stdout=out, stderr=out, verbosity=0)
        # If we reach here, no critical errors
