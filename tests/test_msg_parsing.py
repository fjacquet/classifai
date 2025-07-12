import unittest
from unittest.mock import MagicMock, patch

from classifai.infrastructure.parsing import parse_msg


class TestMsgParsing(unittest.TestCase):
    @patch("extract_msg.openMsg")
    def test_parse_msg_success(self, mock_openMsg):
        # Arrange
        mock_msg = MagicMock()
        mock_msg.body = "This is the body of the email."
        mock_openMsg.return_value.__enter__.return_value = mock_msg

        file_path = "dummy.msg"

        # Act
        content, metadata = parse_msg(file_path)

        # Assert
        self.assertEqual(content, "This is the body of the email.")
        self.assertEqual(metadata, {})
        mock_openMsg.assert_called_once_with(file_path)

    @patch("extract_msg.openMsg", side_effect=Exception("Test error"))
    def test_parse_msg_failure(self, mock_openMsg):
        # Arrange
        file_path = "dummy.msg"

        # Act
        content, metadata = parse_msg(file_path)

        # Assert
        self.assertEqual(content, "")
        self.assertEqual(metadata, {})
        mock_openMsg.assert_called_once_with(file_path)


if __name__ == "__main__":
    unittest.main()
