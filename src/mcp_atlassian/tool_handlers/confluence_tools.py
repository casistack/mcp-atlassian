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
                space_key = arguments["space_key"]
                logger.info(f"Attempting to create page in space: {space_key}")

                # Validate space key first
                is_valid, correct_key = confluence_fetcher.validate_space_key(space_key)
                logger.info(
                    f"Space key validation result - is_valid: {is_valid}, correct_key: {correct_key}"
                )

                if not is_valid:
                    if correct_key:
                        logger.info(
                            f"Using correct space key: {correct_key} instead of: {space_key}"
                        )
                        space_key = correct_key
                    else:
                        logger.warning(f"Invalid space key: {space_key}")
                        return [
                            TextContent(
                                type="text",
                                text=json.dumps(
                                    {
                                        "success": False,
                                        "error": f"Invalid space key: {space_key}. Please check the space name or key.",
                                    },
                                    indent=2,
                                ),
                            )
                        ]

                # Get content from arguments
                content = arguments.get("content", [])
                logger.info(f"Content blocks to process: {len(content)}")

                if not content:
                    logger.warning("Content list is empty")
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "success": False,
                                    "error": "Content list cannot be empty",
                                },
                                indent=2,
                            ),
                        )
                    ]

                if not isinstance(content, list):
                    logger.error("Content is not a list")
                    raise ValueError("Content must be a list of content blocks")

                # Create the content in storage format
                storage_content = []
                for block in content:
                    if not isinstance(block, dict) or "type" not in block:
                        logger.warning(f"Skipping invalid block: {block}")
                        continue

                    block_type = block.get("type", "")
                    block_content = block.get("content", "")
                    logger.info(f"Processing block type: {block_type}")

                    try:
                        if block_type == "text":
                            storage_content.append(f"<p>{block_content}</p>")
                        elif block_type == "heading":
                            level = block.get("properties", {}).get("level", 1)
                            storage_content.append(
                                f"<h{level}>{block_content}</h{level}>"
                            )
                        elif block_type == "list":
                            items = block.get("items", [])
                            if not isinstance(items, list):
                                continue
                            list_type = (
                                "ol" if block.get("style") == "numbered" else "ul"
                            )
                            items_html = "".join(f"<li>{item}</li>" for item in items)
                            storage_content.append(
                                f"<{list_type}>{items_html}</{list_type}>"
                            )
                        elif block_type == "panel":
                            props = block.get("properties", {})
                            panel_type = props.get("type", "info")
                            title = props.get("title", "")
                            storage_content.append(
                                f'<ac:structured-macro ac:name="panel">'
                                f'<ac:parameter ac:name="title">{title}</ac:parameter>'
                                f'<ac:parameter ac:name="type">{panel_type}</ac:parameter>'
                                f"<ac:rich-text-body><p>{block_content}</p></ac:rich-text-body>"
                                f"</ac:structured-macro>"
                            )
                        elif block_type == "code":
                            props = block.get("properties", {})
                            language = props.get("language", "")
                            storage_content.append(
                                f'<ac:structured-macro ac:name="code">'
                                f'<ac:parameter ac:name="language">{language}</ac:parameter>'
                                f"<ac:plain-text-body><![CDATA[{block_content}]]></ac:plain-text-body>"
                                f"</ac:structured-macro>"
                            )
                        logger.info(f"Successfully processed block type: {block_type}")
                    except Exception as e:
                        logger.error(f"Error processing block type {block_type}: {e}")
                        continue

                # Join all content blocks
                final_content = "\n".join(storage_content)
                logger.info(f"Final content length: {len(final_content)}")

                # Create the page directly using the Confluence API
                try:
                    result = confluence_fetcher.confluence.create_page(
                        space=space_key,
                        title=arguments["title"],
                        body=final_content,
                        representation="storage",
                    )
                    logger.info(f"Page creation result: {result}")

                    if not result:
                        logger.error(
                            "Failed to create page - no result returned from API"
                        )
                        return [
                            TextContent(
                                type="text",
                                text=json.dumps(
                                    {
                                        "success": False,
                                        "error": "Failed to create page - no result returned from API",
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
                                    "page_id": result["id"],
                                    "title": result["title"],
                                    "space_key": space_key,
                                    "url": f"{confluence_fetcher.config.url}/wiki/spaces/{space_key}/pages/{result['id']}",
                                    "version": result.get("version", {}).get(
                                        "number", 1
                                    ),
                                },
                                indent=2,
                            ),
                        )
                    ]

                except Exception as e:
                    logger.error(f"Error creating page via API: {str(e)}")
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

            except Exception as e:
                logger.error(f"Error in confluence_create_page: {str(e)}")
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
