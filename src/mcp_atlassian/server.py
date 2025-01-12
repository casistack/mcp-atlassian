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
            description="""
### 🔍 Cross-Platform Search

Search across both Confluence and Jira platforms in a single query.

#### Features:
- Full-text search across all content
- Filter by platform (Confluence, Jira)
- Smart result ranking
- Content excerpts with highlights

#### Example:
```json
{
    "query": "deployment process",
    "platforms": ["confluence", "jira"],
    "limit": 5
}
```
            """,
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
            description="""
### 📝 Confluence Search

Search Confluence content using CQL (Confluence Query Language).

#### Features:
- Advanced CQL query support
- Space-specific search
- Content type filtering
- Metadata inclusion

#### Example:
```json
{
    "query": "type=page AND space=DEV AND text~'deployment'",
    "limit": 5
}
```

#### Common CQL Operators:
- `AND`, `OR`, `NOT`
- `~` for text search
- `=` for exact match
- `IN` for multiple values
            """,
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
            description="""
### 📄 Get Confluence Page

Retrieve content and metadata of a specific Confluence page.

#### Features:
- Full page content retrieval
- Optional metadata inclusion
- Version information
- Author and modification details

#### Example:
```json
{
    "page_id": "123456",
    "include_metadata": true
}
```

#### Returns:
- Page content in storage format
- Last modified date
- Version number
- Author information
- Labels and permissions
            """,
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
            description="""
### 💬 Get Confluence Comments

Retrieve all comments for a specific Confluence page.

#### Features:
- Full comment content
- Author information
- Timestamps
- Nested replies
- Formatting preserved

#### Example:
```json
{
    "page_id": "123456"
}
```

#### Returns:
- Comment content
- Author details
- Creation timestamp
- Reply structure
            """,
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
            description="""
### 🎯 Get Jira Issue

Retrieve detailed information about a specific Jira issue.

#### Features:
- Full issue details
- Customizable field expansion
- Rich formatting support
- Attachment information

#### Example:
```json
{
    "issue_key": "PROJ-123",
    "expand": "renderedFields,names,schema,transitions,operations,editmeta,changelog"
}
```

#### Common Expand Options:
- `renderedFields`: Get formatted field values
- `transitions`: Include available status transitions
- `changelog`: Include issue history
- `comments`: Include all comments
            """,
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
            description="""
### 🔎 Jira Search

Search Jira issues using JQL (Jira Query Language).

#### Features:
- Advanced JQL query support
- Custom field selection
- Result limiting
- Rich metadata

#### Example:
```json
{
    "jql": "project = PROJ AND status = 'In Progress' ORDER BY priority DESC",
    "fields": "summary,description,status,priority",
    "limit": 10
}
```

#### Common JQL Operators:
- `=`, `!=`, `>`, `>=`, `<`, `<=`
- `IN`, `NOT IN`
- `~` for contains
- `IS NULL`, `IS NOT NULL`
- `ORDER BY`, `DESC`, `ASC`
            """,
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
            description="""
### 📊 Get Project Issues

Retrieve all issues from a specific Jira project with pagination support.

#### Features:
- Project-wide issue listing
- Pagination support
- Basic issue details
- Sorting options

#### Example:
```json
{
    "project_key": "PROJ",
    "limit": 20
}
```

#### Returns:
- Issue key
- Title
- Type
- Status
- Creation date
- Issue URL
            """,
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
            description="""
### 📑 List Confluence Templates

Get all available Confluence templates, including blueprints and custom templates.

#### Features:
- Blueprint templates
- Custom templates
- Space templates
- Template metadata

#### Returns:
- Template ID
- Name
- Description
- Space key (if space-specific)
- Labels
            """,
            category=TOOL_CATEGORIES["templates"],
            inputSchema={
                "type": "object",
                "properties": {},
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
            description="""
### 📝 List Jira Templates

Get all available Jira issue templates.

#### Features:
- Project templates
- Shared templates
- Custom field defaults
- Template metadata

#### Returns:
- Template ID
- Name
- Description
- Project key (if project-specific)
- Issue type
- Field mappings
            """,
            category=TOOL_CATEGORIES["templates"],
            inputSchema={
                "type": "object",
                "properties": {},
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
            description="""
### 📋 Create from Confluence Template

Create a new Confluence page using a predefined template.

#### Features:
- Template-based page creation
- Variable substitution
- Rich content formatting
- Automatic space organization

#### Example:
```json
{
    "template_id": "com.atlassian.confluence.plugins.confluence-create-content-plugin:create-blank-page",
    "space_key": "TEAM",
    "title": "Project Requirements",
    "template_parameters": {
        "project_name": "MCP Integration",
        "team": "Backend",
        "start_date": "2024-01-15"
    }
}
```

#### Template Types:
- Blank pages
- Meeting notes
- Product requirements
- Decision documents
- How-to guides
            """,
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
            description="""
### ✨ Create Jira Issue from Template

Create a new Jira issue using a predefined template.

#### Features:
- Template-based issue creation
- Variable substitution
- Custom field support
- Automatic assignments

#### Example:
```json
{
    "template_id": "bug-report",
    "project_key": "PROJ",
    "summary": "Critical: Database Connection Error",
    "template_parameters": {
        "severity": "Critical",
        "environment": "Production",
        "affected_version": "2.1.0"
    }
}
```

#### Template Parameters:
- Project-specific fields
- Custom fields
- Dynamic variables
- Assignee rules
            """,
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
            description="""
### 🔄 Get Issue Transitions

Get all available status transitions for a Jira issue.

#### Features:
- Current status
- Available transitions
- Required fields
- Transition rules

#### Example:
```json
{
    "issue_key": "PROJ-123"
}
```

#### Returns:
- Transition ID
- Target status
- Screen requirements
- Validation rules
            """,
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
            description="""
### ✏️ Update Issue Section

Update a specific section of a Jira issue description by heading.

#### Features:
- Section-based updates
- Markdown support
- Heading preservation
- Content formatting

#### Example:
```json
{
    "issue_key": "PROJ-123",
    "heading": "Technical Details",
    "content": "Updated technical specifications and implementation notes..."
}
```

#### Usage Notes:
- Preserves other sections
- Maintains formatting
- Creates section if not found
- Supports rich text
            """,
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
            description="""
### 📎 Get Issue Attachments

Retrieve all attachments for a specific Jira issue.

#### Features:
- File metadata
- Download URLs
- Creator information
- Size and type details

#### Example:
```json
{
    "issue_key": "PROJ-123"
}
```

#### Returns:
- File name
- Content type
- File size
- Creation date
- Creator
- Download URL
            """,
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
    ]
    logger.debug(f"Returning {len(tools)} tools: {[tool.name for tool in tools]}")
    return tools


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

        elif name == "get_jira_issue_transitions":
            transitions = jira_fetcher.get_issue_transitions(arguments["issue_key"])
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"success": True, "transitions": transitions}, indent=2
                    ),
                )
            ]

        elif name == "update_jira_section":
            doc = jira_fetcher.update_issue_section(
                issue_key=arguments["issue_key"],
                heading=arguments["heading"],
                new_content=arguments["content"],
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
                        {"success": False, "error": "Failed to update section"},
                        indent=2,
                    ),
                )
            ]

        elif name == "get_jira_attachments":
            attachments = jira_fetcher.get_attachments(arguments["issue_key"])
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
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
                        },
                        indent=2,
                    ),
                )
            ]

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
