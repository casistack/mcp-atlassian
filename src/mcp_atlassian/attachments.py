import logging
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional, Union

# Configure logging
logger = logging.getLogger("mcp-atlassian")


@dataclass
class AttachmentInfo:
    """Information about an attachment."""

    filename: str
    content_type: str
    size: int
    url: str
    id: str
    created: str
    creator: Optional[str] = None


class AttachmentHandler:
    """Common functionality for handling attachments."""

    @staticmethod
    def get_content_type(filename: str) -> str:
        """Get the content type of a file based on its extension."""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    @staticmethod
    def get_file_size(file: Union[str, Path, BinaryIO]) -> int:
        """Get the size of a file in bytes."""
        if isinstance(file, (str, Path)):
            return os.path.getsize(file)
        elif hasattr(file, "seek") and hasattr(file, "tell"):
            current_pos = file.tell()
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(current_pos)
            return size
        else:
            raise ValueError("Unsupported file type")

    @staticmethod
    def validate_file(
        file: Union[str, Path, BinaryIO], max_size: int = 10 * 1024 * 1024
    ) -> bool:
        """Validate file size and type.

        Args:
            file: The file to validate
            max_size: Maximum allowed file size in bytes (default: 10MB)

        Returns:
            bool: Whether the file is valid
        """
        try:
            size = AttachmentHandler.get_file_size(file)
            if size > max_size:
                logger.error(
                    f"File size {size} bytes exceeds maximum allowed size of {max_size} bytes"
                )
                return False

            if isinstance(file, (str, Path)):
                content_type = AttachmentHandler.get_content_type(str(file))
                if not content_type:
                    logger.error(f"Could not determine content type for file {file}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error validating file: {e}")
            return False

    @staticmethod
    def open_file(file: Union[str, Path, BinaryIO]) -> BinaryIO:
        """Open a file for reading in binary mode."""
        if isinstance(file, (str, Path)):
            return open(file, "rb")
        return file

    @staticmethod
    def format_attachment_info(
        attachment: dict, base_url: str, space_or_project_key: str
    ) -> AttachmentInfo:
        """Format attachment information into a common structure.

        Args:
            attachment: Raw attachment data from Confluence or Jira
            base_url: Base URL of the Confluence/Jira instance
            space_or_project_key: Space key for Confluence or project key for Jira

        Returns:
            AttachmentInfo object with formatted data
        """
        return AttachmentInfo(
            filename=attachment.get("filename", ""),
            content_type=attachment.get("mimeType", attachment.get("contentType", "")),
            size=attachment.get("size", 0),
            url=f"{base_url.rstrip('/')}/secure/attachment/{attachment.get('id', '')}",
            id=str(attachment.get("id", "")),
            created=attachment.get("created", ""),
            creator=attachment.get("author", {}).get("displayName", None),
        )
