"""
Script to create a sample .msg file for testing.
This uses the extract-msg library's ability to create MSG files.
"""

from datetime import datetime, timezone
from pathlib import Path

from extract_msg.msg_classes import Message


def create_sample_msg():
    """Create a sample .msg file for testing."""
    # Ensure the samples directory exists
    samples_dir = Path("tests/samples")
    samples_dir.mkdir(exist_ok=True, parents=True)

    # Define the output file path
    output_path = samples_dir / "sample_email.msg"

    # Create a new Message object
    msg = Message()

    # Set message properties
    msg.subject = "Test Email for ClassifAI"
    msg.sender = "test@example.com"
    msg.to = "recipient@example.com"
    msg.cc = "cc@example.com"
    msg.date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    msg.body = """
    This is a test email for ClassifAI.

    It contains some sample text that can be used to test the MSG file parser.

    The parser should extract the subject, sender, recipients, date, and body.

    Regards,
    Test User
    """

    # Save the message to a file
    msg.save(output_path)
    # Created sample MSG file at: {output_path}


if __name__ == "__main__":
    create_sample_msg()
