"""
Test the MSG file parser functionality using mocks.
"""

from classifai.infrastructure.parsing import parse_msg


class MockAttachment:
    """Mock class for MSG attachment objects."""

    def __init__(self, long_filename, short_filename):
        self.longFilename = long_filename
        self.shortFilename = short_filename


class MockMsg:
    """Mock class for extract_msg.Message objects."""

    def __init__(
        self,
        body="Test body",
        subject="Test Subject",
        sender="test@example.com",
        date="2023-07-19 10:00:00",
        to="recipient@example.com",
        cc="cc@example.com",
    ):
        self.body = body
        self.subject = subject
        self.sender = sender
        self.date = date
        self.to = to
        self.cc = cc
        self.attachments = [
            MockAttachment("attachment1.pdf", "att1.pdf"),
            MockAttachment("attachment2.docx", "att2.docx"),
        ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_parse_msg_function(mocker):
    """Test that the parse_msg function extracts content and metadata correctly."""
    # Setup the mock
    mock_msg = MockMsg()
    mocker.patch("extract_msg.openMsg", return_value=mock_msg)

    # Call the function with a dummy path
    content, metadata = parse_msg("/path/to/dummy.msg")

    # Verify that content and metadata are extracted correctly
    assert isinstance(content, str)
    assert isinstance(metadata, dict)

    # Check that content includes header information
    assert "Subject: Test Subject" in content
    assert "From: test@example.com" in content
    assert "To: recipient@example.com" in content
    assert "Date: 2023-07-19 10:00:00" in content
    assert "Test body" in content

    # Check that metadata contains expected fields
    assert metadata["subject"] == "Test Subject"
    assert metadata["sender"] == "test@example.com"
    assert metadata["date"] == "2023-07-19 10:00:00"
    assert metadata["to"] == "recipient@example.com"
    assert metadata["cc"] == "cc@example.com"
    assert "attachments" in metadata
    assert "attachment1.pdf" in metadata["attachments"]
    assert "attachment2.docx" in metadata["attachments"]


def test_parse_msg_with_empty_fields(mocker):
    """Test that the parse_msg function handles empty fields gracefully."""
    # Setup the mock with empty fields
    mock_msg = MockMsg(body="", subject="", sender="", date="", to="", cc="")
    mock_msg.attachments = []
    mocker.patch("extract_msg.openMsg", return_value=mock_msg)

    # Call the function with a dummy path
    content, metadata = parse_msg("/path/to/dummy.msg")

    # Verify that content and metadata are extracted correctly
    assert isinstance(content, str)
    assert isinstance(metadata, dict)

    # Check that metadata contains expected fields with empty values
    assert metadata["subject"] == ""
    assert metadata["sender"] == ""
    assert metadata["date"] == ""
    assert metadata["to"] == ""
    assert metadata["cc"] == ""
    assert "attachments" not in metadata
