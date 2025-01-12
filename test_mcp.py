import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import ContentEditor, RichTextEditor


async def test_content_handling():
    """Test comprehensive professional document formatting."""
    content_editor = ContentEditor()
    editor = content_editor.create_editor()

    # Test blocks demonstrating a professional document structure
    test_blocks = [
        # Document Status
        {"type": "status", "properties": {"color": "blue"}, "content": "Draft"},
        # Table of Contents
        {"type": "toc", "properties": {"min_level": 1, "max_level": 3}},
        # Main Title
        {
            "type": "heading",
            "properties": {"level": 1},
            "content": "Project Documentation Guide",
        },
        # Introduction Section
        {"type": "heading", "properties": {"level": 2}, "content": "1. Introduction"},
        {
            "type": "text",
            "content": "This document outlines best practices for project documentation.",
            "style": {"bold": True},
        },
        {
            "type": "panel",
            "properties": {"type": "note", "title": "Document Purpose"},
            "content": "Use this guide as a reference for creating consistent project documentation across the organization.",
        },
        # Key Features Section
        {"type": "heading", "properties": {"level": 2}, "content": "2. Key Features"},
        {
            "type": "list",
            "style": "bullet",
            "items": [
                "Comprehensive formatting options",
                "Professional document structure",
                "Clear visual hierarchy",
                "Interactive elements",
            ],
        },
        # Technical Details Section
        {
            "type": "heading",
            "properties": {"level": 2},
            "content": "3. Technical Implementation",
        },
        {"type": "heading", "properties": {"level": 3}, "content": "3.1 Code Example"},
        {
            "type": "code",
            "properties": {"language": "python"},
            "content": """def format_document(title: str, content: List[Dict]) -> Document:
    \"\"\"Create a professionally formatted document.\"\"\"
    doc = Document(title)
    doc.add_table_of_contents()
    
    for section in content:
        doc.add_section(section)
    
    return doc""",
        },
        # Best Practices Section
        {"type": "heading", "properties": {"level": 2}, "content": "4. Best Practices"},
        {
            "type": "list",
            "style": "numbered",
            "items": [
                "Use consistent heading levels",
                "Include a table of contents for longer documents",
                "Add status indicators for document state",
                "Utilize panels for important information",
            ],
        },
        # Reference Table
        {
            "type": "heading",
            "properties": {"level": 3},
            "content": "4.1 Quick Reference",
        },
        {
            "type": "table",
            "headers": ["Element", "Usage", "Example"],
            "rows": [
                ["Headings", "Document structure", "H1, H2, H3"],
                ["Lists", "Organized information", "Bullet & Numbered"],
                ["Panels", "Important notes", "Info, Warning, Note"],
                ["Code blocks", "Technical content", "With syntax highlighting"],
            ],
        },
        # Summary Panel
        {
            "type": "panel",
            "properties": {"type": "info", "title": "Summary"},
            "content": """Key Takeaways:
• Professional documentation improves project clarity
• Consistent formatting enhances readability
• Rich formatting options available for all content types
• Regular updates maintain document relevance""",
        },
    ]

    try:
        # Process each block
        for block in test_blocks:
            if block["type"] == "status":
                editor.status(block["content"], block["properties"]["color"])
            elif block["type"] == "heading":
                editor.heading(block["content"], block["properties"]["level"])
            elif block["type"] == "text":
                if block.get("style", {}).get("bold"):
                    editor.bold(block["content"])
                else:
                    editor.text(block["content"])
            elif block["type"] == "list":
                if block.get("style") == "numbered":
                    editor.numbered_list(block["items"])
                else:
                    editor.bullet_list(block["items"])
            elif block["type"] == "code":
                editor.code(block["content"], block["properties"]["language"])
            elif block["type"] == "panel":
                editor.panel(
                    block["content"],
                    block["properties"]["type"],
                    block["properties"].get("title", ""),
                )
            elif block["type"] == "table":
                editor.table(block["headers"], block["rows"])
            elif block["type"] == "toc":
                editor.table_of_contents(
                    block["properties"].get("min_level", 1),
                    block["properties"].get("max_level", 7),
                )

        # Get the formatted content
        content = editor.get_content()
        print("\nTest Results:")
        print("=============")
        print("Generated Content Structure:")
        print(json.dumps(content, indent=2))

        # Test content conversion
        formatted_content = content_editor.create_rich_content(content)
        print("\nFormatted Confluence Content:")
        print("============================")
        print(formatted_content)

        return True, "Professional document formatting test completed successfully"
    except Exception as e:
        return False, f"Document formatting test failed: {str(e)}"


async def test_advanced_formatting():
    """Test advanced Confluence formatting capabilities."""
    content_editor = ContentEditor()
    editor = content_editor.create_editor()

    # Test blocks demonstrating advanced formatting
    test_blocks = [
        # Document Header with Status and Layout
        {
            "type": "layout",
            "properties": {"type": "two_column"},
            "content": [
                {
                    "type": "column",
                    "content": [
                        {
                            "type": "status",
                            "properties": {"color": "blue"},
                            "content": "In Review",
                        },
                        {
                            "type": "heading",
                            "properties": {"level": 1},
                            "content": "Advanced Formatting Demo",
                        },
                    ],
                },
                {
                    "type": "column",
                    "content": [
                        {
                            "type": "panel",
                            "properties": {"type": "note", "title": "Last Updated"},
                            "content": "@current-date",
                        }
                    ],
                },
            ],
        },
        # Text Formatting Section
        {
            "type": "heading",
            "properties": {"level": 2},
            "content": "1. Text Formatting",
        },
        {
            "type": "text",
            "content": "This text demonstrates various formatting options:",
            "style": {"bold": True},
        },
        {
            "type": "text",
            "content": "Color and Alignment Example",
            "properties": {"color": "#FF0000", "alignment": "center", "indent": 2},
        },
        {
            "type": "text",
            "content": "Text with background highlight",
            "properties": {"background": "#FFFF00"},
        },
        # Action Items and Tasks
        {
            "type": "heading",
            "properties": {"level": 2},
            "content": "2. Action Items & Tasks",
        },
        {
            "type": "task_list",
            "items": [
                {"text": "Review documentation", "status": "complete"},
                {
                    "text": "Update formatting",
                    "status": "incomplete",
                    "assignee": "@john.doe",
                },
                {"text": "Add examples", "status": "incomplete", "due": "2024-03-01"},
            ],
        },
        # Rich Media Section
        {"type": "heading", "properties": {"level": 2}, "content": "3. Rich Media"},
        {
            "type": "image",
            "properties": {
                "source": "attachment://example.png",
                "alt": "Example Image",
                "caption": "Figure 1: Example Diagram",
                "alignment": "center",
            },
        },
        {
            "type": "video",
            "properties": {
                "source": "https://example.com/video.mp4",
                "thumbnail": "attachment://thumbnail.jpg",
            },
        },
        {
            "type": "file",
            "properties": {
                "path": "attachment://document.pdf",
                "name": "Project Specs",
                "size": "2.5MB",
            },
        },
        # Advanced Links and Mentions
        {
            "type": "heading",
            "properties": {"level": 2},
            "content": "4. Links & Mentions",
        },
        {
            "type": "text",
            "content": [
                {
                    "type": "mention",
                    "properties": {"user": "@jane.smith"},
                    "content": "Jane Smith",
                },
                {"type": "text", "content": " please review the "},
                {
                    "type": "link",
                    "properties": {"href": "confluence://space/page", "type": "page"},
                    "content": "requirements document",
                },
            ],
        },
        {
            "type": "text",
            "content": "Check JIRA ticket ",
            "append": {
                "type": "link",
                "properties": {"href": "jira://PROJECT-123", "type": "jira"},
                "content": "PROJECT-123",
            },
        },
        # Emojis and Special Characters
        {
            "type": "text",
            "content": "Sprint Status: ",
            "append": {
                "type": "emoji",
                "properties": {"name": "rocket"},
                "content": "🚀",
            },
        },
        # Complex Tables
        {
            "type": "heading",
            "properties": {"level": 2},
            "content": "5. Advanced Tables",
        },
        {
            "type": "table",
            "properties": {"has_header": True, "column_widths": ["30%", "40%", "30%"]},
            "headers": ["Feature", "Description", "Status"],
            "rows": [
                [
                    {"content": "Layouts", "style": {"bold": True}},
                    {
                        "content": "Multi-column support",
                        "properties": {"background": "#f0f0f0"},
                    },
                    {"content": "✅", "properties": {"alignment": "center"}},
                ],
                [
                    {"content": "Rich Text", "style": {"bold": True}},
                    {
                        "content": "Colors and formatting",
                        "properties": {"color": "#0000FF"},
                    },
                    {"content": "✅", "properties": {"alignment": "center"}},
                ],
            ],
        },
        # Info Panel Variations
        {
            "type": "heading",
            "properties": {"level": 2},
            "content": "6. Panel Variations",
        },
        {
            "type": "panel",
            "properties": {
                "type": "warning",
                "title": "Important Notice",
                "icon": "warning",
            },
            "content": "Critical information that requires attention",
        },
        {
            "type": "panel",
            "properties": {
                "type": "success",
                "title": "Completed Tasks",
                "collapsible": True,
            },
            "content": "All requirements have been met",
        },
        {
            "type": "expand",
            "properties": {"title": "Click to see more details"},
            "content": "This section contains additional information that can be expanded",
        },
        # Divider with Style
        {
            "type": "divider",
            "properties": {"style": "double", "width": "50%", "alignment": "center"},
        },
    ]

    try:
        # Process each block
        for block in test_blocks:
            if block["type"] == "layout":
                for column in block["content"]:
                    for content in column["content"]:
                        process_content_block(editor, content)
            elif block["type"] == "task_list":
                editor.task_list(block["items"])
            elif block["type"] == "image":
                editor.image(
                    block["properties"]["source"],
                    block["properties"].get("alt", ""),
                    block["properties"].get("caption", ""),
                    block["properties"].get("alignment", "left"),
                )
            elif block["type"] == "video":
                editor.video(
                    block["properties"]["source"],
                    block["properties"].get("thumbnail", ""),
                )
            elif block["type"] == "file":
                editor.file(
                    block["properties"]["path"],
                    block["properties"].get("name", ""),
                    block["properties"].get("size", ""),
                )
            elif block["type"] == "text" and isinstance(block["content"], list):
                for item in block["content"]:
                    if item["type"] == "mention":
                        editor.mention(item["properties"]["user"])
                    elif item["type"] == "link":
                        editor.link(item["content"], item["properties"]["href"])
                    else:
                        editor.text(item["content"])
            elif block["type"] == "emoji":
                editor.emoji(block["properties"]["name"])
            elif block["type"] == "table":
                process_advanced_table(editor, block)
            elif block["type"] == "expand":
                editor.expand(block["content"], block["properties"]["title"])
            elif block["type"] == "divider":
                editor.divider(
                    block["properties"].get("style", "single"),
                    block["properties"].get("width", "100%"),
                    block["properties"].get("alignment", "left"),
                )
            else:
                process_content_block(editor, block)

        # Get the formatted content
        content = editor.get_content()
        print("\nAdvanced Formatting Test Results:")
        print("================================")
        print("Generated Content Structure:")
        print(json.dumps(content, indent=2))

        # Test content conversion
        formatted_content = content_editor.create_rich_content(content)
        print("\nFormatted Confluence Content:")
        print("============================")
        print(formatted_content)

        return True, "Advanced formatting test completed successfully"
    except Exception as e:
        return False, f"Advanced formatting test failed: {str(e)}"


def process_content_block(editor, block):
    """Helper function to process individual content blocks."""
    if block["type"] == "status":
        editor.status(block["content"], block["properties"]["color"])
    elif block["type"] == "heading":
        editor.heading(block["content"], block["properties"]["level"])
    elif block["type"] == "text":
        if "properties" in block:
            editor.text_with_properties(
                block["content"],
                color=block["properties"].get("color"),
                background=block["properties"].get("background"),
                alignment=block["properties"].get("alignment"),
                indent=block["properties"].get("indent"),
            )
        elif block.get("style", {}).get("bold"):
            editor.bold(block["content"])
        else:
            editor.text(block["content"])
        if "append" in block:
            process_content_block(editor, block["append"])
    elif block["type"] == "panel":
        editor.panel(
            block["content"],
            block["properties"]["type"],
            block["properties"].get("title", ""),
            block["properties"].get("collapsible", False),
        )


def process_advanced_table(editor, block):
    """Helper function to process advanced table formatting."""
    headers = []
    for header in block["headers"]:
        if isinstance(header, dict):
            headers.append(header["content"])
        else:
            headers.append(header)

    rows = []
    for row in block["rows"]:
        processed_row = []
        for cell in row:
            if isinstance(cell, dict):
                cell_content = cell["content"]
                if "properties" in cell:
                    # Apply cell properties (background, alignment, etc.)
                    cell_content = editor.format_cell(
                        cell_content,
                        background=cell["properties"].get("background"),
                        alignment=cell["properties"].get("alignment"),
                    )
                processed_row.append(cell_content)
            else:
                processed_row.append(cell)
        rows.append(processed_row)

    editor.table(headers, rows, properties=block.get("properties", {}))


async def main():
    print("Starting MCP Atlassian Advanced Formatting Tests...")

    # Run advanced formatting test
    success, message = await test_advanced_formatting()
    print(f"\nAdvanced Formatting Test: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"Message: {message}")


if __name__ == "__main__":
    asyncio.run(main())
