import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from src.mailer import format_template, EmailDispatcher, send_email

def test_format_template_successful_replacement():
    """Verify template placeholders are accurately replaced with context values."""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".html") as tf:
        tf.write("Hello {{name}}, your mentor is {{mentor}}!")
        tf_path = tf.name

    try:
        rendered = format_template(tf_path, {"name": "Alice", "mentor": "Bob"})
        assert rendered == "Hello Alice, your mentor is Bob!"
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)

def test_format_template_raises_when_missing():
    """Verify FileNotFoundError is raised when the template file is absent."""
    with pytest.raises(FileNotFoundError, match="Template file not found at"):
        format_template("non_existent_template_path.html", {"name": "Alice"})

def test_email_dispatcher_missing_credentials():
    """Verify ValueError is raised when credentials are not supplied."""
    with pytest.raises(ValueError, match="Sender email and password must be provided"):
        EmailDispatcher("", "")

@patch("smtplib.SMTP_SSL")
def test_email_dispatcher_single_login_for_multiple_sends(mock_smtp_ssl):
    """Verify that EmailDispatcher logs in once and reuses connection across multiple sends."""
    mock_server = MagicMock()
    mock_smtp_ssl.return_value = mock_server

    sender = "test@example.com"
    password = "secretpassword"

    with EmailDispatcher(sender, password, smtp_host="smtp.gmail.com", smtp_port=465) as dispatcher:
        dispatcher.send_email("student1@example.com", "Subject 1", "<p>Hello 1</p>")
        dispatcher.send_email("student2@example.com", "Subject 2", "<p>Hello 2</p>")
        dispatcher.send_email("student3@example.com", "Subject 3", "<p>Hello 3</p>")

    # Assert single connection and single login
    mock_smtp_ssl.assert_called_once_with("smtp.gmail.com", 465)
    mock_server.login.assert_called_once_with(sender, password)

    # Assert 3 emails sent
    assert mock_server.sendmail.call_count == 3
    # Assert connection closed
    mock_server.quit.assert_called_once()

@patch("smtplib.SMTP_SSL")
def test_send_email_convenience_function(mock_smtp_ssl):
    """Verify the backward-compatible send_email function works as expected."""
    mock_server = MagicMock()
    mock_smtp_ssl.return_value = mock_server

    send_email(
        to_email="recipient@example.com",
        subject="Test Subject",
        html_body="<p>Test Body</p>",
        sender_email="sender@example.com",
        sender_password="secretpassword"
    )

    mock_server.login.assert_called_once_with("sender@example.com", "secretpassword")
    mock_server.sendmail.assert_called_once()
    mock_server.quit.assert_called_once()

