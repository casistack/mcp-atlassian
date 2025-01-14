import json
import logging
from typing import Sequence
from mcp.types import TextContent

from mcp_atlassian.content import TemplateHandler
from ..content_advanced import AdvancedFormatting

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
                advanced_formatting = AdvancedFormatting()

                for block in content:
                    if not isinstance(block, dict) or "type" not in block:
                        logger.warning(f"Skipping invalid block: {block}")
                        continue

                    block_type = block.get("type", "")
                    block_content = block.get("content", "")
                    logger.info(f"Processing block type: {block_type}")

                    try:
                        # Handle basic blocks
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
                        # Handle advanced blocks
                        elif block_type == "layout":
                            columns = block.get("content", [])
                            layout_type = block.get("properties", {}).get("type")
                            if layout_type == "two_equal" and len(columns) == 2:
                                storage_content.append(
                                    advanced_formatting.two_column_layout(
                                        columns[0].get("content", ""),
                                        columns[1].get("content", ""),
                                    )
                                )
                            elif layout_type == "three_equal" and len(columns) == 3:
                                storage_content.append(
                                    advanced_formatting.three_column_layout(
                                        [col.get("content", "") for col in columns]
                                    )
                                )
                        elif block_type == "tabs":
                            tabs = block.get("content", [])
                            storage_content.append(
                                advanced_formatting.tabbed_content(tabs)
                            )
                        elif block_type == "chart":
                            storage_content.append(
                                advanced_formatting.chart(
                                    block.get("chart_type", "pie"),
                                    block.get("data", {}),
                                    block.get("title", ""),
                                    block.get("width", 600),
                                    block.get("height", 400),
                                )
                            )
                        elif block_type == "roadmap":
                            storage_content.append(
                                advanced_formatting.roadmap(block.get("items", []))
                            )
                        elif block_type == "info_card":
                            storage_content.append(
                                advanced_formatting.info_card(
                                    block.get("title", ""),
                                    block.get("content", ""),
                                    block.get("icon", "info"),
                                    block.get("color", "#0052CC"),
                                )
                            )
                        elif block_type == "table":
                            headers = block.get("headers", [])
                            rows = block.get("rows", [])
                            styles = block.get("styles")
                            if styles:
                                storage_content.append(
                                    advanced_formatting.table_with_styling(
                                        headers, rows, styles
                                    )
                                )
                            else:
                                table_html = ["<table><tbody>"]
                                header_html = "".join(
                                    f"<th>{header}</th>" for header in headers
                                )
                                table_html.append(f"<tr>{header_html}</tr>")
                                for row in rows:
                                    cells = "".join(f"<td>{cell}</td>" for cell in row)
                                    table_html.append(f"<tr>{cells}</tr>")
                                table_html.append("</tbody></table>")
                                storage_content.append("\n".join(table_html))
                        elif block_type == "panel":
                            props = block.get("properties", {})
                            panel_type = props.get("type", "info")
                            title = props.get("title", "")
                            storage_content.append(
                                f'<ac:structured-macro ac:name="panel">'
                                f'<ac:parameter ac:name="type">{panel_type}</ac:parameter>'
                                f'<ac:parameter ac:name="title">{title}</ac:parameter>'
                                f"<ac:rich-text-body><p>{block_content}</p></ac:rich-text-body>"
                                f"</ac:structured-macro>"
                            )
                        elif block_type == "status":
                            color = block.get("properties", {}).get("color", "grey")
                            storage_content.append(
                                f'<ac:structured-macro ac:name="status">'
                                f'<ac:parameter ac:name="colour">{color}</ac:parameter>'
                                f'<ac:parameter ac:name="title">{block_content}</ac:parameter>'
                                "</ac:structured-macro>"
                            )
                        elif block_type == "code":
                            language = block.get("properties", {}).get("language", "")
                            storage_content.append(
                                f'<ac:structured-macro ac:name="code">'
                                f'<ac:parameter ac:name="language">{language}</ac:parameter>'
                                "<ac:plain-text-body><![CDATA["
                                f"{block_content}"
                                "]]></ac:plain-text-body>"
                                "</ac:structured-macro>"
                            )
                        elif block_type == "toc":
                            props = block.get("properties", {})
                            min_level = props.get("min_level", 1)
                            max_level = props.get("max_level", 7)
                            storage_content.append(
                                f'<ac:structured-macro ac:name="toc">'
                                f'<ac:parameter ac:name="minLevel">{min_level}</ac:parameter>'
                                f'<ac:parameter ac:name="maxLevel">{max_level}</ac:parameter>'
                                "</ac:structured-macro>"
                            )
                        logger.info(f"Successfully processed block type: {block_type}")
                    except Exception as e:
                        logger.error(f"Error processing block type {block_type}: {e}")
                        continue

                # Join all content blocks
                final_content = "\n".join(storage_content)
                logger.info(f"Final content length: {len(final_content)}")

                # Create the page
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

                # Create a new editor instance
                editor = content_editor.create_editor()

                # Process each content block
                for block in content:
                    if not isinstance(block, dict) or "type" not in block:
                        raise ValueError(
                            "Each content block must be a dictionary with a 'type' field"
                        )

                    print(f"Processing block: {json.dumps(block, indent=2)}")
                    block_type = block.get("type", "")

                    try:
                        if block_type == "heading":
                            editor.heading(
                                block["content"],
                                block.get("properties", {}).get("level", 1),
                            )
                        elif block_type == "text":
                            if "style" in block:
                                if "bold" in block["style"]:
                                    editor.bold(block["content"])
                                elif "italic" in block["style"]:
                                    editor.italic(block["content"])
                            else:
                                editor.text(block["content"])
                        elif block_type == "list":
                            items = block.get("items", [])
                            if not isinstance(items, list):
                                raise ValueError(
                                    f"List items must be an array, got {type(items)}"
                                )
                            if block.get("style") == "numbered":
                                editor.numbered_list(items)
                            else:
                                editor.bullet_list(items)
                        elif block_type == "table":
                            headers = block.get("headers")
                            rows = block.get("rows")
                            if not headers or not rows:
                                raise ValueError(
                                    "Table must have both headers and rows"
                                )
                            if not isinstance(headers, list) or not isinstance(
                                rows, list
                            ):
                                raise ValueError(
                                    "Table headers and rows must be arrays"
                                )
                            editor.table(headers, rows)
                        elif block_type == "panel":
                            props = block.get("properties", {})
                            editor.panel(
                                block["content"],
                                props.get("type", "info"),
                                props.get("title", ""),
                            )
                        elif block_type == "status":
                            props = block.get("properties", {})
                            editor.status(block["content"], props.get("color", "grey"))
                        elif block_type == "code":
                            props = block.get("properties", {})
                            editor.code(block["content"], props.get("language", ""))
                        elif block_type == "toc":
                            props = block.get("properties", {})
                            editor.table_of_contents(
                                props.get("min_level", 1), props.get("max_level", 7)
                            )
                        else:
                            print(f"Warning: Unknown block type {block_type}, skipping")
                            continue

                        print(f"Successfully processed {block_type} block")
                    except Exception as block_error:
                        print(
                            f"Error processing {block_type} block: {str(block_error)}"
                        )
                        raise ValueError(
                            f"Failed to process {block_type} block: {str(block_error)}"
                        )

                # Convert the content to HTML format
                formatted_content = content_editor.create_rich_content(
                    editor.get_content()
                )
                print(f"\nFormatted content: {formatted_content}")

                if not formatted_content:
                    raise ValueError("Failed to format content - no content generated")

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
                error_msg = str(e)
                print(f"Error during update: {error_msg}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "success": False,
                                "error": f"Failed to update page: {error_msg}",
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
