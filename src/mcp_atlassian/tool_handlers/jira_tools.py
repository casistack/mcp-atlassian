import json
import logging
from typing import Sequence
from mcp.types import TextContent

from mcp_atlassian.content import TemplateHandler

logger = logging.getLogger("mcp-atlassian")


def handle_jira_tools(
    name: str, arguments: dict, jira_fetcher
) -> Sequence[TextContent]:
    """Handle all Jira-related tool calls."""

    if name == "jira_get_issue":
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

    elif name == "get_jira_templates":
        templates = jira_fetcher.get_templates(project_key=arguments.get("project_key"))
        return [TextContent(type="text", text=json.dumps(templates, indent=2))]

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

    elif name == "create_jira_issue":
        doc = jira_fetcher.create_issue(
            project_key=arguments["project_key"],
            summary=arguments["summary"],
            description=arguments["description"],
            issue_type=arguments["issue_type"],
            priority=arguments["priority"],
            assignee=arguments["assignee"],
            labels=arguments["labels"],
            custom_fields=arguments["custom_fields"],
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
                    {"success": False, "error": "Failed to create issue"},
                    indent=2,
                ),
            )
        ]

    elif name == "update_jira_issue":
        doc = jira_fetcher.update_issue(
            issue_key=arguments["issue_key"],
            summary=arguments["summary"],
            description=arguments["description"],
            status=arguments["status"],
            priority=arguments["priority"],
            assignee=arguments["assignee"],
            labels=arguments["labels"],
            custom_fields=arguments["custom_fields"],
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
                    {"success": False, "error": "Failed to update issue"},
                    indent=2,
                ),
            )
        ]

    elif name == "add_jira_comment":
        doc = jira_fetcher.add_comment(
            issue_key=arguments["issue_key"],
            content=arguments["content"],
            format_type=arguments["format_type"],
            format_options=arguments["format_options"],
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
                    {"success": False, "error": "Failed to add comment"},
                    indent=2,
                ),
            )
        ]

    elif name == "add_jira_attachment":
        doc = jira_fetcher.add_attachment(
            issue_key=arguments["issue_key"],
            file_path=arguments["file_path"],
            filename=arguments["filename"],
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
                    {"success": False, "error": "Failed to add attachment"},
                    indent=2,
                ),
            )
        ]

    elif name == "delete_jira_attachment":
        doc = jira_fetcher.delete_attachment(arguments["attachment_id"])
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
                    {"success": False, "error": "Failed to delete attachment"},
                    indent=2,
                ),
            )
        ]

    raise ValueError(f"Unknown Jira tool: {name}")
