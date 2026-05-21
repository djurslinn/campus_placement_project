import random
import string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def generate_otp(length=6):
    """Generate a random 6-digit numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(email, otp_code, purpose):
    """
    Send OTP to the specified email via SMTP.

    Returns:
        (True, None)        — email sent successfully
        (True, otp_code)    — dev-mode fallback (no real email sent, OTP returned for display)
        (False, None)       — sending failed
    """
    if purpose == 'registration':
        subject = "Your Registration OTP – Campus Placement Training System"
        heading = "Verify Your Account"
        body_line = "Use the code below to complete your registration:"
    else:
        subject = "Password Reset OTP – Campus Placement Training System"
        heading = "Reset Your Password"
        body_line = "Use the code below to reset your password. If you did not request this, ignore this email."

    plain_text = f"{heading}\n\n{body_line}\n\nOTP: {otp_code}\n\nThis code is valid for 10 minutes."

    html_content = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 480px; margin: 0 auto;
                background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 32px 40px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 22px; letter-spacing: -0.3px;">{heading}</h1>
            <p style="color: rgba(255,255,255,0.80); margin: 6px 0 0; font-size: 14px;">Campus Placement Training System</p>
        </div>
        <div style="padding: 36px 40px; text-align: center;">
            <p style="color: #475569; font-size: 15px; margin: 0 0 24px;">{body_line}</p>
            <div style="display: inline-block; background: #f1f5f9; border: 2px dashed #667eea;
                        border-radius: 12px; padding: 18px 40px; margin-bottom: 24px;">
                <span style="font-size: 36px; font-weight: 800; letter-spacing: 10px;
                             color: #1e293b; font-family: 'Courier New', monospace;">{otp_code}</span>
            </div>
            <p style="color: #94a3b8; font-size: 13px; margin: 0;">
                This code expires in <strong>10 minutes</strong>. Do not share it with anyone.
            </p>
        </div>
        <div style="background: #f8fafc; padding: 18px 40px; text-align: center;
                    border-top: 1px solid #e2e8f0;">
            <p style="color: #cbd5e1; font-size: 12px; margin: 0;">
                &copy; 2024 Campus Placement Training System
            </p>
        </div>
    </div>
    """

    host_user = getattr(settings, 'EMAIL_HOST_USER', '')
    host_pass = getattr(settings, 'EMAIL_HOST_PASSWORD', '')

    # ── Dev-mode fallback ──────────────────────────────────────────────────────
    # If credentials are missing or still have the placeholder text, skip SMTP
    # and return the OTP so the view can display it directly on screen.
    is_placeholder = (
        not host_user or not host_pass
        or 'your_' in host_user.lower()
        or 'your_' in host_pass.lower()
    )

    if is_placeholder:
        if getattr(settings, 'DEBUG', False):
            print("\n" + "=" * 60)
            print("[DEV MODE] OTP EMAIL — not actually sent via SMTP")
            print(f"  To      : {email}")
            print(f"  Purpose : {purpose}")
            print(f"  OTP     : {otp_code}")
            print("=" * 60 + "\n")
            # Return the OTP so the view can show it on the page
            return True, otp_code
        return False, None

    # ── Real SMTP send ─────────────────────────────────────────────────────────
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', f'Campus Placement Training System <{host_user}>')
    try:
        msg = EmailMultiAlternatives(subject, plain_text, from_email, [email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True, None          # sent — no need to expose OTP on screen
    except Exception as e:
        print(f"[OTP EMAIL ERROR] {e}")
        return False, None
