import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch
from mcp_atlassian.attachments import AttachmentHandler, AttachmentInfo


class TestAttachmentHandler:
    def test_get_content_type(self):
        """Test getting content type from filename."""
        # Test common file types
        assert AttachmentHandler.get_content_type("test.txt") == "text/plain"
        assert AttachmentHandler.get_content_type("image.png") == "image/png"
        assert AttachmentHandler.get_content_type("doc.pdf") == "application/pdf"

        # Test unknown file type
        assert (
            AttachmentHandler.get_content_type("unknown") == "application/octet-stream"
        )

    def test_get_file_size_path(self, tmp_path):
        """Test getting file size from path."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        size = AttachmentHandler.get_file_size(test_file)
        assert size == len("test content")

    def test_get_file_size_file_object(self):
        """Test getting file size from file object."""
        content = b"test content"
        mock_file = MagicMock()
        mock_file.tell.side_effect = [
            0,
            len(content),
            0,
        ]  # Initial pos, end pos, back to initial

        size = AttachmentHandler.get_file_size(mock_file)
        assert size == len(content)
        assert mock_file.seek.call_count == 2  # Called to seek end and back to start

    def test_get_file_size_invalid(self):
        """Test getting file size with invalid input."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            AttachmentHandler.get_file_size(123)

    def test_validate_file_size_valid(self, tmp_path):
        """Test validating file with valid size."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Test with default max size (10MB)
        assert AttachmentHandler.validate_file(test_file) is True

        # Test with custom max size
        assert AttachmentHandler.validate_file(test_file, max_size=1024) is True

    def test_validate_file_size_invalid(self, tmp_path):
        """Test validating file with invalid size."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Test with very small max size
        assert AttachmentHandler.validate_file(test_file, max_size=1) is False

    def test_validate_file_type_invalid(self, tmp_path):
        """Test validating file with invalid type."""
        # Create a test file without extension
        test_file = tmp_path / "testfile"
        test_file.write_text("test content")

        # Should still return True as application/octet-stream is used as fallback
        assert AttachmentHandler.validate_file(test_file) is True

    def test_open_file_path(self, tmp_path):
        """Test opening file from path."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with AttachmentHandler.open_file(test_file) as f:
            content = f.read()
            assert content == b"test content"

    def test_open_file_file_object(self):
        """Test opening file from file object."""
        file_obj = MagicMock()
        result = AttachmentHandler.open_file(file_obj)
        assert result == file_obj

    def test_format_attachment_info(self):
        """Test formatting attachment information."""
        attachment_data = {
            "filename": "test.txt",
            "mimeType": "text/plain",
            "size": 1024,
            "id": "123",
            "created": "2024-01-09T12:00:00Z",
            "author": {"displayName": "Test User"},
        }

        base_url = "https://test.atlassian.net"
        space_key = "TEST"

        info = AttachmentHandler.format_attachment_info(
            attachment_data, base_url, space_key
        )

        assert isinstance(info, AttachmentInfo)
        assert info.filename == "test.txt"
        assert info.content_type == "text/plain"
        assert info.size == 1024
        assert info.url == "https://test.atlassian.net/secure/attachment/123"
        assert info.id == "123"
        assert info.created == "2024-01-09T12:00:00Z"
        assert info.creator == "Test User"

    def test_format_attachment_info_minimal(self):
        """Test formatting attachment information with minimal data."""
        attachment_data = {"id": "123"}

        base_url = "https://test.atlassian.net"
        space_key = "TEST"

        info = AttachmentHandler.format_attachment_info(
            attachment_data, base_url, space_key
        )

        assert isinstance(info, AttachmentInfo)
        assert info.filename == ""
        assert info.content_type == ""
        assert info.size == 0
        assert info.url == "https://test.atlassian.net/secure/attachment/123"
        assert info.id == "123"
        assert info.created == ""
        assert info.creator is None

    def test_format_attachment_info_jira_content_type(self):
        """Test formatting attachment information with Jira-style content type."""
        attachment_data = {
            "filename": "test.txt",
            "contentType": "text/plain",  # Jira uses contentType instead of mimeType
            "size": 1024,
            "id": "123",
            "created": "2024-01-09T12:00:00Z",
        }

        base_url = "https://test.atlassian.net"
        space_key = "TEST"

        info = AttachmentHandler.format_attachment_info(
            attachment_data, base_url, space_key
        )

        assert isinstance(info, AttachmentInfo)
        assert info.content_type == "text/plain"

    def test_attachment_info_initialization(self):
        info = AttachmentInfo(
            filename="test.txt",
            content_type="text/plain",
            size=100,
            url="http://example.com",
            id="123",
            created="2023-01-01",
            creator="testuser",
            container={"key": "TEAM"},
        )
        assert info.filename == "test.txt"
        assert info.content_type == "text/plain"
        assert info.size == 100
        assert info.url == "http://example.com"
        assert info.id == "123"
        assert info.created == "2023-01-01"
        assert info.creator == "testuser"
        assert info.container["key"] == "TEAM"
