import json
import logging
from typing import Sequence
from mcp.types import TextContent

from mcp_atlassian.content import TemplateHandler

logger = logging.getLogger("mcp-atlassian")


def handle_confluence_tools(
    name: str, arguments: dict, confluence_fetcher, content_editor
) -> Sequence[TextContent]:
    """Handle Confluence-related tool calls."""
    try:
        # Ensure content editor has confluence instance
        if not content_editor.confluence:
            content_editor.confluence = confluence_fetcher

        if name == "confluence_search":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 10)

            if not query:
                return [TextContent(type="text", text="Error: Query is required")]

            # Extract title from CQL if provided
            title = query
            if "title =" in query:
                title = query.split("title =")[1].strip().strip('"')
            elif "title ~" in query:
                title = query.split("title ~")[1].strip().strip('"')

            results = confluence_fetcher.search_pages(title, limit)

            if not results:
                return [
                    TextContent(type="text", text="No pages found matching the query")
                ]

            response_texts = []
            for doc in results:
                metadata = doc.metadata
                content = f"""Title: {metadata['title']}
                        Space: {metadata['space_name']} ({metadata['space_key']})
                        URL: {metadata['url']}
                        Last Modified: {metadata['last_modified']}
                        Author: {metadata['author_name']}

                        Content Preview:
                        {doc.page_content[:500]}...
                        """
                response_texts.append(TextContent(type="text", text=content))

            return response_texts

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

        elif name == "get_confluence_templates":
            templates = confluence_fetcher.get_templates(
                space_key=arguments.get("space_key")
            )
            return [TextContent(type="text", text=json.dumps(templates, indent=2))]

        elif name == "create_from_confluence_template":
            template_handler = TemplateHandler()
            result = template_handler.create_from_template(
                space_key=arguments["space_key"],
                template_id=arguments["template_id"],
                title=arguments["title"],
                template_parameters=arguments.get("template_parameters"),
            )

            if result and "error" not in result:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "success": True,
                                "page_id": result["page_id"],
                                "title": result["title"],
                                "url": result["url"],
                                "content": result.get("content", ""),
                            },
                            indent=2,
                        ),
                    )
                ]

            error_msg = (
                result.get("error", "Failed to create page from template")
                if result
                else "Failed to create page from template"
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": error_msg,
                        }
                    ),
                )
            ]

        elif name == "update_confluence_page":
            doc = confluence_fetcher.update_page(
                page_id=arguments["page_id"],
                title=arguments["title"],
                body=arguments["body"],
                minor_edit=arguments["minor_edit"],
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
                        {"success": False, "error": "Failed to update page"},
                        indent=2,
                    ),
                )
            ]

        elif name == "delete_confluence_page":
            success = confluence_fetcher.delete_page(arguments["page_id"])
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": success,
                            "message": (
                                "Page deleted successfully"
                                if success
                                else "Failed to delete page"
                            ),
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "add_confluence_attachment":
            doc = confluence_fetcher.add_attachment(
                page_id=arguments["page_id"],
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

        elif name == "delete_confluence_attachment":
            doc = confluence_fetcher.delete_attachment(arguments["attachment_id"])
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

        elif name == "confluence_create_page_raw":
            doc = confluence_fetcher.create_page(
                space_key=arguments["space_key"],
                title=arguments["title"],
                body=arguments["body"],
                parent_id=arguments.get("parent_id"),
                representation=arguments.get("representation", "storage"),
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
                                "space_key": doc.metadata["space_key"],
                                "url": doc.metadata["url"],
                                "version": doc.metadata["version"],
                            },
                            indent=2,
                        ),
                    )
                ]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"success": False, "error": "Failed to create page"},
                        indent=2,
                    ),
                )
            ]

        elif name == "confluence_create_page":
            try:
                content = arguments.get("content", [])
                if not isinstance(content, list):
                    raise ValueError("Content must be a list of content blocks")

                editor = content_editor.create_editor()

                for block in content:
                    if not isinstance(block, dict) or "type" not in block:
                        continue

                    block_type = block.get("type", "")
                    content = block.get("content", "")
                    props = block.get("properties", {})

                    try:
                        if block_type == "heading":
                            editor.heading(content, props.get("level", 1))
                        elif block_type == "text":
                            if "style" in block:
                                style = block["style"]
                                if style.get("bold"):
                                    content = editor.bold(content)
                                if style.get("italic"):
                                    content = editor.italic(content)
                            editor.text(content)
                        elif block_type == "list":
                            items = block.get("items", [])
                            if not isinstance(items, list):
                                continue
                            if block.get("style") == "numbered":
                                editor.numbered_list(items)
                            else:
                                editor.bullet_list(items)
                        elif block_type == "table":
                            headers = block.get("headers", [])
                            rows = block.get("rows", [])
                            if isinstance(headers, list) and isinstance(rows, list):
                                editor.table(headers, rows)
                        elif block_type == "panel":
                            editor.panel(
                                content,
                                props.get("type", "info"),
                                props.get("title", ""),
                            )
                        elif block_type == "status":
                            editor.status(content, props.get("color", "grey"))
                        elif block_type == "code":
                            editor.code(content, props.get("language", ""))
                        elif block_type == "toc":
                            editor.table_of_contents(
                                props.get("min_level", 1), props.get("max_level", 7)
                            )
                    except Exception as e:
                        logger.error(f"Error processing block type {block_type}: {e}")
                        continue

                # Create the page and get the result
                result = content_editor.create_page(
                    arguments["space_key"], arguments["title"], editor
                )

                if not result:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "success": False,
                                    "error": "Failed to create page - no result returned",
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
                                "success": True,
                                "message": f"Page '{arguments['title']}' created successfully",
                                "page_id": result["page_id"],
                                "title": result["title"],
                                "space_key": result["space_key"],
                                "url": result["url"],
                                "version": result["version"],
                            },
                            indent=2,
                        ),
                    )
                ]
            except Exception as e:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "success": False,
                                "error": f"Failed to create page: {str(e)}",
                            },
                            indent=2,
                        ),
                    )
                ]

        elif name == "confluence_update_page":
            try:
                content = arguments["content"]
                print(
                    f"\nProcessing content for update: {json.dumps(content, indent=2)}"
                )

                if not isinstance(content, list):
                    raise ValueError("Content must be a list of content blocks")

                editor = content_editor.create_editor()
                for block in content:
                    if not isinstance(block, dict) or "type" not in block:
                        raise ValueError(
                            "Each content block must be a dictionary with a 'type' field"
                        )
                    print(f"Processing block: {json.dumps(block, indent=2)}")

                    if block["type"] == "heading":
                        editor.heading(
                            block["content"],
                            block.get("properties", {}).get("level", 1),
                        )
                    elif block["type"] == "text":
                        if "style" in block:
                            if "bold" in block["style"]:
                                editor.bold(block["content"])
                            elif "italic" in block["style"]:
                                editor.italic(block["content"])
                        else:
                            editor.text(block["content"])
                    elif block["type"] == "list":
                        if block.get("style") == "numbered":
                            editor.numbered_list(block["items"])
                        else:
                            editor.bullet_list(block["items"])
                    elif block["type"] == "table":
                        editor.table(block["headers"], block["rows"])
                    elif block["type"] == "panel":
                        props = block.get("properties", {})
                        editor.panel(
                            block["content"],
                            props.get("type", "info"),
                            props.get("title", ""),
                        )
                    elif block["type"] == "status":
                        props = block.get("properties", {})
                        editor.status(block["content"], props.get("color", "grey"))
                    elif block["type"] == "code":
                        props = block.get("properties", {})
                        editor.code(block["content"], props.get("language", ""))
                    elif block["type"] == "toc":
                        props = block.get("properties", {})
                        editor.table_of_contents(
                            props.get("min_level", 1), props.get("max_level", 7)
                        )

                # Convert the content to HTML format
                formatted_content = content_editor.create_rich_content(
                    editor.get_content()
                )
                print(f"\nFormatted content: {formatted_content}")

                if not formatted_content:
                    raise ValueError("Failed to format content")

                # Update the page
                print(
                    f"\nAttempting to update page {arguments['page_id']} with title '{arguments['title']}'"
                )
                result = content_editor.update_page(
                    page_id=arguments["page_id"],
                    title=arguments["title"],
                    body=formatted_content,
                    representation="storage",
                    minor_edit=True,
                )
                print(f"Update result: {result}")

                if result:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "success": True,
                                    "message": f"Page '{arguments['title']}' updated successfully",
                                    "page_id": result["page_id"],
                                    "title": result["title"],
                                    "space_key": result["space_key"],
                                    "version": result["version"],
                                    "url": result["url"],
                                },
                                indent=2,
                            ),
                        )
                    ]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "success": False,
                                    "error": "Failed to update page - page not found or no permission",
                                },
                                indent=2,
                            ),
                        )
                    ]

            except Exception as e:
                print(f"Error during update: {str(e)}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "success": False,
                                "error": f"Failed to update page: {str(e)}",
                            },
                            indent=2,
                        ),
                    )
                ]

        raise ValueError(f"Unknown Confluence tool: {name}")
    except Exception as e:
        logger.error(f"Error handling Confluence tool: {str(e)}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "success": False,
                        "error": f"Failed to handle Confluence tool: {str(e)}",
                    },
                    indent=2,
                ),
            )
        ]
