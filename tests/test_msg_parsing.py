from classifai.infrastructure.parsing import parse_msg


def test_parse_msg_success(mocker):
    # Mock the extract_msg.openMsg function
    mock_open_msg = mocker.patch("extract_msg.openMsg")
    # Arrange
    mock_msg = mocker.MagicMock()
    mock_msg.body = "This is the body of the email."
    mock_msg.subject = "Test Subject"
    mock_msg.sender = "sender@example.com"
    mock_msg.to = "recipient@example.com"
    mock_msg.date = "2023-01-01"
    mock_msg.cc = ""
    mock_msg.attachments = []
    mock_open_msg.return_value.__enter__.return_value = mock_msg

    file_path = "dummy.msg"

    # Act
    content, metadata = parse_msg(file_path)

    # Assert
    expected_header = (
        "Subject: Test Subject\nFrom: sender@example.com\nTo: recipient@example.com\nDate: 2023-01-01\n\n"
    )
    expected_content = expected_header + "This is the body of the email."
    assert content == expected_content

    expected_metadata = {
        "subject": "Test Subject",
        "sender": "sender@example.com",
        "to": "recipient@example.com",
        "date": "2023-01-01",
        "cc": "",
    }
    assert metadata == expected_metadata
    mock_open_msg.assert_called_once_with(file_path)


def test_parse_msg_failure(mocker):
    # Mock the extract_msg.openMsg function with exception
    mock_open_msg = mocker.patch("extract_msg.openMsg", side_effect=Exception("Test error"))
    # Arrange
    file_path = "dummy.msg"

    # Act
    content, metadata = parse_msg(file_path)

    # Assert
    assert content == ""
    assert metadata == {}
    mock_open_msg.assert_called_once_with(file_path)
