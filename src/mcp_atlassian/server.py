import json
import logging
from collections.abc import Sequence
from typing import Any, Optional
from pathlib import Path
import base64

from mcp.server import Server
from mcp.types import Resource, TextContent, Tool
from pydantic import AnyUrl

from .confluence import ConfluenceFetcher
from .jira import JiraFetcher
from .search import UnifiedSearch
from .content import TemplateHandler, ContentEditor, RichTextEditor
from .tool_handlers import handle_confluence_tools, handle_jira_tools

# Configure logging
logging.basicConfig(level=logging.disable())
logger = logging.getLogger("mcp-atlassian")

# Initialize the content fetchers
logger.debug("Initializing content fetchers...")
confluence_fetcher = ConfluenceFetcher()
jira_fetcher = JiraFetcher()
unified_search = UnifiedSearch(confluence_fetcher, jira_fetcher)
app = Server("mcp-atlassian")
logger.debug("Server initialized successfully")

# Tool categories for better organization
TOOL_CATEGORIES = {
    "search": "🔍 Search",
    "confluence": "📝 Confluence",
    "jira": "🎯 Jira",
    "templates": "📋 Templates",
}

# Initialize content editor
content_editor = ContentEditor()


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available Confluence spaces and Jira projects as resources."""
    resources = []

    # Add Confluence spaces
    spaces_response = confluence_fetcher.get_spaces()
    if isinstance(spaces_response, dict) and "results" in spaces_response:
        spaces = spaces_response["results"]
        resources.extend(
            [
                Resource(
                    uri=AnyUrl(f"confluence://{space['key']}"),
                    name=f"Confluence Space: {space['name']}",
                    mimeType="text/plain",
                    description=space.get("description", {})
                    .get("plain", {})
                    .get("value", ""),
                )
                for space in spaces
            ]
        )

    # Add Jira projects
    try:
        projects = jira_fetcher.jira.projects()
        resources.extend(
            [
                Resource(
                    uri=AnyUrl(f"jira://{project['key']}"),
                    name=f"Jira Project: {project['name']}",
                    mimeType="text/plain",
                    description=project.get("description", ""),
                )
                for project in projects
            ]
        )
    except Exception as e:
        logger.error(f"Error fetching Jira projects: {str(e)}")

    return resources


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read content from Confluence or Jira."""
    uri_str = str(uri)

    # Handle Confluence resources
    if uri_str.startswith("confluence://"):
        parts = uri_str.replace("confluence://", "").split("/")

        # Handle space listing
        if len(parts) == 1:
            space_key = parts[0]
            documents = confluence_fetcher.get_space_pages(space_key)
            content = []
            for doc in documents:
                content.append(f"# {doc.metadata['title']}\n\n{doc.page_content}\n---")
            return "\n\n".join(content)

        # Handle specific page
        elif len(parts) >= 3 and parts[1] == "pages":
            space_key = parts[0]
            title = parts[2]
            doc = confluence_fetcher.get_page_by_title(space_key, title)

            if not doc:
                raise ValueError(f"Page not found: {title}")

            return doc.page_content

    # Handle Jira resources
    elif uri_str.startswith("jira://"):
        parts = uri_str.replace("jira://", "").split("/")

        # Handle project listing
        if len(parts) == 1:
            project_key = parts[0]
            issues = jira_fetcher.get_project_issues(project_key)
            content = []
            for issue in issues:
                content.append(
                    f"# {issue.metadata['key']}: {issue.metadata['title']}\n\n{issue.page_content}\n---"
                )
            return "\n\n".join(content)

        # Handle specific issue
        elif len(parts) >= 3 and parts[1] == "issues":
            issue_key = parts[2]
            issue = jira_fetcher.get_issue(issue_key)
            return issue.page_content

    raise ValueError(f"Invalid resource URI: {uri}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Confluence and Jira tools."""
    logger.debug("Starting list_tools()")
    tools = [
        Tool(
            name="unified_search",
            description="Cross-Platform Search Search across both Confluence and Jira platforms in a single query.",
            category=TOOL_CATEGORIES["search"],
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "platforms": {
                        "type": "array",
                        "description": "Optional list of platforms to search ('confluence', 'jira')",
                        "items": {"type": "string", "enum": ["confluence", "jira"]},
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["query"],
            },
            metadata={
                "icon": "🔍",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="confluence_search",
            description="Search Confluence content using CQL (Confluence Query Language) with support for advanced queries and content filtering.",
            category=TOOL_CATEGORIES["confluence"],
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "CQL query string (e.g. 'type=page AND space=DEV')",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["query"],
            },
            metadata={
                "icon": "📝",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="confluence_get_page",
            description="Retrieve content and metadata of a specific Confluence page.",
            category=TOOL_CATEGORIES["confluence"],
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Confluence page ID"},
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Whether to include page metadata",
                        "default": True,
                    },
                },
                "required": ["page_id"],
            },
            metadata={
                "icon": "📄",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="confluence_get_comments",
            description="Retrieve all comments for a specific Confluence page, including author information and timestamps.",
            category=TOOL_CATEGORIES["confluence"],
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Confluence page ID"}
                },
                "required": ["page_id"],
            },
            metadata={
                "icon": "💬",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="jira_get_issue",
            description="Retrieve detailed information about a specific Jira issue, including fields, transitions, and history.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Jira issue key (e.g., 'PROJ-123')",
                    },
                    "expand": {
                        "type": "string",
                        "description": "Optional fields to expand",
                        "default": None,
                    },
                },
                "required": ["issue_key"],
            },
            metadata={
                "icon": "🎯",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="jira_search",
            description="Search Jira issues using JQL (Jira Query Language) with support for custom fields and sorting.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {"type": "string", "description": "JQL query string"},
                    "fields": {
                        "type": "string",
                        "description": "Comma-separated fields to return",
                        "default": "*all",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["jql"],
            },
            metadata={
                "icon": "🔎",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="jira_get_project_issues",
            description="Retrieve all issues from a specific Jira project with pagination support.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {"type": "string", "description": "The project key"},
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["project_key"],
            },
            metadata={
                "icon": "📊",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="get_confluence_templates",
            description="Get all available Confluence templates, including blueprints and custom templates.",
            category=TOOL_CATEGORIES["templates"],
            inputSchema={
                "type": "object",
                "properties": {
                    "space_key": {
                        "type": "string",
                        "description": "Optional space key to get space-specific templates",
                    },
                },
            },
            metadata={
                "icon": "📑",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="get_jira_templates",
            description="Get all available Jira issue templates with their metadata and field mappings.",
            category=TOOL_CATEGORIES["templates"],
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "Optional project key to get project-specific templates",
                    },
                },
            },
            metadata={
                "icon": "📝",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="create_from_confluence_template",
            description="Create a new Confluence page using a predefined template with variable substitution.",
            category=TOOL_CATEGORIES["templates"],
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "ID of the template to use",
                    },
                    "space_key": {
                        "type": "string",
                        "description": "Key of the space to create page in",
                    },
                    "title": {
                        "type": "string",
                        "description": "Title for the new page",
                    },
                    "template_parameters": {
                        "type": "object",
                        "description": "Optional parameters to fill in template",
                    },
                },
                "required": ["template_id", "space_key", "title"],
            },
            metadata={
                "icon": "📋",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="create_from_jira_template",
            description="Create a new Jira issue using a predefined template with custom field support.",
            category=TOOL_CATEGORIES["templates"],
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "ID of the template to use",
                    },
                    "project_key": {
                        "type": "string",
                        "description": "Key of the project to create issue in",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Issue summary",
                    },
                    "template_parameters": {
                        "type": "object",
                        "description": "Optional parameters to fill in template",
                    },
                },
                "required": ["template_id", "project_key", "summary"],
            },
            metadata={
                "icon": "✨",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="get_jira_issue_transitions",
            description="Get all available status transitions for a Jira issue.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The issue key to get transitions for",
                    }
                },
                "required": ["issue_key"],
            },
            metadata={
                "icon": "🔄",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="update_jira_section",
            description="Update a specific section of a Jira issue description by heading.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The issue key to update",
                    },
                    "heading": {
                        "type": "string",
                        "description": "The heading text that identifies the section",
                    },
                    "content": {
                        "type": "string",
                        "description": "The new content for the section",
                    },
                },
                "required": ["issue_key", "heading", "content"],
            },
            metadata={
                "icon": "✏️",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="get_jira_attachments",
            description="Retrieve all attachments for a specific Jira issue with file metadata.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "The issue key"}
                },
                "required": ["issue_key"],
            },
            metadata={
                "icon": "📎",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="update_confluence_page",
            description="Update an existing Confluence page with new content.",
            category=TOOL_CATEGORIES["confluence"],
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to update",
                    },
                    "title": {
                        "type": "string",
                        "description": "The new title of the page",
                    },
                    "body": {
                        "type": "string",
                        "description": "The new content of the page",
                    },
                    "minor_edit": {
                        "type": "boolean",
                        "description": "Whether this is a minor edit",
                        "default": False,
                    },
                },
                "required": ["page_id", "title", "body"],
            },
            metadata={
                "icon": "✏️",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="delete_confluence_page",
            description="Delete a Confluence page.",
            category=TOOL_CATEGORIES["confluence"],
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to delete",
                    },
                },
                "required": ["page_id"],
            },
            metadata={
                "icon": "🗑️",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="add_confluence_attachment",
            description="Add an attachment to a Confluence page.",
            category=TOOL_CATEGORIES["confluence"],
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to attach to",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to attach",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename for the attachment",
                    },
                },
                "required": ["page_id", "file_path"],
            },
            metadata={
                "icon": "📎",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="delete_confluence_attachment",
            description="Delete an attachment from a Confluence page.",
            category=TOOL_CATEGORIES["confluence"],
            inputSchema={
                "type": "object",
                "properties": {
                    "attachment_id": {
                        "type": "string",
                        "description": "The ID of the attachment to delete",
                    },
                },
                "required": ["attachment_id"],
            },
            metadata={
                "icon": "🗑️",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="create_jira_issue",
            description="Create a new Jira issue with custom fields and options.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {"type": "string", "description": "The project key"},
                    "summary": {"type": "string", "description": "Issue summary/title"},
                    "description": {
                        "type": "string",
                        "description": "Issue description",
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Type of issue (e.g., Task, Bug, Story)",
                        "default": "Task",
                    },
                    "priority": {"type": "string", "description": "Priority level"},
                    "assignee": {
                        "type": "string",
                        "description": "Username to assign the issue to",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to add to the issue",
                    },
                    "custom_fields": {
                        "type": "object",
                        "description": "Custom field values",
                    },
                },
                "required": ["project_key", "summary", "description"],
            },
            metadata={
                "icon": "➕",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="update_jira_issue",
            description="Update an existing Jira issue with new values.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The issue key to update",
                    },
                    "summary": {"type": "string", "description": "New issue summary"},
                    "description": {
                        "type": "string",
                        "description": "New issue description",
                    },
                    "status": {"type": "string", "description": "New status"},
                    "priority": {"type": "string", "description": "New priority level"},
                    "assignee": {
                        "type": "string",
                        "description": "New assignee username",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New labels",
                    },
                    "custom_fields": {
                        "type": "object",
                        "description": "New custom field values",
                    },
                },
                "required": ["issue_key"],
            },
            metadata={
                "icon": "✏️",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="add_jira_comment",
            description="Add a formatted comment to a Jira issue.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "The issue key"},
                    "content": {"type": "string", "description": "Comment content"},
                    "format_type": {
                        "type": "string",
                        "description": "Format type (e.g., 'code', 'quote', 'panel')",
                    },
                    "format_options": {
                        "type": "object",
                        "description": "Additional formatting options",
                    },
                },
                "required": ["issue_key", "content", "format_type"],
            },
            metadata={
                "icon": "💬",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="add_jira_attachment",
            description="Add an attachment to a Jira issue.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "The issue key"},
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to attach",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename for the attachment",
                    },
                },
                "required": ["issue_key", "file_path"],
            },
            metadata={
                "icon": "📎",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="delete_jira_attachment",
            description="Delete an attachment from a Jira issue.",
            category=TOOL_CATEGORIES["jira"],
            inputSchema={
                "type": "object",
                "properties": {
                    "attachment_id": {
                        "type": "string",
                        "description": "The ID of the attachment to delete",
                    },
                },
                "required": ["attachment_id"],
            },
            metadata={
                "icon": "🗑️",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="confluence_create_page_raw",
            description="Advanced tool for creating Confluence pages using direct storage format. Only use this if you need low-level control over the page format. For normal page creation with rich formatting, use 'confluence_create_page' instead.",
            category=TOOL_CATEGORIES["confluence"],
            inputSchema={
                "type": "object",
                "properties": {
                    "space_key": {
                        "type": "string",
                        "description": "Key of the space to create page in",
                    },
                    "title": {
                        "type": "string",
                        "description": "Title for the new page",
                    },
                    "body": {
                        "type": "string",
                        "description": "Content of the page in storage format (Confluence wiki markup)",
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "Optional ID of the parent page",
                    },
                    "representation": {
                        "type": "string",
                        "description": "Content representation ('storage' for wiki markup, 'editor' for rich text)",
                        "default": "storage",
                        "enum": ["storage", "editor"],
                    },
                },
                "required": ["space_key", "title", "body"],
            },
            metadata={
                "icon": "📄",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="confluence_create_page",
            description="Create a new Confluence page with rich formatting. This is the recommended way to create pages with professional formatting. Supports headings, lists, tables, panels, code blocks, and more.",
            category=TOOL_CATEGORIES["confluence"],
            inputSchema={
                "type": "object",
                "properties": {
                    "space_key": {
                        "type": "string",
                        "description": "Key of the space to create page in",
                    },
                    "title": {
                        "type": "string",
                        "description": "Title for the new page",
                    },
                    "content": {
                        "type": "array",
                        "description": "Content blocks in rich text format",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "description": "Type of block: heading, text, list, table, panel, status, code, toc",
                                    "enum": [
                                        "heading",
                                        "text",
                                        "list",
                                        "table",
                                        "panel",
                                        "status",
                                        "code",
                                        "toc",
                                    ],
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Content of the block (required for all types except list)",
                                },
                                "items": {
                                    "type": "array",
                                    "description": "Array of items for list blocks (required for list type)",
                                    "items": {"type": "string"},
                                },
                                "properties": {
                                    "type": "object",
                                    "description": "Block properties",
                                    "properties": {
                                        "level": {
                                            "type": "integer",
                                            "description": "Heading level (1-6)",
                                            "minimum": 1,
                                            "maximum": 6,
                                        },
                                        "language": {
                                            "type": "string",
                                            "description": "Programming language for code blocks",
                                        },
                                        "type": {
                                            "type": "string",
                                            "description": "Panel type (info, note, warning)",
                                            "enum": ["info", "note", "warning"],
                                        },
                                        "color": {
                                            "type": "string",
                                            "description": "Status color (grey, red, yellow, green, blue)",
                                            "enum": [
                                                "grey",
                                                "red",
                                                "yellow",
                                                "green",
                                                "blue",
                                            ],
                                        },
                                        "title": {
                                            "type": "string",
                                            "description": "Title for panels",
                                        },
                                    },
                                },
                                "style": {
                                    "type": "string",
                                    "description": "List style (bullet or numbered)",
                                    "enum": ["bullet", "numbered"],
                                },
                            },
                            "required": ["type"],
                            "allOf": [
                                {
                                    "if": {"properties": {"type": {"const": "list"}}},
                                    "then": {"required": ["items"]},
                                },
                                {
                                    "if": {
                                        "properties": {
                                            "type": {"not": {"const": "list"}}
                                        }
                                    },
                                    "then": {"required": ["content"]},
                                },
                            ],
                        },
                    },
                },
                "required": ["space_key", "title", "content"],
            },
            metadata={
                "icon": "✨",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="confluence_update_page",
            description="Update an existing Confluence page with rich formatting.",
            category=TOOL_CATEGORIES["confluence"],
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "ID of the page to update",
                    },
                    "title": {
                        "type": "string",
                        "description": "Title of the page",
                    },
                    "content": {
                        "type": "array",
                        "description": "Content blocks in rich text format",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "description": "Type of block: heading, text, list, table, panel, status, code, toc",
                                    "enum": [
                                        "heading",
                                        "text",
                                        "list",
                                        "table",
                                        "panel",
                                        "status",
                                        "code",
                                        "toc",
                                    ],
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Content of the block",
                                },
                                "properties": {
                                    "type": "object",
                                    "description": "Block properties like level for headings, language for code, etc.",
                                },
                            },
                            "required": ["type", "content"],
                        },
                    },
                },
                "required": ["page_id", "title", "content"],
            },
            metadata={
                "icon": "✏️",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
    ]
    logger.debug(f"Returning {len(tools)} tools: {[tool.name for tool in tools]}")
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls for Confluence and Jira operations."""
    try:
        # Handle unified search separately as it uses both services
        if name == "unified_search":
            limit = min(int(arguments.get("limit", 10)), 50)
            platforms = arguments.get("platforms")
            results = unified_search.search(
                query=arguments["query"], platforms=platforms, limit=limit
            )
            formatted_results = [
                {
                    "id": result.id,
                    "title": result.title,
                    "content": result.content,
                    "url": result.url,
                    "platform": result.platform,
                    "last_modified": result.last_modified,
                    "content_type": result.content_type,
                    "space_or_project": result.space_or_project,
                    "author": result.author,
                }
                for result in results
            ]
            return [
                TextContent(type="text", text=json.dumps(formatted_results, indent=2))
            ]

        # Handle Confluence tools
        if name.startswith("confluence_") or name in [
            "get_confluence_templates",
            "create_from_confluence_template",
        ]:
            return handle_confluence_tools(
                name, arguments, confluence_fetcher, content_editor
            )

        # Handle Jira tools
        if name.startswith("jira_") or name in [
            "get_jira_templates",
            "create_from_jira_template",
        ]:
            return handle_jira_tools(name, arguments, jira_fetcher)

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}")
        raise RuntimeError(f"Tool execution failed: {str(e)}")


@app.list_resource_templates()
async def list_resource_templates() -> list[Resource]:
    """List available templates for Confluence and Jira."""
    logger.debug("Starting list_resource_templates()")
    templates = []

    # Add Confluence templates
    confluence_templates = confluence_fetcher.get_templates()
    for template in confluence_templates:
        templates.append(
            Resource(
                uri=AnyUrl(f"template://confluence/{template['id']}"),
                name=f"Confluence Template: {template['name']}",
                mimeType="text/plain",
                description=template.get("description", ""),
            )
        )

    # Add Jira templates
    jira_templates = jira_fetcher.get_templates()
    for template in jira_templates:
        templates.append(
            Resource(
                uri=AnyUrl(f"template://jira/{template['id']}"),
                name=f"Jira Template: {template['name']}",
                mimeType="text/plain",
                description=template.get("description", ""),
            )
        )

    logger.debug(f"Returning {len(templates)} templates")
    return templates


async def main():
    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
