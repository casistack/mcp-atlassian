import logging
import os
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

from atlassian import Confluence
from dotenv import load_dotenv

from .config import ConfluenceConfig
from .preprocessing import TextPreprocessor
from .types import Document
from .attachments import AttachmentHandler, AttachmentInfo
from .content import ContentEditor

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("mcp-atlassian")


class ConfluenceFetcher:
    """Fetches content from Confluence."""

    def __init__(self):
        """Initialize the fetcher."""
        url = os.getenv("CONFLUENCE_URL")
        # Remove trailing /wiki from the URL if present
        if url and url.endswith("/wiki"):
            url = url[:-5]
        username = os.getenv("CONFLUENCE_USERNAME")
        token = os.getenv("CONFLUENCE_API_TOKEN")

        self.config = ConfluenceConfig(url=url, username=username, api_token=token)
        self.confluence = Confluence(
            url=self.config.url,
            username=self.config.username,
            password=self.config.api_token,  # API token is used as password
            cloud=True,
        )
        self.preprocessor = TextPreprocessor(self.config.url, self.confluence)
        self.content_editor = ContentEditor()
        self.logger = logging.getLogger("mcp-atlassian")

    def _process_html_content(
        self, html_content: str, space_key: str
    ) -> tuple[str, str]:
        return self.preprocessor.process_html_content(html_content, space_key)

    def _clean_html_content(self, html_content: str) -> str:
        """Clean HTML content by removing unnecessary tags and formatting."""
        cleaned_html, _ = self._process_html_content(html_content, "")
        return cleaned_html

    def get_spaces(self, start: int = 0, limit: int = 10):
        """Get all available spaces."""
        return self.confluence.get_all_spaces(start=start, limit=limit)

    def get_space_key_by_name(self, space_name: str) -> Optional[str]:
        """Get the correct space key for a given space name/display name.

        Args:
            space_name: The display name or partial name of the space

        Returns:
            The correct space key if found, None otherwise
        """
        try:
            spaces = self.get_spaces()
            if not spaces or "results" not in spaces:
                self.logger.error("Failed to fetch spaces")
                return None

            # First try exact match
            for space in spaces["results"]:
                if space.get("name") == space_name:
                    return space.get("key")

            # Then try case-insensitive match
            for space in spaces["results"]:
                if space.get("name", "").lower() == space_name.lower():
                    return space.get("key")

            # Finally try partial match
            for space in spaces["results"]:
                if space_name.lower() in space.get("name", "").lower():
                    return space.get("key")

            self.logger.warning(f"No space found matching name: {space_name}")
            return None

        except Exception as e:
            self.logger.error(f"Error finding space key: {str(e)}")
            return None

    def validate_space_key(self, space_key: str) -> Tuple[bool, Optional[str]]:
        """Validate a space key and return the correct one if needed.

        Args:
            space_key: The space key to validate

        Returns:
            Tuple of (is_valid, correct_key)
            - is_valid: Whether the provided key is valid
            - correct_key: The correct key if found, None otherwise
        """
        try:
            self.logger.info(f"Validating space key: {space_key}")

            # If it's already a valid key, verify it exists
            spaces = self.get_spaces()
            if not spaces or "results" not in spaces:
                self.logger.error("Failed to fetch spaces")
                return False, None

            self.logger.debug(f"Found {len(spaces['results'])} spaces")

            # First check exact match
            for space in spaces["results"]:
                current_key = space.get("key")
                self.logger.debug(f"Checking against space: {current_key}")
                if current_key == space_key:
                    self.logger.info(f"Found exact match for key: {space_key}")
                    return True, space_key

            # Then check case-insensitive key match
            for space in spaces["results"]:
                current_key = space.get("key", "")
                if current_key.lower() == space_key.lower():
                    self.logger.info(
                        f"Found case-insensitive match. Original: {space_key}, Correct: {current_key}"
                    )
                    return False, current_key  # Return the correctly cased key

            # If not found as a key, try to find it by name
            self.logger.info("No key match found, trying to find by name")
            correct_key = self.get_space_key_by_name(space_key)
            if correct_key:
                self.logger.info(f"Found matching space by name. Key: {correct_key}")
                return False, correct_key

            self.logger.warning(
                f"Invalid space key and no matching space found: {space_key}"
            )
            return False, None

        except Exception as e:
            self.logger.error(f"Error validating space key: {str(e)}")
            return False, None

    def _get_page_url(self, space_key: str, page_id: str) -> str:
        """Construct the correct URL for a Confluence page."""
        return f"{self.config.url}/wiki/spaces/{space_key}/pages/{page_id}"

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
            "version": version.get("number", 1),
            "url": self._get_page_url(space_key, page_id),
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
        template_id: Optional[str] = None,
        template_parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Document]:
        """Create a new Confluence page.

        Args:
            space_key: The key of the space where the page will be created
            title: The title of the new page
            body: The content of the page
            parent_id: Optional ID of the parent page
            representation: Content representation ('storage' for wiki markup, 'editor' for rich text)
            template_id: Optional template ID to create page from
            template_parameters: Optional parameters for template

        Returns:
            Document object if creation successful, None otherwise
        """
        try:
            self.logger.debug(
                f"Creating page with title: {title} in space: {space_key}"
            )

            # Validate space key first
            is_valid, correct_key = self.validate_space_key(space_key)
            if not is_valid:
                if correct_key:
                    self.logger.info(
                        f"Using correct space key: {correct_key} instead of: {space_key}"
                    )
                    space_key = correct_key
                else:
                    self.logger.error(f"Invalid space key: {space_key}")
                    return None

            self.logger.debug(f"Content representation: {representation}")

            if template_id:
                # First check if this is a blueprint template
                templates = self.get_templates(space_key)
                template_info = next(
                    (t for t in templates if t["id"] == template_id), None
                )

                if not template_info:
                    self.logger.error(f"Template {template_id} not found")
                    return None

                if template_info["type"] == "blueprint":
                    # For blueprint templates, we need to create a page first and then update it
                    self.logger.debug(
                        f"Creating page from blueprint template: {template_id}"
                    )
                    self.logger.debug(f"Template parameters: {template_parameters}")

                    # Create initial page
                    page = self.confluence.create_page(
                        space=space_key,
                        title=title,
                        body="",  # Empty body initially
                        parent_id=parent_id,
                        representation=representation,
                    )

                    if not page or not page.get("id"):
                        self.logger.error("Failed to create initial page")
                        return None

                    try:
                        # Now apply the blueprint template
                        self.confluence.create_page_from_blueprint(
                            page_id=page["id"],
                            blueprint_id=template_id,
                            **template_parameters or {},
                        )

                        # Get the updated page
                        created_page = self.get_page_content(page["id"])
                        self.logger.debug(
                            f"Created page metadata: {created_page.metadata}"
                        )
                        return created_page

                    except Exception as e:
                        # If blueprint application fails, clean up the created page
                        self.logger.error(f"Error applying blueprint: {str(e)}")
                        self.confluence.remove_page(page["id"])
                        return None
                else:
                    # For content templates
                    self.logger.debug(
                        f"Creating page from content template: {template_id}"
                    )
                    try:
                        # Use create_page_from_template for content templates
                        page = self.confluence.create_page_from_template(
                            space_key=space_key,
                            title=title,
                            template_id=template_id,
                            parent_id=parent_id,
                            **template_parameters or {},
                        )

                        if page and isinstance(page, dict) and page.get("id"):
                            created_page = self.get_page_content(page["id"])
                            self.logger.debug(
                                f"Created page metadata: {created_page.metadata}"
                            )
                            return created_page

                        self.logger.error(
                            "Failed to create page from template - API returned invalid response"
                        )
                        return None

                    except Exception as e:
                        self.logger.error(
                            f"Error creating page from template: {str(e)}"
                        )
                        return None
            else:
                # Regular page creation without template
                page = self.confluence.create_page(
                    space=space_key,
                    title=title,
                    body=body,
                    parent_id=parent_id,
                    representation=representation,
                )

            self.logger.debug(f"API Response: {page}")

            if page and page.get("id"):
                created_page = self.get_page_content(page["id"])
                self.logger.debug(f"Created page metadata: {created_page.metadata}")
                return created_page

            self.logger.error("Failed to create page - API returned invalid response")
            return None
        except Exception as e:
            self.logger.error(f"Error creating Confluence page: {e}")
            self.logger.debug("Full error details:", exc_info=True)
            return None

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        representation: str = "storage",
        minor_edit: bool = False,
        type: str = "page",
    ) -> Optional[Document]:
        """Update an existing Confluence page.

        Args:
            page_id: The ID of the page to update
            title: The new title of the page
            body: The new content of the page
            representation: Content representation ('storage' for wiki markup, 'editor' for rich text)
            minor_edit: Whether this is a minor edit
            type: The type of content ('page' or 'blogpost')

        Returns:
            Document object if update successful, None otherwise
        """
        try:
            # Get current version
            current_page = self.confluence.get_page_by_id(
                page_id=page_id, expand="version,space"
            )
            if not current_page:
                self.logger.error(f"Page {page_id} not found")
                return None

            space_key = current_page.get("space", {}).get("key", "")

            self.logger.debug(f"Updating page {page_id}")
            self.logger.debug(f"New title: {title}")
            self.logger.debug(f"Content length: {len(body)}")

            # Update the page
            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=title,
                body=body,
                type=type,
                representation=representation,
                minor_edit=minor_edit,
            )

            if updated_page and updated_page.get("id"):
                # Get the updated page to ensure we have the correct version
                updated_page = self.confluence.get_page_by_id(
                    page_id=updated_page["id"], expand="body.storage,version,space"
                )

                # Process the content
                content = (
                    updated_page.get("body", {}).get("storage", {}).get("value", "")
                )
                processed_html, processed_markdown = self._process_html_content(
                    content, space_key
                )

                # Get the new version number from the response
                version = updated_page.get("version", {}).get("number", 1)

                # Create metadata with updated version
                metadata = {
                    "page_id": updated_page["id"],
                    "title": updated_page["title"],
                    "version": version,
                    "space_key": space_key,
                    "url": self._get_page_url(space_key, updated_page["id"]),
                }

                return Document(page_content=processed_markdown, metadata=metadata)

            self.logger.error("Failed to update page - API returned invalid response")
            return None
        except Exception as e:
            self.logger.error(f"Error updating Confluence page: {e}")
            self.logger.debug("Full error details:", exc_info=True)
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
                page_id=page_id, expand="body.storage,version,space"
            )
            if not current_page:
                logger.error(f"Page {page_id} not found")
                return None

            current_content = current_page["body"]["storage"]["value"]
            version = current_page["version"]["number"]
            space_key = current_page.get("space", {}).get("key", "")

            # Update the specific section
            updated_content = self.content_editor.replace_section(
                current_content, heading, new_content
            )

            # Update the page
            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=current_page["title"],
                body=updated_content,
                type="page",
                representation="storage",
                minor_edit=minor_edit,
                version_number=version,
            )

            if updated_page and updated_page.get("id"):
                # Process the content
                content = (
                    updated_page.get("body", {}).get("storage", {}).get("value", "")
                )
                processed_html, processed_markdown = self._process_html_content(
                    content, space_key
                )

                # Get the new version number from the response
                new_version = updated_page.get("version", {}).get("number", version + 1)

                # Create metadata with updated version
                metadata = {
                    "page_id": updated_page["id"],
                    "title": updated_page["title"],
                    "version": new_version,
                    "space_key": space_key,
                    "url": f"{self.config.url}/wiki/spaces/{space_key}/pages/{updated_page['id']}",
                }

                return Document(page_content=processed_markdown, metadata=metadata)

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
                page_id=page_id, expand="body.storage,version,space"
            )
            if not current_page:
                logger.error(f"Page {page_id} not found")
                return None

            current_content = current_page["body"]["storage"]["value"]
            version = current_page["version"]["number"]
            space_key = current_page.get("space", {}).get("key", "")

            updated_content = self.content_editor.insert_after_heading(
                current_content, heading, new_content
            )

            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=current_page["title"],
                body=updated_content,
                type="page",
                representation="storage",
                minor_edit=minor_edit,
                version_number=version,
            )

            if updated_page and updated_page.get("id"):
                # Process the content
                content = (
                    updated_page.get("body", {}).get("storage", {}).get("value", "")
                )
                processed_html, processed_markdown = self._process_html_content(
                    content, space_key
                )

                # Get the new version number from the response
                new_version = updated_page.get("version", {}).get("number", version + 1)

                # Create metadata with updated version
                metadata = {
                    "page_id": updated_page["id"],
                    "title": updated_page["title"],
                    "version": new_version,
                    "space_key": space_key,
                    "url": f"{self.config.url}/wiki/spaces/{space_key}/pages/{updated_page['id']}",
                }

                return Document(page_content=processed_markdown, metadata=metadata)

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
                page_id=page_id, expand="body.storage,version,space"
            )
            if not current_page:
                logger.error(f"Page {page_id} not found")
                return None

            current_content = current_page["body"]["storage"]["value"]
            version = current_page["version"]["number"]
            space_key = current_page.get("space", {}).get("key", "")

            start, end = self.content_editor.find_section(current_content, heading)
            if start == -1:
                logger.error(f"Section with heading '{heading}' not found")
                return None

            section_content = current_content[start:end]
            updated_section = self.content_editor.append_to_list(
                section_content, list_marker, new_item
            )
            updated_content = (
                current_content[:start] + updated_section + current_content[end:]
            )

            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=current_page["title"],
                body=updated_content,
                type="page",
                representation="storage",
                minor_edit=minor_edit,
                version_number=version,
            )

            if updated_page and updated_page.get("id"):
                # Process the content
                content = (
                    updated_page.get("body", {}).get("storage", {}).get("value", "")
                )
                processed_html, processed_markdown = self._process_html_content(
                    content, space_key
                )

                # Get the new version number from the response
                new_version = updated_page.get("version", {}).get("number", version + 1)

                # Create metadata with updated version
                metadata = {
                    "page_id": updated_page["id"],
                    "title": updated_page["title"],
                    "version": new_version,
                    "space_key": space_key,
                    "url": f"{self.config.url}/wiki/spaces/{space_key}/pages/{updated_page['id']}",
                }

                return Document(page_content=processed_markdown, metadata=metadata)

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
                page_id=page_id, expand="body.storage,version,space"
            )
            if not current_page:
                logger.error(f"Page {page_id} not found")
                return None

            current_content = current_page["body"]["storage"]["value"]
            version = current_page["version"]["number"]
            space_key = current_page.get("space", {}).get("key", "")

            start, end = self.content_editor.find_section(current_content, heading)
            if start == -1:
                logger.error(f"Section with heading '{heading}' not found")
                return None

            section_content = current_content[start:end]
            updated_section = self.content_editor.update_table_row(
                section_content, table_start, row_identifier, new_values
            )
            updated_content = (
                current_content[:start] + updated_section + current_content[end:]
            )

            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=current_page["title"],
                body=updated_content,
                type="page",
                representation="storage",
                minor_edit=minor_edit,
                version_number=version,
            )

            if updated_page and updated_page.get("id"):
                # Process the content
                content = (
                    updated_page.get("body", {}).get("storage", {}).get("value", "")
                )
                processed_html, processed_markdown = self._process_html_content(
                    content, space_key
                )

                # Get the new version number from the response
                new_version = updated_page.get("version", {}).get("number", version + 1)

                # Create metadata with updated version
                metadata = {
                    "page_id": updated_page["id"],
                    "title": updated_page["title"],
                    "version": new_version,
                    "space_key": space_key,
                    "url": f"{self.config.url}/wiki/spaces/{space_key}/pages/{updated_page['id']}",
                }

                return Document(page_content=processed_markdown, metadata=metadata)

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
            return self.confluence.get_attachment_content(attachment_id)
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

            # Get space key for the page
            page = self.confluence.get_page_by_id(page_id, expand="space")
            space_key = page.get("space", {}).get("key", "")

            # Open file if needed
            with AttachmentHandler.open_file(file) as f:
                # Upload attachment
                result = self.confluence.attach_file(
                    content=f, name=filename, content_type=content_type, page_id=page_id
                )

                # Handle both list and single object responses
                if result:
                    attachment_data = result[0] if isinstance(result, list) else result
                    # Add container info to attachment data
                    attachment_data["container"] = {"key": space_key}
                    return AttachmentHandler.format_attachment_info(
                        attachment_data, self.config.url, space_key
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

    def delete_page(self, page_id: str) -> bool:
        """Delete a Confluence page.

        Args:
            page_id: The ID of the page to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.confluence.remove_page(page_id=page_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting page: {e}")
            return False

    def get_templates(self, space_key=None):
        """Get available templates for a space or globally."""
        templates = []
        try:
            # Get blueprint templates
            self.logger.debug(f"Fetching blueprint templates for space: {space_key}")
            blueprint_response = self.confluence.get_blueprint_templates(space_key)
            self.logger.debug(f"Blueprint response: {blueprint_response}")

            if blueprint_response and isinstance(blueprint_response, list):
                for template in blueprint_response:
                    templates.append(
                        {
                            "id": template.get("templateId"),
                            "name": template.get("name"),
                            "description": template.get("description"),
                            "type": "blueprint",
                            "space_key": template.get("space", {}).get("key"),
                        }
                    )

            # Get custom templates
            if space_key:
                self.logger.debug(f"Fetching custom templates for space: {space_key}")
                custom_templates = self.confluence.get_content_templates(space_key)
                self.logger.debug(f"Custom templates response: {custom_templates}")

                if custom_templates and isinstance(custom_templates, list):
                    for template in custom_templates:
                        templates.append(
                            {
                                "id": template.get("id"),
                                "name": template.get("title"),
                                "description": template.get("description"),
                                "type": "custom",
                                "space_key": space_key,
                            }
                        )

            self.logger.debug(f"Final templates list: {templates}")
            return templates

        except Exception as e:
            self.logger.error(f"Error fetching Confluence templates: {str(e)}")
            self.logger.debug("Exception details:", exc_info=True)
            return []

    def search_pages(self, title: str, limit: int = 10) -> List[Document]:
        """Search for pages across all spaces by title."""
        try:
            # Use CQL to search for pages with the given title
            cql = f'type = page AND title ~ "{title}"'
            self.logger.debug(f"Executing CQL query: {cql}")

            results = self.confluence.cql(
                cql, limit=limit, expand="body.storage,version,space"
            )
            self.logger.debug(f"Raw search results: {results}")

            if not results or "results" not in results:
                self.logger.debug("No results found or invalid response format")
                return []

            documents = []
            for result in results["results"]:
                try:
                    # Extract content details from the result
                    content = result.get("content", {})
                    space_key = (
                        content.get("_expandable", {}).get("space", "").split("/")[-1]
                    )

                    # Fetch the full page content since it's not in the CQL results
                    page = self.confluence.get_page_by_id(
                        content["id"], expand="body.storage,version,space"
                    )

                    if not page:
                        self.logger.debug(
                            f"Could not fetch full page content for ID: {content['id']}"
                        )
                        continue

                    content_body = (
                        page.get("body", {}).get("storage", {}).get("value", "")
                    )
                    if not content_body:
                        self.logger.debug(f"No content found for page: {content['id']}")
                        continue

                    processed_html, processed_markdown = self._process_html_content(
                        content_body, space_key
                    )

                    # Get space details
                    space = page.get("space", {})

                    # Get version and author information
                    version = page.get("version", {})
                    author = version.get("by", {})

                    metadata = {
                        "page_id": content["id"],
                        "title": content["title"],
                        "version": version.get("number", 1),
                        "url": f"{self.config.url}{result['url']}",
                        "space_key": space.get("key", space_key),
                        "space_name": space.get("name", "Unknown Space"),
                        "author_name": author.get("displayName", "Unknown"),
                        "last_modified": result.get("lastModified"),
                    }

                    documents.append(
                        Document(page_content=processed_markdown, metadata=metadata)
                    )
                    self.logger.debug(
                        f"Successfully processed document: {metadata['title']}"
                    )
                except Exception as e:
                    self.logger.error(f"Error processing search result: {str(e)}")
                    self.logger.debug("Result that caused error:", result)
                    continue

            return documents

        except Exception as e:
            self.logger.error(f"Error searching pages: {str(e)}")
            self.logger.debug("Full error details:", exc_info=True)
            return []

    def get_content_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a content template by its ID.

        Args:
            template_id: The ID of the template to retrieve

        Returns:
            Template content if successful, None otherwise
        """
        try:
            return self.confluence.get_content_template(template_id)
        except Exception as e:
            self.logger.error(f"Error getting content template: {str(e)}")
            self.logger.debug("Exception details:", exc_info=True)
            return None
