import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
from src.models import Match, Participant

def format_template(template_path: str, context: Dict[str, Any]) -> str:
    """
    Renders an HTML template by replacing {{key}} tokens with context values.
    
    Raises:
        FileNotFoundError: If the specified template_path does not exist.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found at: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        content = content.replace(placeholder, str(value))
    return content

def build_contact_html(contact_dict: Dict[str, str]) -> str:
    """Formats a contact dictionary into an HTML unordered list."""
    if not contact_dict:
        return "None provided"
    items = [f"<li><strong>{k}:</strong> {v}</li>" for k, v in contact_dict.items()]
    return f"<ul>{''.join(items)}</ul>"

def group_matches_by_mentor(matches: List[Match]) -> Dict[str, List[Match]]:
    """Groups matches by mentor ID, preserving all assigned mentees."""
    grouped: Dict[str, List[Match]] = {}
    for m in matches:
        grouped.setdefault(m.mentor.id, []).append(m)
    return grouped

def build_mentor_email_context(mentor: Participant, mentor_matches: List[Match]) -> Dict[str, Any]:
    """
    Builds the template context for a mentor. 
    Handles both single-mentee and multi-mentee assignments cleanly.
    """
    if not mentor_matches:
        raise ValueError(f"No matches provided for mentor {mentor.id}")

    mentees = [m.mentee for m in mentor_matches]
    mentee_names = ", ".join(m.name for m in mentees)
    mentee_emails = ", ".join(m.id for m in mentees)

    if len(mentees) == 1:
        mentee_contact_html = build_contact_html(mentees[0].contact_info)
    else:
        # Structure multi-mentee contacts with clear visual separation
        blocks = []
        for mentee in mentees:
            contact_details = build_contact_html(mentee.contact_info)
            blocks.append(
                f'<div style="margin-bottom: 12px; padding: 10px; border-left: 4px solid #0869e9; background-color: #f8f9fa; border-radius: 4px;">'
                f'<strong>{mentee.name}</strong> ({mentee.id})<br>{contact_details}'
                f'</div>'
            )
        mentee_contact_html = "".join(blocks)

    return {
        "mentor_name": mentor.name,
        "mentor_email": mentor.id,
        "mentor_contact": build_contact_html(mentor.contact_info),
        "mentee_name": mentee_names,
        "mentee_email": mentee_emails,
        "mentee_contact": mentee_contact_html,
        "mentee_count": len(mentees),
    }

def build_mentee_email_context(match: Match) -> Dict[str, Any]:
    """Builds the template context for a mentee."""
    return {
        "mentor_name": match.mentor.name,
        "mentor_email": match.mentor.id,
        "mentor_contact": build_contact_html(match.mentor.contact_info),
        "mentee_name": match.mentee.name,
        "mentee_email": match.mentee.id,
        "mentee_contact": build_contact_html(match.mentee.contact_info),
    }

class EmailDispatcher:
    """
    Manages an authenticated SMTP session to send multiple emails efficiently
    without reconnecting and re-authenticating for each message.
    """
    def __init__(
        self,
        sender_email: str,
        sender_password: str,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 465,
        use_ssl: bool = True
    ) -> None:
        if not sender_email or not sender_password:
            raise ValueError("Sender email and password must be provided.")
            
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.use_ssl = use_ssl
        self.server: Optional[smtplib.SMTP] = None

    def connect(self) -> "EmailDispatcher":
        """Establishes connection and logs in to the SMTP server."""
        try:
            if self.use_ssl:
                self.server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                self.server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                self.server.starttls()
            
            self.server.login(self.sender_email, self.sender_password)
            return self
        except Exception as e:
            self.close()
            raise RuntimeError(f"Failed to connect and authenticate to {self.smtp_host}:{self.smtp_port}: {e}")

    def send_email(self, to_email: str, subject: str, html_body: str) -> None:
        """Sends an HTML email over the active SMTP connection."""
        if not self.server:
            raise RuntimeError("SMTP connection is not active. Use within a 'with' block or call connect() first.")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = to_email

        part = MIMEText(html_body, "html", "utf-8")
        msg.attach(part)

        try:
            self.server.sendmail(self.sender_email, to_email, msg.as_string())
        except Exception as e:
            raise RuntimeError(f"Failed to send email to {to_email}: {e}")

    def close(self) -> None:
        """Safely closes the SMTP connection."""
        if self.server:
            try:
                self.server.quit()
            except Exception:
                pass
            finally:
                self.server = None

    def __enter__(self) -> "EmailDispatcher":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

def send_email(
    to_email: str, 
    subject: str, 
    html_body: str, 
    sender_email: str, 
    sender_password: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 465
) -> None:
    """
    Convenience function to send a single email. 
    For bulk sending, prefer using EmailDispatcher as a context manager.
    """
    with EmailDispatcher(sender_email, sender_password, smtp_host=smtp_host, smtp_port=smtp_port) as dispatcher:
        dispatcher.send_email(to_email, subject, html_body)
