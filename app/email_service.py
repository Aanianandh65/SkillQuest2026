import os
import smtplib
from email.message import EmailMessage


def send_student_credentials(name, email, username, password):
    """Send newly created student login credentials by SMTP.

    SMTP settings are read from environment variables so secrets are never
    hard-coded into the application.
    """
    mail_server = os.getenv("MAIL_SERVER", "").strip()
    mail_port = int(os.getenv("MAIL_PORT", "587"))
    mail_username = os.getenv("MAIL_USERNAME", "").strip()
    mail_password = os.getenv("MAIL_PASSWORD", "")
    mail_from = os.getenv("MAIL_FROM", mail_username).strip()
    use_tls = os.getenv("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")

    if not all([mail_server, mail_username, mail_password, mail_from]):
        return False, "Email service is not configured."

    msg = EmailMessage()
    msg["Subject"] = "Skill Quest 2026 - Student Login Credentials"
    msg["From"] = mail_from
    msg["To"] = email

    msg.set_content(
        f"""Dear {name},

Your Skill Quest 2026 student account has been created.

Login details:
Username: {username}
Password: {password}

Please keep these credentials confidential.

You can use the Skill Quest 2026 examination portal to log in and access your examination.

Regards,
Skill Quest 2026
EduCADD Learning Solutions Pvt Ltd
"""
    )

    msg.add_alternative(
        f"""        <html>
          <body style="font-family:Arial,sans-serif;color:#0B1F3A;">
            <div style="max-width:600px;margin:auto;padding:25px;border:1px solid #e5e8ed;border-radius:12px;">
              <h2 style="margin-top:0;">Skill Quest 2026</h2>
              <p>Dear <strong>{name}</strong>,</p>
              <p>Your student account has been created successfully.</p>
              <div style="background:#FFF8D6;padding:18px;border-radius:10px;">
                <p><strong>Username:</strong> {username}</p>
                <p><strong>Password:</strong> {password}</p>
              </div>
              <p>Please keep these credentials confidential.</p>
              <p>Regards,<br><strong>Skill Quest 2026</strong><br> EduCADD Learning Solutions Pvt Ltd</p>
            </div>
          </body>
        </html>
        """,
        subtype="html",
    )

    try:
        with smtplib.SMTP(mail_server, mail_port, timeout=20) as server:
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()
            server.login(mail_username, mail_password)
            server.send_message(msg)
        return True, "Credentials email sent successfully."
    except Exception as exc:
        return False, f"Student was registered, but the credentials email could not be sent: {exc}"
