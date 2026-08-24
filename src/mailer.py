import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def format_template(template_path: str, context: dict) -> str:
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return f"Template not found: {template_path}"
    
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        content = content.replace(placeholder, str(value))
    return content

def send_email(to_email: str, subject: str, html_body: str, sender_email: str, sender_password: str):
    if not sender_email or not sender_password:
        raise ValueError("Email credentials not provided.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    part = MIMEText(html_body, "html")
    msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
    except Exception as e:
        raise RuntimeError(f"Failed to send email to {to_email}: {str(e)}")
