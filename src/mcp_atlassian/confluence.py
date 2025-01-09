import logging
import os
from typing import Optional
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

from atlassian import Confluence
from dotenv import load_dotenv

from .config import ConfluenceConfig
from .preprocessing import TextPreprocessor
from .types import Document
from .attachments import AttachmentHandler, AttachmentInfo

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("mcp-atlassian")


class ConfluenceFetcher:
    """Handles fetching and parsing content from Confluence."""

    def __init__(self):
        url = os.getenv("CONFLUENCE_URL")
        username = os.getenv("CONFLUENCE_USERNAME")
        token = os.getenv("CONFLUENCE_API_TOKEN")

        if not all([url, username, token]):
            raise ValueError("Missing required Confluence environment variables")

        self.config = ConfluenceConfig(url=url, username=username, api_token=token)
        self.confluence = Confluence(
            url=self.config.url,
            username=self.config.username,
            password=self.config.api_token,  # API token is used as password
            cloud=True,
        )
        self.preprocessor = TextPreprocessor(self.config.url, self.confluence)

    def _process_html_content(
        self, html_content: str, space_key: str
    ) -> tuple[str, str]:
        return self.preprocessor.process_html_content(html_content, space_key)

    def get_spaces(self, start: int = 0, limit: int = 10):
        """Get all available spaces."""
        return self.confluence.get_all_spaces(start=start, limit=limit)

    def get_page_content(self, page_id: str, clean_html: bool = True) -> Document:
        """Get content of a specific page."""
        page = self.confluence.get_page_by_id(
            page_id=page_id, expand="body.storage,version,space"
        )
        space_key = page.get("space", {}).get("key", "")

        content = page["body"]["storage"]["value"]
        processed_html, processed_markdown = self._process_html_content(
            content, space_key
        )

        # Get author information from version
        version = page.get("version", {})
        author = version.get("by", {})

        metadata = {
            "page_id": page_id,
            "title": page["title"],
            "version": version.get("number"),
            "url": f"{self.config.url}/wiki/spaces/{space_key}/pages/{page_id}",
            "space_key": space_key,
            "author_name": author.get("displayName"),
            "space_name": page.get("space", {}).get("name", ""),
            "last_modified": version.get("when"),
        }

        return Document(
            page_content=processed_markdown if clean_html else processed_html,
            metadata=metadata,
        )

    def get_page_by_title(
        self, space_key: str, title: str, clean_html: bool = True
    ) -> Optional[Document]:
        """Get page content by space key and title."""
        try:
            page = self.confluence.get_page_by_title(
                space=space_key, title=title, expand="body.storage,version"
            )

            if not page:
                return None

            content = page["body"]["storage"]["value"]
            if clean_html:
                content = self._clean_html_content(content)

            metadata = {
                "page_id": page["id"],
                "title": page["title"],
                "version": page.get("version", {}).get("number"),
                "space_key": space_key,
                "url": f"{self.config.url}/wiki/spaces/{space_key}/pages/{page['id']}",
            }

            return Document(page_content=content, metadata=metadata)

        except Exception as e:
            logger.error(f"Error fetching page: {str(e)}")
            return None

    def get_space_pages(
        self, space_key: str, start: int = 0, limit: int = 10, clean_html: bool = True
    ) -> list[Document]:
        """Get all pages from a specific space."""
        pages = self.confluence.get_all_pages_from_space(
            space=space_key, start=start, limit=limit, expand="body.storage"
        )

        documents = []
        for page in pages:
            content = page["body"]["storage"]["value"]
            if clean_html:
                content = self._clean_html_content(content)

            metadata = {
                "page_id": page["id"],
                "title": page["title"],
                "space_key": space_key,
                "version": page.get("version", {}).get("number"),
                "url": f"{self.config.url}/wiki/spaces/{space_key}/pages/{page['id']}",
            }

            documents.append(Document(page_content=content, metadata=metadata))

        return documents

    def get_page_comments(
        self, page_id: str, clean_html: bool = True
    ) -> list[Document]:
        """Get all comments for a specific page."""
        page = self.confluence.get_page_by_id(page_id=page_id, expand="space")
        space_key = page.get("space", {}).get("key", "")
        space_name = page.get("space", {}).get("name", "")

        comments = self.confluence.get_page_comments(
            content_id=page_id, expand="body.view.value,version", depth="all"
        )["results"]

        comment_documents = []
        for comment in comments:
            body = comment["body"]["view"]["value"]
            processed_html, processed_markdown = self._process_html_content(
                body, space_key
            )

            # Get author information from version.by instead of author
            author = comment.get("version", {}).get("by", {})

            metadata = {
                "page_id": page_id,
                "comment_id": comment["id"],
                "last_modified": comment.get("version", {}).get("when"),
                "type": "comment",
                "author_name": author.get("displayName"),
                "space_key": space_key,
                "space_name": space_name,
            }

            comment_documents.append(
                Document(
                    page_content=processed_markdown if clean_html else processed_html,
                    metadata=metadata,
                )
            )

        return comment_documents

    def search(self, cql: str, limit: int = 10) -> list[Document]:
        """Search Confluence content using CQL."""
        try:
            results = self.confluence.cql(cql, limit=limit)
            documents = []
            for result in results.get("results", []):
                content = result.get("content", {})
                if content and content.get("type") == "page":
                    doc = self.get_page_content(content.get("id"))
                    if doc:
                        documents.append(doc)
            return documents
        except Exception as e:
            logger.error(f"Error searching Confluence: {e}")
            return []

    def create_page(
        self,
        space_key: str,
        title: str,
        body: str,
        parent_id: Optional[str] = None,
        representation: str = "storage",
    ) -> Optional[Document]:
        """Create a new Confluence page.

        Args:
            space_key: The key of the space where the page will be created
            title: The title of the new page
            body: The content of the page
            parent_id: Optional ID of the parent page
            representation: Content representation ('storage' for wiki markup, 'editor' for rich text)

        Returns:
            Document object if creation successful, None otherwise
        """
        try:
            page = self.confluence.create_page(
                space=space_key,
                title=title,
                body=body,
                parent_id=parent_id,
                representation=representation,
            )
            if page and page.get("id"):
                return self.get_page_content(page["id"])
            return None
        except Exception as e:
            logger.error(f"Error creating Confluence page: {e}")
            return None

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        representation: str = "storage",
        minor_edit: bool = False,
    ) -> Optional[Document]:
        """Update an existing Confluence page.

        Args:
            page_id: The ID of the page to update
            title: The new title of the page
            body: The new content of the page
            representation: Content representation ('storage' for wiki markup, 'editor' for rich text)
            minor_edit: Whether this is a minor edit (affects notifications and version history)

        Returns:
            Updated Document object if successful, None otherwise
        """
        try:
            # Get current version number
            current_page = self.confluence.get_page_by_id(
                page_id=page_id, expand="version"
            )
            if not current_page:
                logger.error(f"Page {page_id} not found")
                return None

            version = current_page["version"]["number"]

            # Update the page
            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=title,
                body=body,
                representation=representation,
                minor_edit=minor_edit,
                version_number=version + 1,
            )

            if updated_page and updated_page.get("id"):
                return self.get_page_content(updated_page["id"])
            return None
        except Exception as e:
            logger.error(f"Error updating Confluence page: {e}")
            return None

    def update_page_section(
        self,
        page_id: str,
        heading: str,
        new_content: str,
        minor_edit: bool = False,
    ) -> Optional[Document]:
        """Update a specific section of a Confluence page.

        Args:
            page_id: The ID of the page to update
            heading: The heading text that identifies the section
            new_content: The new content for the section
            minor_edit: Whether this is a minor edit

        Returns:
            Updated Document object if successful, None otherwise
        """
        try:
            # Get current page content
            current_page = self.confluence.get_page_by_id(
                page_id=page_id, expand="body.storage,version"
            )
            if not current_page:
                logger.error(f"Page {page_id} not found")
                return None

            current_content = current_page["body"]["storage"]["value"]
            version = current_page["version"]["number"]

            # Update the specific section
            from .content import ContentEditor

            updated_content = ContentEditor.replace_section(
                current_content, heading, new_content
            )

            # Update the page
            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=current_page["title"],
                body=updated_content,
                representation="storage",
                minor_edit=minor_edit,
                version_number=version + 1,
            )

            if updated_page and updated_page.get("id"):
                return self.get_page_content(updated_page["id"])
            return None

        except Exception as e:
            logger.error(f"Error updating page section: {e}")
            return None

    def insert_after_section(
        self,
        page_id: str,
        heading: str,
        new_content: str,
        minor_edit: bool = False,
    ) -> Optional[Document]:
        """Insert content after a specific section in a Confluence page.

        Args:
            page_id: The ID of the page to update
            heading: The heading text after which to insert content
            new_content: The content to insert
            minor_edit: Whether this is a minor edit

        Returns:
            Updated Document object if successful, None otherwise
        """
        try:
            current_page = self.confluence.get_page_by_id(
                page_id=page_id, expand="body.storage,version"
            )
            if not current_page:
                logger.error(f"Page {page_id} not found")
                return None

            current_content = current_page["body"]["storage"]["value"]
            version = current_page["version"]["number"]

            from .content import ContentEditor

            updated_content = ContentEditor.insert_after_heading(
                current_content, heading, new_content
            )

            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=current_page["title"],
                body=updated_content,
                representation="storage",
                minor_edit=minor_edit,
                version_number=version + 1,
            )

            if updated_page and updated_page.get("id"):
                return self.get_page_content(updated_page["id"])
            return None

        except Exception as e:
            logger.error(f"Error inserting content: {e}")
            return None

    def append_to_list_in_section(
        self,
        page_id: str,
        heading: str,
        list_marker: str,
        new_item: str,
        minor_edit: bool = False,
    ) -> Optional[Document]:
        """Append an item to a list in a specific section.

        Args:
            page_id: The ID of the page to update
            heading: The heading text that identifies the section
            list_marker: The marker that identifies the list ('*' for bullet, '#' for numbered)
            new_item: The new list item to append
            minor_edit: Whether this is a minor edit

        Returns:
            Updated Document object if successful, None otherwise
        """
        try:
            current_page = self.confluence.get_page_by_id(
                page_id=page_id, expand="body.storage,version"
            )
            if not current_page:
                logger.error(f"Page {page_id} not found")
                return None

            current_content = current_page["body"]["storage"]["value"]
            version = current_page["version"]["number"]

            from .content import ContentEditor

            start, end = ContentEditor.find_section(current_content, heading)
            if start == -1:
                logger.error(f"Section with heading '{heading}' not found")
                return None

            section_content = current_content[start:end]
            updated_section = ContentEditor.append_to_list(
                section_content, list_marker, new_item
            )
            updated_content = (
                current_content[:start] + updated_section + current_content[end:]
            )

            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=current_page["title"],
                body=updated_content,
                representation="storage",
                minor_edit=minor_edit,
                version_number=version + 1,
            )

            if updated_page and updated_page.get("id"):
                return self.get_page_content(updated_page["id"])
            return None

        except Exception as e:
            logger.error(f"Error appending to list: {e}")
            return None

    def update_table_in_section(
        self,
        page_id: str,
        heading: str,
        table_start: str,
        row_identifier: str,
        new_values: list[str],
        minor_edit: bool = False,
    ) -> Optional[Document]:
        """Update a specific row in a table within a section.

        Args:
            page_id: The ID of the page to update
            heading: The heading text that identifies the section
            table_start: Text that uniquely identifies the table
            row_identifier: Text that uniquely identifies the row to update
            new_values: New values for the row cells
            minor_edit: Whether this is a minor edit

        Returns:
            Updated Document object if successful, None otherwise
        """
        try:
            current_page = self.confluence.get_page_by_id(
                page_id=page_id, expand="body.storage,version"
            )
            if not current_page:
                logger.error(f"Page {page_id} not found")
                return None

            current_content = current_page["body"]["storage"]["value"]
            version = current_page["version"]["number"]

            from .content import ContentEditor

            start, end = ContentEditor.find_section(current_content, heading)
            if start == -1:
                logger.error(f"Section with heading '{heading}' not found")
                return None

            section_content = current_content[start:end]
            updated_section = ContentEditor.update_table_row(
                section_content, table_start, row_identifier, new_values
            )
            updated_content = (
                current_content[:start] + updated_section + current_content[end:]
            )

            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=current_page["title"],
                body=updated_content,
                representation="storage",
                minor_edit=minor_edit,
                version_number=version + 1,
            )

            if updated_page and updated_page.get("id"):
                return self.get_page_content(updated_page["id"])
            return None

        except Exception as e:
            logger.error(f"Error updating table: {e}")
            return None

    def get_attachments(self, page_id: str) -> list[AttachmentInfo]:
        """Get all attachments for a specific page.

        Args:
            page_id: The ID of the page

        Returns:
            List of AttachmentInfo objects
        """
        try:
            attachments = self.confluence.get_attachments_from_content(page_id)
            return [
                AttachmentHandler.format_attachment_info(
                    attachment,
                    self.config.url,
                    attachment.get("container", {}).get("key", ""),
                )
                for attachment in attachments.get("results", [])
            ]
        except Exception as e:
            logger.error(f"Error getting attachments: {e}")
            return []

    def get_attachment_content(self, attachment_id: str) -> Optional[bytes]:
        """Get the content of a specific attachment.

        Args:
            attachment_id: The ID of the attachment

        Returns:
            Attachment content as bytes if successful, None otherwise
        """
        try:
            return self.confluence.get_attachment_by_id(attachment_id, expand="content")
        except Exception as e:
            logger.error(f"Error getting attachment content: {e}")
            return None

    def add_attachment(
        self,
        page_id: str,
        file: Union[str, Path, BinaryIO],
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[AttachmentInfo]:
        """Add an attachment to a page.

        Args:
            page_id: The ID of the page to attach to
            file: The file to attach (path or file-like object)
            filename: Optional filename (required if file is a file-like object)
            content_type: Optional content type (will be guessed if not provided)

        Returns:
            AttachmentInfo if successful, None otherwise
        """
        try:
            # Validate inputs
            if isinstance(file, (str, Path)):
                file_path = str(file)
                filename = filename or os.path.basename(file_path)
                content_type = content_type or AttachmentHandler.get_content_type(
                    file_path
                )
            elif not filename:
                raise ValueError(
                    "Filename must be provided when using file-like object"
                )

            # Validate file
            if not AttachmentHandler.validate_file(file):
                return None

            # Open file if needed
            with AttachmentHandler.open_file(file) as f:
                # Upload attachment
                result = self.confluence.attach_file(
                    content=f, name=filename, content_type=content_type, page_id=page_id
                )

                if result and "id" in result:
                    # Get space key for the page
                    page = self.confluence.get_page_by_id(page_id, expand="space")
                    space_key = page.get("space", {}).get("key", "")

                    return AttachmentHandler.format_attachment_info(
                        result, self.config.url, space_key
                    )

            return None

        except Exception as e:
            logger.error(f"Error adding attachment: {e}")
            return None

    def update_attachment(
        self,
        attachment_id: str,
        file: Union[str, Path, BinaryIO],
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[AttachmentInfo]:
        """Update an existing attachment.

        Args:
            attachment_id: The ID of the attachment to update
            file: The new file content (path or file-like object)
            filename: Optional new filename (required if file is a file-like object)
            content_type: Optional new content type (will be guessed if not provided)

        Returns:
            Updated AttachmentInfo if successful, None otherwise
        """
        try:
            # Validate inputs
            if isinstance(file, (str, Path)):
                file_path = str(file)
                filename = filename or os.path.basename(file_path)
                content_type = content_type or AttachmentHandler.get_content_type(
                    file_path
                )
            elif not filename:
                raise ValueError(
                    "Filename must be provided when using file-like object"
                )

            # Validate file
            if not AttachmentHandler.validate_file(file):
                return None

            # Open file if needed
            with AttachmentHandler.open_file(file) as f:
                # Update attachment
                result = self.confluence.update_attachment(
                    content=f,
                    name=filename,
                    content_type=content_type,
                    attachment_id=attachment_id,
                )

                if result and "id" in result:
                    # Get space key
                    space_key = result.get("container", {}).get("key", "")

                    return AttachmentHandler.format_attachment_info(
                        result, self.config.url, space_key
                    )

            return None

        except Exception as e:
            logger.error(f"Error updating attachment: {e}")
            return None

    def delete_attachment(self, attachment_id: str) -> bool:
        """Delete an attachment.

        Args:
            attachment_id: The ID of the attachment to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.confluence.delete_attachment(attachment_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting attachment: {e}")
            return False
