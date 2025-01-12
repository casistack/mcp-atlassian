import logging
import os
from datetime import datetime
from typing import List, Optional, Any, BinaryIO, Union
from pathlib import Path

from atlassian import Jira
from dotenv import load_dotenv

from .config import JiraConfig
from .preprocessing import TextPreprocessor
from .types import Document
from .attachments import AttachmentHandler, AttachmentInfo

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("mcp-jira")


class JiraFetcher:
    """Handles fetching and parsing content from Jira."""

    def __init__(self):
        url = os.getenv("JIRA_URL")
        username = os.getenv("JIRA_USERNAME")
        token = os.getenv("JIRA_API_TOKEN")

        if not all([url, username, token]):
            raise ValueError("Missing required Jira environment variables")

        self.config = JiraConfig(url=url, username=username, api_token=token)
        self.jira = Jira(
            url=self.config.url,
            username=self.config.username,
            password=self.config.api_token,  # API token is used as password
            cloud=True,
        )
        self.preprocessor = TextPreprocessor(self.config.url)

    def _clean_text(self, text: str) -> str:
        """
        Clean text content by:
        1. Processing user mentions and links
        2. Converting HTML/wiki markup to markdown
        """
        if not text:
            return ""

        return self.preprocessor.clean_jira_text(text)

    def get_issue(self, issue_key: str, expand: Optional[str] = None) -> Document:
        """
        Get a single issue with all its details.

        Args:
            issue_key: The issue key (e.g. 'PROJ-123')
            expand: Optional fields to expand

        Returns:
            Document containing issue content and metadata
        """
        try:
            issue = self.jira.issue(issue_key, expand=expand)

            # Process description and comments
            description = self._clean_text(issue["fields"].get("description", ""))

            # Get comments
            comments = []
            if "comment" in issue["fields"]:
                for comment in issue["fields"]["comment"]["comments"]:
                    processed_comment = self._clean_text(comment["body"])
                    created = datetime.fromisoformat(
                        comment["created"].replace("Z", "+00:00")
                    )
                    author = comment["author"].get("displayName", "Unknown")
                    comments.append(
                        {
                            "body": processed_comment,
                            "created": created.strftime("%Y-%m-%d"),
                            "author": author,
                        }
                    )

            # Format created date
            created_date = datetime.fromisoformat(
                issue["fields"]["created"].replace("Z", "+00:00")
            )
            formatted_created = created_date.strftime("%Y-%m-%d")

            # Combine content in a more structured way
            content = f"""Issue: {issue_key}
Title: {issue['fields'].get('summary', '')}
Type: {issue['fields']['issuetype']['name']}
Status: {issue['fields']['status']['name']}
Created: {formatted_created}

Description:
{description}

Comments:
""" + "\n".join(
                [f"{c['created']} - {c['author']}: {c['body']}" for c in comments]
            )

            # Streamlined metadata with only essential information
            metadata = {
                "key": issue_key,
                "title": issue["fields"].get("summary", ""),
                "type": issue["fields"]["issuetype"]["name"],
                "status": issue["fields"]["status"]["name"],
                "created_date": formatted_created,
                "priority": issue["fields"].get("priority", {}).get("name", "None"),
                "link": f"{self.config.url.rstrip('/')}/browse/{issue_key}",
            }

            return Document(page_content=content, metadata=metadata)

        except Exception as e:
            logger.error(f"Error fetching issue {issue_key}: {str(e)}")
            raise

    def search_issues(
        self,
        jql: str,
        fields: str = "*all",
        start: int = 0,
        limit: int = 50,
        expand: Optional[str] = None,
    ) -> List[Document]:
        """
        Search for issues using JQL.

        Args:
            jql: JQL query string
            fields: Comma-separated string of fields to return
            start: Starting index
            limit: Maximum results to return
            expand: Fields to expand

        Returns:
            List of Documents containing matching issues
        """
        try:
            results = self.jira.jql(
                jql, fields=fields, start=start, limit=limit, expand=expand
            )

            documents = []
            for issue in results["issues"]:
                # Get full issue details
                doc = self.get_issue(issue["key"], expand=expand)
                documents.append(doc)

            return documents

        except Exception as e:
            logger.error(f"Error searching issues with JQL {jql}: {str(e)}")
            raise

    def get_project_issues(
        self, project_key: str, start: int = 0, limit: int = 50
    ) -> List[Document]:
        """
        Get all issues for a project.

        Args:
            project_key: The project key
            start: Starting index
            limit: Maximum results to return

        Returns:
            List of Documents containing project issues
        """
        jql = f"project = {project_key} ORDER BY created DESC"
        return self.search_issues(jql, start=start, limit=limit)

    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
        custom_fields: Optional[dict] = None,
    ) -> Optional[Document]:
        """Create a new Jira issue.

        Args:
            project_key: The project key where the issue will be created
            summary: The issue summary/title
            description: The issue description
            issue_type: The type of issue (e.g., 'Task', 'Bug', 'Story')
            priority: Optional priority level
            assignee: Optional username to assign the issue to
            labels: Optional list of labels to add to the issue
            custom_fields: Optional dictionary of custom field values

        Returns:
            Document object if creation successful, None otherwise
        """
        try:
            # Prepare the issue fields
            fields = {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }

            # Add optional fields if provided
            if priority:
                fields["priority"] = {"name": priority}
            if assignee:
                fields["assignee"] = {"name": assignee}
            if labels:
                fields["labels"] = labels
            if custom_fields:
                fields.update(custom_fields)

            # Create the issue
            issue = self.jira.issue_create(fields=fields)

            if issue and "key" in issue:
                # Return the created issue as a Document
                return self.get_issue(issue["key"])
            return None

        except Exception as e:
            logger.error(f"Error creating Jira issue: {e}")
            return None

    def update_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
        custom_fields: Optional[dict] = None,
    ) -> Optional[Document]:
        """Update an existing Jira issue.

        Args:
            issue_key: The issue key to update
            summary: Optional new summary
            description: Optional new description
            status: Optional new status
            priority: Optional new priority
            assignee: Optional new assignee
            labels: Optional new labels
            custom_fields: Optional custom fields to update

        Returns:
            Document object if update successful, None otherwise
        """
        try:
            # Prepare the update fields
            fields = {}
            if summary is not None:
                fields["summary"] = summary
            if description is not None:
                fields["description"] = description
            if priority is not None:
                fields["priority"] = {"name": priority}
            if assignee is not None:
                fields["assignee"] = {"name": assignee}
            if labels is not None:
                fields["labels"] = labels
            if custom_fields:
                fields.update(custom_fields)

            # Update the issue
            self.jira.issue_update(issue_key, fields=fields)

            # Return the updated issue as a Document
            return self.get_issue(issue_key)

        except Exception as e:
            logger.error(f"Error updating Jira issue {issue_key}: {e}")
            return None

    def get_issue_transitions(self, issue_key: str) -> dict:
        """Get available transitions for an issue.

        Args:
            issue_key: The issue key to get transitions for

        Returns:
            Dictionary containing available transitions
        """
        try:
            return self.jira.get_issue_transitions(issue_key)
        except Exception as e:
            logger.error(f"Error getting issue transitions: {e}")
            return {"transitions": []}

    def update_issue_section(
        self,
        issue_key: str,
        heading: str,
        new_content: str,
    ) -> Optional[Document]:
        """Update a specific section of a Jira issue description.

        Args:
            issue_key: The issue key to update
            heading: The heading text that identifies the section
            new_content: The new content for the section

        Returns:
            Updated Document object if successful, None otherwise
        """
        try:
            # Get current issue
            issue = self.jira.issue(issue_key)
            if not issue:
                logger.error(f"Issue {issue_key} not found")
                return None

            current_description = issue["fields"].get("description", "")

            # Update the specific section
            from .content import ContentEditor

            updated_description = ContentEditor.replace_section(
                current_description, heading, new_content
            )

            # Update the issue
            self.jira.update_issue_field(
                issue_key, {"description": updated_description}
            )

            return self.get_issue(issue_key)

        except Exception as e:
            logger.error(f"Error updating issue section: {e}")
            return None

    def insert_after_issue_section(
        self,
        issue_key: str,
        heading: str,
        new_content: str,
    ) -> Optional[Document]:
        """Insert content after a specific section in a Jira issue description.

        Args:
            issue_key: The issue key to update
            heading: The heading text after which to insert content
            new_content: The content to insert

        Returns:
            Updated Document object if successful, None otherwise
        """
        try:
            issue = self.jira.issue(issue_key)
            if not issue:
                logger.error(f"Issue {issue_key} not found")
                return None

            current_description = issue["fields"].get("description", "")

            from .content import ContentEditor

            updated_description = ContentEditor.insert_after_heading(
                current_description, heading, new_content
            )

            self.jira.update_issue_field(
                issue_key, {"description": updated_description}
            )

            return self.get_issue(issue_key)

        except Exception as e:
            logger.error(f"Error inserting content: {e}")
            return None

    def append_to_list_in_issue(
        self,
        issue_key: str,
        heading: str,
        list_marker: str,
        new_item: str,
    ) -> Optional[Document]:
        """Append an item to a list in a specific section of a Jira issue.

        Args:
            issue_key: The issue key to update
            heading: The heading text that identifies the section
            list_marker: The marker that identifies the list ('*' for bullet, '#' for numbered)
            new_item: The new list item to append

        Returns:
            Updated Document object if successful, None otherwise
        """
        try:
            issue = self.jira.issue(issue_key)
            if not issue:
                logger.error(f"Issue {issue_key} not found")
                return None

            current_description = issue["fields"].get("description", "")

            from .content import ContentEditor

            start, end = ContentEditor.find_section(current_description, heading)
            if start == -1:
                logger.error(f"Section with heading '{heading}' not found")
                return None

            section_content = current_description[start:end]
            updated_section = ContentEditor.append_to_list(
                section_content, list_marker, new_item
            )
            updated_description = (
                current_description[:start]
                + updated_section
                + current_description[end:]
            )

            self.jira.update_issue_field(
                issue_key, {"description": updated_description}
            )

            return self.get_issue(issue_key)

        except Exception as e:
            logger.error(f"Error appending to list: {e}")
            return None

    def update_table_in_issue(
        self,
        issue_key: str,
        heading: str,
        table_start: str,
        row_identifier: str,
        new_values: list[str],
    ) -> Optional[Document]:
        """Update a specific row in a table within a section of a Jira issue.

        Args:
            issue_key: The issue key to update
            heading: The heading text that identifies the section
            table_start: Text that uniquely identifies the table
            row_identifier: Text that uniquely identifies the row to update
            new_values: New values for the row cells

        Returns:
            Updated Document object if successful, None otherwise
        """
        try:
            issue = self.jira.issue(issue_key)
            if not issue:
                logger.error(f"Issue {issue_key} not found")
                return None

            current_description = issue["fields"].get("description", "")

            from .content import ContentEditor

            start, end = ContentEditor.find_section(current_description, heading)
            if start == -1:
                logger.error(f"Section with heading '{heading}' not found")
                return None

            section_content = current_description[start:end]
            updated_section = ContentEditor.update_table_row(
                section_content, table_start, row_identifier, new_values
            )
            updated_description = (
                current_description[:start]
                + updated_section
                + current_description[end:]
            )

            self.jira.update_issue_field(
                issue_key, {"description": updated_description}
            )

            return self.get_issue(issue_key)

        except Exception as e:
            logger.error(f"Error updating table: {e}")
            return None

    def add_comment_with_formatting(
        self,
        issue_key: str,
        content: str,
        format_type: str,
        **format_options: Any,
    ) -> Optional[Document]:
        """Add a formatted comment to a Jira issue.

        Args:
            issue_key: The issue key to add the comment to
            content: The comment content
            format_type: Type of formatting to apply
            **format_options: Additional formatting options

        Returns:
            Updated Document object if successful, None otherwise
        """
        try:
            from .content import MarkupFormatter

            formatter = getattr(MarkupFormatter, format_type, None)
            if not formatter:
                logger.error(f"Unknown format type: {format_type}")
                return None

            formatted_content = formatter(content, **format_options)

            self.jira.add_comment(issue_key, formatted_content)

            return self.get_issue(issue_key)

        except Exception as e:
            logger.error(f"Error adding formatted comment: {e}")
            return None

    def get_attachments(self, issue_key: str) -> list[AttachmentInfo]:
        """Get all attachments for a specific issue.

        Args:
            issue_key: The issue key

        Returns:
            List of AttachmentInfo objects
        """
        try:
            issue = self.jira.issue(issue_key, fields="attachment")
            attachments = issue["fields"].get("attachment", [])
            project_key = issue_key.split("-")[0]

            return [
                AttachmentHandler.format_attachment_info(
                    attachment, self.config.url, project_key
                )
                for attachment in attachments
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
            return self.jira.get_attachment_content(attachment_id)
        except Exception as e:
            logger.error(f"Error getting attachment content: {e}")
            return None

    def add_attachment(
        self,
        issue_key: str,
        file: Union[str, Path, BinaryIO],
        filename: Optional[str] = None,
    ) -> Optional[AttachmentInfo]:
        """Add an attachment to an issue.

        Args:
            issue_key: The issue key to attach to
            file: The file to attach (path or file-like object)
            filename: Optional filename (required if file is a file-like object)

        Returns:
            AttachmentInfo if successful, None otherwise
        """
        try:
            # Validate inputs
            if isinstance(file, (str, Path)):
                file_path = str(file)
                filename = filename or os.path.basename(file_path)
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
                result = self.jira.add_attachment(issue_key, f, filename=filename)

                if result and len(result) > 0:
                    # Get project key
                    project_key = issue_key.split("-")[0]

                    return AttachmentHandler.format_attachment_info(
                        result[0], self.config.url, project_key
                    )

            return None

        except Exception as e:
            logger.error(f"Error adding attachment: {e}")
            return None

    def delete_attachment(self, attachment_id: str) -> bool:
        """Delete an attachment.

        Args:
            attachment_id: The ID of the attachment to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.jira.delete_attachment(attachment_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting attachment: {e}")
            return False

    def get_templates(self, project_key: Optional[str] = None) -> list[dict]:
        """Get all available issue templates for a project or global templates.

        Args:
            project_key: Optional project key to get project-specific templates

        Returns:
            List of template dictionaries containing id, name, description, and other metadata
        """
        try:
            # Get project templates if project_key is provided
            templates = []

            if project_key:
                # Get project-specific templates
                project_templates = self.jira.get_project_issue_templates(project_key)
                for template in project_templates:
                    templates.append(
                        {
                            "id": template["id"],
                            "name": template["name"],
                            "description": template.get("description", ""),
                            "type": "project",
                            "project_key": project_key,
                            "issue_type": template.get("issueType", {}).get("name"),
                            "fields": template.get("fields", {}),
                        }
                    )

            # Get global templates
            global_templates = self.jira.get_global_issue_templates()
            for template in global_templates:
                templates.append(
                    {
                        "id": template["id"],
                        "name": template["name"],
                        "description": template.get("description", ""),
                        "type": "global",
                        "issue_type": template.get("issueType", {}).get("name"),
                        "fields": template.get("fields", {}),
                    }
                )

            return templates

        except Exception as e:
            logger.error(f"Error fetching Jira templates: {e}")
            return []
