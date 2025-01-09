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
from .content import TemplateHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-atlassian")

# Initialize the content fetchers
confluence_fetcher = ConfluenceFetcher()
jira_fetcher = JiraFetcher()
unified_search = UnifiedSearch(confluence_fetcher, jira_fetcher)
app = Server("mcp-atlassian")


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
    return [
        Tool(
            name="unified_search",
            description="Search across both Confluence and Jira platforms",
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
        ),
        Tool(
            name="confluence_search",
            description="Search Confluence content using CQL",
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
        ),
        Tool(
            name="confluence_get_page",
            description="Get content of a specific Confluence page by ID",
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
        ),
        Tool(
            name="confluence_get_comments",
            description="Get comments for a specific Confluence page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Confluence page ID"}
                },
                "required": ["page_id"],
            },
        ),
        Tool(
            name="jira_get_issue",
            description="Get details of a specific Jira issue",
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
        ),
        Tool(
            name="jira_search",
            description="Search Jira issues using JQL",
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
        ),
        Tool(
            name="jira_get_project_issues",
            description="Get all issues for a specific Jira project",
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
        ),
        Tool(
            name="get_confluence_templates",
            description="Get available Confluence templates (blueprints and custom templates)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_jira_templates",
            description="Get available Jira issue templates",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="create_from_confluence_template",
            description="Create a new Confluence page from a template",
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
        ),
        Tool(
            name="create_from_jira_template",
            description="Create a new Jira issue from a template",
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
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls for Confluence and Jira operations."""
    try:
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

        elif name == "confluence_search":
            limit = min(int(arguments.get("limit", 10)), 50)
            documents = confluence_fetcher.search(arguments["query"], limit)
            search_results = [
                {
                    "page_id": doc.metadata["page_id"],
                    "title": doc.metadata["title"],
                    "space": doc.metadata["space"],
                    "url": doc.metadata["url"],
                    "last_modified": doc.metadata["last_modified"],
                    "type": doc.metadata["type"],
                    "excerpt": doc.page_content,
                }
                for doc in documents
            ]

            return [TextContent(type="text", text=json.dumps(search_results, indent=2))]

        elif name == "confluence_get_page":
            doc = confluence_fetcher.get_page_content(arguments["page_id"])
            include_metadata = arguments.get("include_metadata", True)

            if include_metadata:
                result = {"content": doc.page_content, "metadata": doc.metadata}
            else:
                result = {"content": doc.page_content}

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "confluence_get_comments":
            comments = confluence_fetcher.get_page_comments(arguments["page_id"])
            formatted_comments = [
                {
                    "author": comment.metadata["author_name"],
                    "created": comment.metadata["last_modified"],
                    "content": comment.page_content,
                }
                for comment in comments
            ]

            return [
                TextContent(type="text", text=json.dumps(formatted_comments, indent=2))
            ]

        elif name == "jira_get_issue":
            doc = jira_fetcher.get_issue(
                arguments["issue_key"], expand=arguments.get("expand")
            )
            result = {"content": doc.page_content, "metadata": doc.metadata}
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_search":
            limit = min(int(arguments.get("limit", 10)), 50)
            documents = jira_fetcher.search_issues(
                arguments["jql"], fields=arguments.get("fields", "*all"), limit=limit
            )
            search_results = [
                {
                    "key": doc.metadata["key"],
                    "title": doc.metadata["title"],
                    "type": doc.metadata["type"],
                    "status": doc.metadata["status"],
                    "created_date": doc.metadata["created_date"],
                    "priority": doc.metadata["priority"],
                    "link": doc.metadata["link"],
                    "excerpt": (
                        doc.page_content[:500] + "..."
                        if len(doc.page_content) > 500
                        else doc.page_content
                    ),
                }
                for doc in documents
            ]
            return [TextContent(type="text", text=json.dumps(search_results, indent=2))]

        elif name == "jira_get_project_issues":
            limit = min(int(arguments.get("limit", 10)), 50)
            documents = jira_fetcher.get_project_issues(
                arguments["project_key"], limit=limit
            )
            project_issues = [
                {
                    "key": doc.metadata["key"],
                    "title": doc.metadata["title"],
                    "type": doc.metadata["type"],
                    "status": doc.metadata["status"],
                    "created_date": doc.metadata["created_date"],
                    "link": doc.metadata["link"],
                }
                for doc in documents
            ]
            return [TextContent(type="text", text=json.dumps(project_issues, indent=2))]

        elif name == "get_confluence_templates":
            templates = TemplateHandler.get_confluence_templates(
                confluence_fetcher.confluence
            )
            return [TextContent(type="text", text=json.dumps(templates, indent=2))]

        elif name == "get_jira_templates":
            templates = TemplateHandler.get_jira_templates(jira_fetcher.jira)
            return [TextContent(type="text", text=json.dumps(templates, indent=2))]

        elif name == "create_from_confluence_template":
            content = TemplateHandler.apply_confluence_template(
                confluence_fetcher.confluence,
                template_id=arguments["template_id"],
                space_key=arguments["space_key"],
                title=arguments["title"],
                template_parameters=arguments.get("template_parameters"),
            )

            if content:
                # Create the page with template content
                doc = confluence_fetcher.create_page(
                    space_key=arguments["space_key"],
                    title=arguments["title"],
                    body=content,
                    representation="storage",
                )

                if doc:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "success": True,
                                    "page_id": doc.metadata["page_id"],
                                    "title": doc.metadata["title"],
                                    "url": doc.metadata["url"],
                                    "content": doc.page_content,
                                },
                                indent=2,
                            ),
                        )
                    ]

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": "Failed to create page from template",
                        }
                    ),
                )
            ]

        elif name == "create_from_jira_template":
            fields = TemplateHandler.apply_jira_template(
                jira_fetcher.jira,
                template_id=arguments["template_id"],
                project_key=arguments["project_key"],
                summary=arguments["summary"],
                template_parameters=arguments.get("template_parameters"),
            )

            if fields:
                # Create the issue with template fields
                doc = jira_fetcher.create_issue(
                    project_key=arguments["project_key"],
                    summary=arguments["summary"],
                    **fields,
                )

                if doc:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "success": True,
                                    "key": doc.metadata["key"],
                                    "title": doc.metadata["title"],
                                    "status": doc.metadata["status"],
                                    "type": doc.metadata["type"],
                                    "url": doc.metadata["link"],
                                    "description": doc.page_content,
                                },
                                indent=2,
                            ),
                        )
                    ]

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": "Failed to create issue from template",
                        }
                    ),
                )
            ]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}")
        raise RuntimeError(f"Tool execution failed: {str(e)}")


@app.tool()
async def create_confluence_page(
    space_key: str,
    title: str,
    content: str,
    parent_id: str | None = None,
) -> dict[str, Any]:
    """Create a new page in Confluence.

    Args:
        space_key: The key of the space where the page will be created
        title: The title of the new page
        content: The content of the page in storage format (wiki markup)
        parent_id: Optional ID of the parent page

    Returns:
        Dictionary containing the page details if successful
    """
    try:
        doc = confluence_fetcher.create_page(
            space_key=space_key,
            title=title,
            body=content,
            parent_id=parent_id,
            representation="storage",
        )
        if doc:
            return {
                "success": True,
                "page_id": doc.metadata["page_id"],
                "title": doc.metadata["title"],
                "url": doc.metadata["url"],
                "content": doc.page_content,
            }
        return {"success": False, "error": "Failed to create page"}
    except Exception as e:
        logger.error(f"Error creating Confluence page: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def update_confluence_page(
    page_id: str,
    title: str,
    content: str,
    minor_edit: bool = False,
) -> dict[str, Any]:
    """Update an existing page in Confluence.

    Args:
        page_id: The ID of the page to update
        title: The new title of the page
        content: The new content in storage format (wiki markup)
        minor_edit: Whether this is a minor edit

    Returns:
        Dictionary containing the updated page details if successful
    """
    try:
        doc = confluence_fetcher.update_page(
            page_id=page_id,
            title=title,
            body=content,
            representation="storage",
            minor_edit=minor_edit,
        )
        if doc:
            return {
                "success": True,
                "page_id": doc.metadata["page_id"],
                "title": doc.metadata["title"],
                "url": doc.metadata["url"],
                "content": doc.page_content,
            }
        return {"success": False, "error": "Failed to update page"}
    except Exception as e:
        logger.error(f"Error updating Confluence page: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def create_jira_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    priority: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new Jira issue.

    Args:
        project_key: The project key where the issue will be created
        summary: The issue summary/title
        description: The issue description
        issue_type: The type of issue (e.g., 'Task', 'Bug', 'Story')
        priority: Optional priority level
        assignee: Optional username to assign the issue to
        labels: Optional list of labels

    Returns:
        Dictionary containing the issue details if successful
    """
    try:
        doc = jira_fetcher.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=priority,
            assignee=assignee,
            labels=labels,
        )
        if doc:
            return {
                "success": True,
                "key": doc.metadata["key"],
                "title": doc.metadata["title"],
                "status": doc.metadata["status"],
                "type": doc.metadata["type"],
                "priority": doc.metadata.get("priority"),
                "assignee": doc.metadata.get("assignee"),
                "url": doc.metadata["link"],
                "description": doc.page_content,
            }
        return {"success": False, "error": "Failed to create issue"}
    except Exception as e:
        logger.error(f"Error creating Jira issue: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def update_jira_issue(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Update an existing Jira issue.

    Args:
        issue_key: The issue key to update
        summary: Optional new summary/title
        description: Optional new description
        status: Optional new status
        priority: Optional new priority level
        assignee: Optional username to assign the issue to
        labels: Optional list of labels

    Returns:
        Dictionary containing the updated issue details if successful
    """
    try:
        doc = jira_fetcher.update_issue(
            issue_key=issue_key,
            summary=summary,
            description=description,
            status=status,
            priority=priority,
            assignee=assignee,
            labels=labels,
        )
        if doc:
            return {
                "success": True,
                "key": doc.metadata["key"],
                "title": doc.metadata["title"],
                "status": doc.metadata["status"],
                "type": doc.metadata["type"],
                "priority": doc.metadata.get("priority"),
                "assignee": doc.metadata.get("assignee"),
                "url": doc.metadata["link"],
                "description": doc.page_content,
            }
        return {"success": False, "error": "Failed to update issue"}
    except Exception as e:
        logger.error(f"Error updating Jira issue: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def get_jira_issue_transitions(issue_key: str) -> dict[str, Any]:
    """Get available status transitions for a Jira issue.

    Args:
        issue_key: The issue key to get transitions for

    Returns:
        Dictionary containing the list of available transitions
    """
    try:
        transitions = jira_fetcher.get_issue_transitions(issue_key)
        return {"success": True, "transitions": transitions}
    except Exception as e:
        logger.error(f"Error getting issue transitions: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def update_confluence_section(
    page_id: str,
    heading: str,
    content: str,
    minor_edit: bool = False,
) -> dict[str, Any]:
    """Update a specific section of a Confluence page.

    Args:
        page_id: The ID of the page to update
        heading: The heading text that identifies the section
        content: The new content for the section
        minor_edit: Whether this is a minor edit

    Returns:
        Dictionary containing the updated page details if successful
    """
    try:
        doc = confluence_fetcher.update_page_section(
            page_id=page_id,
            heading=heading,
            new_content=content,
            minor_edit=minor_edit,
        )
        if doc:
            return {
                "success": True,
                "page_id": doc.metadata["page_id"],
                "title": doc.metadata["title"],
                "url": doc.metadata["url"],
                "content": doc.page_content,
            }
        return {"success": False, "error": "Failed to update section"}
    except Exception as e:
        logger.error(f"Error updating page section: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def insert_after_confluence_section(
    page_id: str,
    heading: str,
    content: str,
    minor_edit: bool = False,
) -> dict[str, Any]:
    """Insert content after a specific section in a Confluence page.

    Args:
        page_id: The ID of the page to update
        heading: The heading text after which to insert content
        content: The content to insert
        minor_edit: Whether this is a minor edit

    Returns:
        Dictionary containing the updated page details if successful
    """
    try:
        doc = confluence_fetcher.insert_after_section(
            page_id=page_id,
            heading=heading,
            new_content=content,
            minor_edit=minor_edit,
        )
        if doc:
            return {
                "success": True,
                "page_id": doc.metadata["page_id"],
                "title": doc.metadata["title"],
                "url": doc.metadata["url"],
                "content": doc.page_content,
            }
        return {"success": False, "error": "Failed to insert content"}
    except Exception as e:
        logger.error(f"Error inserting content: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def append_to_confluence_list(
    page_id: str,
    heading: str,
    list_marker: str,
    item: str,
    minor_edit: bool = False,
) -> dict[str, Any]:
    """Append an item to a list in a specific section of a Confluence page.

    Args:
        page_id: The ID of the page to update
        heading: The heading text that identifies the section
        list_marker: The marker that identifies the list ('*' for bullet, '#' for numbered)
        item: The new list item to append
        minor_edit: Whether this is a minor edit

    Returns:
        Dictionary containing the updated page details if successful
    """
    try:
        doc = confluence_fetcher.append_to_list_in_section(
            page_id=page_id,
            heading=heading,
            list_marker=list_marker,
            new_item=item,
            minor_edit=minor_edit,
        )
        if doc:
            return {
                "success": True,
                "page_id": doc.metadata["page_id"],
                "title": doc.metadata["title"],
                "url": doc.metadata["url"],
                "content": doc.page_content,
            }
        return {"success": False, "error": "Failed to append list item"}
    except Exception as e:
        logger.error(f"Error appending to list: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def update_confluence_table(
    page_id: str,
    heading: str,
    table_start: str,
    row_identifier: str,
    new_values: list[str],
    minor_edit: bool = False,
) -> dict[str, Any]:
    """Update a specific row in a table within a section of a Confluence page.

    Args:
        page_id: The ID of the page to update
        heading: The heading text that identifies the section
        table_start: Text that uniquely identifies the table
        row_identifier: Text that uniquely identifies the row to update
        new_values: New values for the row cells
        minor_edit: Whether this is a minor edit

    Returns:
        Dictionary containing the updated page details if successful
    """
    try:
        doc = confluence_fetcher.update_table_in_section(
            page_id=page_id,
            heading=heading,
            table_start=table_start,
            row_identifier=row_identifier,
            new_values=new_values,
            minor_edit=minor_edit,
        )
        if doc:
            return {
                "success": True,
                "page_id": doc.metadata["page_id"],
                "title": doc.metadata["title"],
                "url": doc.metadata["url"],
                "content": doc.page_content,
            }
        return {"success": False, "error": "Failed to update table"}
    except Exception as e:
        logger.error(f"Error updating table: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def format_confluence_content(
    format_type: str,
    content: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Format content using Confluence markup.

    Args:
        format_type: Type of formatting to apply ('heading', 'bullet_list', 'numbered_list',
                    'code_block', 'table', 'quote', 'link', 'bold', 'italic')
        content: The content to format
        **kwargs: Additional formatting options

    Returns:
        Dictionary containing the formatted content
    """
    try:
        from .content import MarkupFormatter

        formatter = getattr(MarkupFormatter, format_type, None)
        if not formatter:
            return {"success": False, "error": f"Unknown format type: {format_type}"}

        formatted_content = formatter(content, **kwargs)
        return {"success": True, "content": formatted_content}
    except Exception as e:
        logger.error(f"Error formatting content: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def update_jira_section(
    issue_key: str,
    heading: str,
    content: str,
) -> dict[str, Any]:
    """Update a specific section of a Jira issue description.

    Args:
        issue_key: The issue key to update
        heading: The heading text that identifies the section
        content: The new content for the section

    Returns:
        Dictionary containing the updated issue details if successful
    """
    try:
        doc = jira_fetcher.update_issue_section(
            issue_key=issue_key,
            heading=heading,
            new_content=content,
        )
        if doc:
            return {
                "success": True,
                "key": doc.metadata["key"],
                "title": doc.metadata["title"],
                "status": doc.metadata["status"],
                "type": doc.metadata["type"],
                "url": doc.metadata["link"],
                "description": doc.page_content,
            }
        return {"success": False, "error": "Failed to update section"}
    except Exception as e:
        logger.error(f"Error updating issue section: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def insert_after_jira_section(
    issue_key: str,
    heading: str,
    content: str,
) -> dict[str, Any]:
    """Insert content after a specific section in a Jira issue description.

    Args:
        issue_key: The issue key to update
        heading: The heading text after which to insert content
        content: The content to insert

    Returns:
        Dictionary containing the updated issue details if successful
    """
    try:
        doc = jira_fetcher.insert_after_issue_section(
            issue_key=issue_key,
            heading=heading,
            new_content=content,
        )
        if doc:
            return {
                "success": True,
                "key": doc.metadata["key"],
                "title": doc.metadata["title"],
                "status": doc.metadata["status"],
                "type": doc.metadata["type"],
                "url": doc.metadata["link"],
                "description": doc.page_content,
            }
        return {"success": False, "error": "Failed to insert content"}
    except Exception as e:
        logger.error(f"Error inserting content: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def append_to_jira_list(
    issue_key: str,
    heading: str,
    list_marker: str,
    item: str,
) -> dict[str, Any]:
    """Append an item to a list in a specific section of a Jira issue.

    Args:
        issue_key: The issue key to update
        heading: The heading text that identifies the section
        list_marker: The marker that identifies the list ('*' for bullet, '#' for numbered)
        item: The new list item to append

    Returns:
        Dictionary containing the updated issue details if successful
    """
    try:
        doc = jira_fetcher.append_to_list_in_issue(
            issue_key=issue_key,
            heading=heading,
            list_marker=list_marker,
            new_item=item,
        )
        if doc:
            return {
                "success": True,
                "key": doc.metadata["key"],
                "title": doc.metadata["title"],
                "status": doc.metadata["status"],
                "type": doc.metadata["type"],
                "url": doc.metadata["link"],
                "description": doc.page_content,
            }
        return {"success": False, "error": "Failed to append list item"}
    except Exception as e:
        logger.error(f"Error appending to list: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def update_jira_table(
    issue_key: str,
    heading: str,
    table_start: str,
    row_identifier: str,
    new_values: list[str],
) -> dict[str, Any]:
    """Update a specific row in a table within a section of a Jira issue.

    Args:
        issue_key: The issue key to update
        heading: The heading text that identifies the section
        table_start: Text that uniquely identifies the table
        row_identifier: Text that uniquely identifies the row to update
        new_values: New values for the row cells

    Returns:
        Dictionary containing the updated issue details if successful
    """
    try:
        doc = jira_fetcher.update_table_in_issue(
            issue_key=issue_key,
            heading=heading,
            table_start=table_start,
            row_identifier=row_identifier,
            new_values=new_values,
        )
        if doc:
            return {
                "success": True,
                "key": doc.metadata["key"],
                "title": doc.metadata["title"],
                "status": doc.metadata["status"],
                "type": doc.metadata["type"],
                "url": doc.metadata["link"],
                "description": doc.page_content,
            }
        return {"success": False, "error": "Failed to update table"}
    except Exception as e:
        logger.error(f"Error updating table: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def add_formatted_jira_comment(
    issue_key: str,
    content: str,
    format_type: str,
    **format_options: Any,
) -> dict[str, Any]:
    """Add a formatted comment to a Jira issue.

    Args:
        issue_key: The issue key to add the comment to
        content: The comment content
        format_type: Type of formatting to apply ('heading', 'bullet_list', 'numbered_list',
                    'code_block', 'table', 'quote', 'link', 'bold', 'italic')
        **format_options: Additional formatting options

    Returns:
        Dictionary containing the updated issue details if successful
    """
    try:
        doc = jira_fetcher.add_comment_with_formatting(
            issue_key=issue_key,
            content=content,
            format_type=format_type,
            **format_options,
        )
        if doc:
            return {
                "success": True,
                "key": doc.metadata["key"],
                "title": doc.metadata["title"],
                "status": doc.metadata["status"],
                "type": doc.metadata["type"],
                "url": doc.metadata["link"],
                "description": doc.page_content,
            }
        return {"success": False, "error": "Failed to add formatted comment"}
    except Exception as e:
        logger.error(f"Error adding formatted comment: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def get_confluence_attachments(page_id: str) -> dict[str, Any]:
    """Get all attachments for a Confluence page.

    Args:
        page_id: The ID of the page

    Returns:
        Dictionary containing the list of attachments
    """
    try:
        attachments = confluence_fetcher.get_attachments(page_id)
        return {
            "success": True,
            "attachments": [
                {
                    "id": att.id,
                    "filename": att.filename,
                    "content_type": att.content_type,
                    "size": att.size,
                    "url": att.url,
                    "created": att.created,
                    "creator": att.creator,
                }
                for att in attachments
            ],
        }
    except Exception as e:
        logger.error(f"Error getting Confluence attachments: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def get_confluence_attachment_content(attachment_id: str) -> dict[str, Any]:
    """Get the content of a Confluence attachment.

    Args:
        attachment_id: The ID of the attachment

    Returns:
        Dictionary containing the attachment content as base64
    """
    try:
        content = confluence_fetcher.get_attachment_content(attachment_id)
        if content:
            return {
                "success": True,
                "content": base64.b64encode(content).decode("utf-8"),
            }
        return {"success": False, "error": "Failed to get attachment content"}
    except Exception as e:
        logger.error(f"Error getting Confluence attachment content: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def add_confluence_attachment(
    page_id: str,
    file_path: str,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
) -> dict[str, Any]:
    """Add an attachment to a Confluence page.

    Args:
        page_id: The ID of the page to attach to
        file_path: Path to the file to attach
        filename: Optional filename to use (defaults to basename of file_path)
        content_type: Optional content type (will be guessed if not provided)

    Returns:
        Dictionary containing the attachment details if successful
    """
    try:
        attachment = confluence_fetcher.add_attachment(
            page_id=page_id,
            file=Path(file_path),
            filename=filename,
            content_type=content_type,
        )
        if attachment:
            return {
                "success": True,
                "id": attachment.id,
                "filename": attachment.filename,
                "content_type": attachment.content_type,
                "size": attachment.size,
                "url": attachment.url,
                "created": attachment.created,
                "creator": attachment.creator,
            }
        return {"success": False, "error": "Failed to add attachment"}
    except Exception as e:
        logger.error(f"Error adding Confluence attachment: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def update_confluence_attachment(
    attachment_id: str,
    file_path: str,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
) -> dict[str, Any]:
    """Update an existing Confluence attachment.

    Args:
        attachment_id: The ID of the attachment to update
        file_path: Path to the new file content
        filename: Optional new filename
        content_type: Optional new content type

    Returns:
        Dictionary containing the updated attachment details if successful
    """
    try:
        attachment = confluence_fetcher.update_attachment(
            attachment_id=attachment_id,
            file=Path(file_path),
            filename=filename,
            content_type=content_type,
        )
        if attachment:
            return {
                "success": True,
                "id": attachment.id,
                "filename": attachment.filename,
                "content_type": attachment.content_type,
                "size": attachment.size,
                "url": attachment.url,
                "created": attachment.created,
                "creator": attachment.creator,
            }
        return {"success": False, "error": "Failed to update attachment"}
    except Exception as e:
        logger.error(f"Error updating Confluence attachment: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def delete_confluence_attachment(attachment_id: str) -> dict[str, Any]:
    """Delete a Confluence attachment.

    Args:
        attachment_id: The ID of the attachment to delete

    Returns:
        Dictionary indicating success or failure
    """
    try:
        success = confluence_fetcher.delete_attachment(attachment_id)
        return {
            "success": success,
            "error": None if success else "Failed to delete attachment",
        }
    except Exception as e:
        logger.error(f"Error deleting Confluence attachment: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def get_jira_attachments(issue_key: str) -> dict[str, Any]:
    """Get all attachments for a Jira issue.

    Args:
        issue_key: The issue key

    Returns:
        Dictionary containing the list of attachments
    """
    try:
        attachments = jira_fetcher.get_attachments(issue_key)
        return {
            "success": True,
            "attachments": [
                {
                    "id": att.id,
                    "filename": att.filename,
                    "content_type": att.content_type,
                    "size": att.size,
                    "url": att.url,
                    "created": att.created,
                    "creator": att.creator,
                }
                for att in attachments
            ],
        }
    except Exception as e:
        logger.error(f"Error getting Jira attachments: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def get_jira_attachment_content(attachment_id: str) -> dict[str, Any]:
    """Get the content of a Jira attachment.

    Args:
        attachment_id: The ID of the attachment

    Returns:
        Dictionary containing the attachment content as base64
    """
    try:
        content = jira_fetcher.get_attachment_content(attachment_id)
        if content:
            return {
                "success": True,
                "content": base64.b64encode(content).decode("utf-8"),
            }
        return {"success": False, "error": "Failed to get attachment content"}
    except Exception as e:
        logger.error(f"Error getting Jira attachment content: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def add_jira_attachment(
    issue_key: str,
    file_path: str,
    filename: Optional[str] = None,
) -> dict[str, Any]:
    """Add an attachment to a Jira issue.

    Args:
        issue_key: The issue key to attach to
        file_path: Path to the file to attach
        filename: Optional filename to use (defaults to basename of file_path)

    Returns:
        Dictionary containing the attachment details if successful
    """
    try:
        attachment = jira_fetcher.add_attachment(
            issue_key=issue_key,
            file=Path(file_path),
            filename=filename,
        )
        if attachment:
            return {
                "success": True,
                "id": attachment.id,
                "filename": attachment.filename,
                "content_type": attachment.content_type,
                "size": attachment.size,
                "url": attachment.url,
                "created": attachment.created,
                "creator": attachment.creator,
            }
        return {"success": False, "error": "Failed to add attachment"}
    except Exception as e:
        logger.error(f"Error adding Jira attachment: {e}")
        return {"success": False, "error": str(e)}


@app.tool()
async def delete_jira_attachment(attachment_id: str) -> dict[str, Any]:
    """Delete a Jira attachment.

    Args:
        attachment_id: The ID of the attachment to delete

    Returns:
        Dictionary indicating success or failure
    """
    try:
        success = jira_fetcher.delete_attachment(attachment_id)
        return {
            "success": success,
            "error": None if success else "Failed to delete attachment",
        }
    except Exception as e:
        logger.error(f"Error deleting Jira attachment: {e}")
        return {"success": False, "error": str(e)}


async def main():
    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
