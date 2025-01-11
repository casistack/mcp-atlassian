import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Set testing environment
os.environ["TESTING"] = "1"

from mcp_atlassian.content import ContentEditor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_advanced_formatting():
    """Test advanced formatting capabilities."""
    editor = ContentEditor()
    space_key = "IS"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    page_title = f"Advanced Formatting Test {timestamp}"

    logger.info("\n" + "=" * 80)
    logger.info("## Advanced Formatting Test Suite")
    logger.info("=" * 80 + "\n")

    try:
        # Create initial page with TOC
        logger.info("Creating test page with table of contents...")
        initial_content = [
            {"type": "status", "text": "In Progress", "color": "blue"},
            {
                "type": "text",
                "content": "This page demonstrates advanced formatting capabilities.",
            },
        ]
        editor.create_page(space_key, page_title, initial_content)
        editor.add_table_of_contents(page_title, space_key, min_level=1, max_level=3)
        logger.info("✓ Created page with TOC")

        # Test rich text formatting
        logger.info("\n# Testing Rich Text Formatting")
        section_content = [
            {
                "type": "text",
                "content": editor.format_text("This is bold text", ["bold"])
                + " and "
                + editor.format_text("this is italic", ["italic"])
                + " and "
                + editor.format_text("this is both", ["bold", "italic"]),
            }
        ]
        editor.add_section(
            page_title, space_key, "Text Formatting Examples", section_content
        )
        logger.info("✓ Added formatted text section")

        # Test links
        logger.info("\n# Testing Links")
        editor.add_section(
            page_title, space_key, "Link Examples", [{"type": "text", "content": ""}]
        )
        editor.add_link(
            page_title,
            space_key,
            "Link Examples",
            "External Link",
            "https://www.atlassian.com",
            "external",
        )
        editor.add_link(
            page_title, space_key, "Link Examples", "Page Link", page_title, "page"
        )
        logger.info("✓ Added different types of links")

        # Test expandable sections
        logger.info("\n# Testing Expandable Sections")
        editor.add_expandable_section(
            page_title,
            space_key,
            "Link Examples",
            "Click to expand",
            "This is hidden content that can be expanded.",
        )
        logger.info("✓ Added expandable section")

        # Test section movement
        logger.info("\n# Testing Section Movement")
        editor.add_section(
            page_title,
            space_key,
            "Section to Move",
            [{"type": "text", "content": "This section will be moved."}],
        )
        editor.move_section(
            page_title,
            space_key,
            "Section to Move",
            "Text Formatting Examples",
            "after",
        )
        logger.info("✓ Moved section successfully")

        # Test panels with different types
        logger.info("\n# Testing Panel Types")
        editor.add_panel(
            page_title,
            space_key,
            "Section to Move",
            "This is an info panel",
            "info",
            "Information",
        )
        editor.add_panel(
            page_title,
            space_key,
            "Section to Move",
            "This is a warning panel",
            "warning",
            "Warning",
        )
        editor.add_panel(
            page_title,
            space_key,
            "Section to Move",
            "This is a note panel",
            "note",
            "Note",
        )
        logger.info("✓ Added different panel types")

        # Update status to complete
        editor.update_status(page_title, space_key, "Complete", "green")
        logger.info("\n✓ Updated page status to Complete")

        logger.info("\n" + "=" * 80)
        logger.info("## Test Completion Summary")
        logger.info("=" * 80)
        logger.info(f"✓ Successfully tested advanced formatting capabilities")
        logger.info(
            f"✓ Document available at: https://udawgy.atlassian.net/wiki/spaces/{space_key}/pages/{page_title}"
        )
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Error in advanced formatting test: {str(e)}")
        raise


if __name__ == "__main__":
    test_advanced_formatting()
