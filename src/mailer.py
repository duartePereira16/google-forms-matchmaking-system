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

def resolve_mentor_template_path(theme_dir: str, mentee_count: int) -> str:
    """
    Resolves the appropriate mentor template path for a given theme:
    - If mentee_count > 1 and 'multi_mentor_template.html' exists in theme_dir, uses it.
    - Otherwise, falls back to 'mentor_template.html'.
    """
    if mentee_count > 1:
        multi_path = os.path.join(theme_dir, "multi_mentor_template.html")
        if os.path.exists(multi_path):
            return multi_path
    return os.path.join(theme_dir, "mentor_template.html")

def build_contact_html(contact_dict: Dict[str, str]) -> str:
    """Formats a contact dictionary into an HTML unordered list."""
    if not contact_dict:
        return "None provided"
    items = [f"<li><strong>{k}:</strong> {v}</li>" for k, v in contact_dict.items()]
    return f'<ul style="margin: 4px 0 0 0; padding-left: 20px;">{"".join(items)}</ul>'

def group_matches_by_mentor(matches: List[Match]) -> Dict[str, List[Match]]:
    """Groups matches by mentor ID, preserving all assigned mentees."""
    grouped: Dict[str, List[Match]] = {}
    for m in matches:
        grouped.setdefault(m.mentor.id, []).append(m)
    return grouped

def render_mentee_cards(mentees: List[Participant], theme_dir: Optional[str] = None) -> str:
    """
    Renders individual cards for a list of mentees using the theme's 
    'mentee_card_template.html' if available, or a clean default card.
    """
    card_template_str: Optional[str] = None
    
    if theme_dir:
        base_dir = theme_dir
        if not os.path.isdir(base_dir) and os.path.isdir(os.path.join("src/templates", base_dir)):
            base_dir = os.path.join("src/templates", base_dir)
        card_template_path = os.path.join(base_dir, "mentee_card_template.html")
        if os.path.exists(card_template_path):
            with open(card_template_path, "r", encoding="utf-8") as f:
                card_template_str = f.read()

    if not card_template_str:
        # Generic fallback if the theme does not define mentee_card_template.html
        card_template_str = (
            '<div class="mentee-card" style="background-color: #ffffff; border: 1px solid #e2e8f0; '
            'border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">\n'
            '    <div class="info-row" style="margin-bottom: 6px;"><span class="info-label" style="font-weight: 600; color: #555;">Name:</span> {{mentee_name}}</div>\n'
            '    <div class="info-row" style="margin-bottom: 0;"><span class="info-label" style="font-weight: 600; color: #555;">Contacts:</span><br>{{mentee_contact}}</div>\n'
            '</div>'
        )

    cards = []
    for mentee in mentees:
        ctx = {
            "mentee_name": mentee.name,
            "mentee_email": mentee.id,
            "mentee_contact": build_contact_html(mentee.contact_info)
        }
        rendered = card_template_str
        for k, v in ctx.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
        cards.append(rendered)

    return "".join(cards)

def build_mentor_email_context(
    mentor: Participant, 
    mentor_matches: List[Match],
    theme_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Builds the template context for a mentor. 
    Handles both single-mentee and multi-mentee assignments cleanly.
    Delegates card rendering to the theme's mentee_card_template.html sub-template.
    """
    if not mentor_matches:
        raise ValueError(f"No matches provided for mentor {mentor.id}")

    mentees = [m.mentee for m in mentor_matches]
    mentee_names = ", ".join(m.name for m in mentees)
    mentee_emails = ", ".join(m.id for m in mentees)

    mentee_cards_html = render_mentee_cards(mentees, theme_dir)

    if len(mentees) == 1:
        mentee_contact_html = build_contact_html(mentees[0].contact_info)
    else:
        mentee_contact_html = mentee_cards_html

    return {
        "mentor_name": mentor.name,
        "mentor_email": mentor.id,
        "mentor_contact": build_contact_html(mentor.contact_info),
        "mentee_name": mentee_names,
        "mentee_email": mentee_emails,
        "mentee_contact": mentee_contact_html,
        "mentee_cards": mentee_cards_html,
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
