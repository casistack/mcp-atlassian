import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import ContentEditor, RichTextEditor


async def test_content_handling():
    """Test the improved content handling functionality."""
    content_editor = ContentEditor()
    editor = content_editor.create_editor()

    # Test various content block types
    test_blocks = [
        {"type": "status", "content": "In Progress", "properties": {"color": "blue"}},
        {"type": "heading", "content": "Test Heading", "properties": {"level": 1}},
        {
            "type": "text",
            "content": "This is a test paragraph",
            "style": {"bold": True},
        },
        {"type": "list", "items": ["Item 1", "Item 2", "Item 3"], "style": "bullet"},
        {
            "type": "code",
            "content": "print('Hello World')",
            "properties": {"language": "python"},
        },
        {
            "type": "panel",
            "content": "Important information",
            "properties": {"type": "info", "title": "Note"},
        },
    ]

    # Process each block
    try:
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

        return True, "Content handling test completed successfully"
    except Exception as e:
        return False, f"Content handling test failed: {str(e)}"


async def main():
    print("Starting MCP Atlassian Tests...")

    # Run content handling test
    success, message = await test_content_handling()
    print(f"\nContent Handling Test: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"Message: {message}")


if __name__ == "__main__":
    asyncio.run(main())
