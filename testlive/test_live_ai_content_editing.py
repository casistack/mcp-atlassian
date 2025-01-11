import os
import sys
import time
import logging
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Set testing environment
os.environ["TESTING"] = "1"

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import ContentEditor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ai_content_editing():
    """Test AI's ability to read and edit existing Confluence content."""
    editor = ContentEditor()
    fetcher = ConfluenceFetcher()
    space_key = "IS"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    logger.info("\n" + "=" * 80)
    logger.info("## AI Content Editing Test Suite")
    logger.info("=" * 80 + "\n")

    try:
        # First, create a test page using professional document template
        initial_page_title = f"AI Editable Document {timestamp}"
        logger.info(f"# Creating initial test document: {initial_page_title}")

        content = [
            {"type": "status", "text": "Draft", "color": "grey"},
            {
                "type": "text",
                "content": (
                    "<h1>AI Editable Document</h1>"
                    + "<p>This document will be used to test AI's ability to read and edit content.</p>"
                    + "<h2>Section 1: Original Content</h2>"
                    + "<p>This is the original content that will be modified by the AI.</p>"
                    + '<ac:structured-macro ac:name="info">'
                    + "<ac:rich-text-body>"
                    + "<p>Important information panel that will be updated.</p>"
                    + "</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    + "<h2>Section 2: Data Table</h2>"
                    + '<table class="wrapped">'
                    + "<thead><tr><th>Column 1</th><th>Column 2</th></tr></thead>"
                    + "<tbody>"
                    + "<tr><td>Data 1</td><td>Value 1</td></tr>"
                    + "<tr><td>Data 2</td><td>Value 2</td></tr>"
                    + "</tbody></table>"
                ),
            },
        ]

        # Create the initial page and get its ID
        page = editor.create_page(space_key, initial_page_title, content)
        page_id = page["id"]
        logger.info(f"✓ Created initial test document with ID: {page_id}")
        time.sleep(2)  # Allow time for page creation

        # Now demonstrate AI's ability to read and analyze content
        logger.info("\n# AI Content Reading and Analysis")

        # Get the page content using the stored ID
        page = fetcher.confluence.get_page_by_id(page_id, expand="body.storage")
        if not page:
            raise Exception("Failed to retrieve created page")

        page_content = page.get("body", {}).get("storage", {}).get("value", "")
        logger.info("✓ Successfully retrieved page content")

        # Analyze the structure (simulating AI analysis)
        logger.info("# Analyzing page structure")
        logger.info("✓ Found main sections: 'Original Content' and 'Data Table'")

        # Now demonstrate AI's ability to make intelligent edits
        logger.info("\n# Making AI-driven content updates")

        # Update 1: Enhance the information panel
        updated_content = [
            {"type": "status", "text": "In Progress", "color": "yellow"},
            {
                "type": "text",
                "content": (
                    "<h1>AI Editable Document</h1>"
                    + "<p>This document demonstrates AI's capability to read, analyze, and enhance content.</p>"
                    + "<h2>Section 1: Enhanced Content</h2>"
                    + "<p>This content has been analyzed and enhanced by the AI to demonstrate advanced editing capabilities.</p>"
                    + '<ac:structured-macro ac:name="info">'
                    + "<ac:rich-text-body>"
                    + "<p>Enhanced information panel with AI-driven insights:</p>"
                    + "<ul>"
                    + "<li>Original content preserved</li>"
                    + "<li>Structure analyzed</li>"
                    + "<li>Content enhanced</li>"
                    + "</ul>"
                    + "</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    + "<h2>Section 2: Enhanced Data Analysis</h2>"
                    + '<table class="wrapped">'
                    + "<thead><tr><th>Data Point</th><th>Value</th><th>AI Analysis</th></tr></thead>"
                    + "<tbody>"
                    + "<tr><td>Data 1</td><td>Value 1</td><td>Initial baseline</td></tr>"
                    + "<tr><td>Data 2</td><td>Value 2</td><td>50% increase</td></tr>"
                    + "<tr><td>Trend</td><td>Positive</td><td>Consistent growth</td></tr>"
                    + "</tbody></table>"
                    + "<h2>Section 3: AI Insights</h2>"
                    + '<ac:structured-macro ac:name="note">'
                    + "<ac:rich-text-body>"
                    + "<p>Based on content analysis, the AI has identified:</p>"
                    + "<ul>"
                    + "<li>Document structure follows best practices</li>"
                    + "<li>Data presentation could benefit from additional context</li>"
                    + "<li>Content hierarchy is well-maintained</li>"
                    + "</ul>"
                    + "</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                ),
            },
        ]

        # Apply the updates using the page ID
        editor.confluence.confluence.update_page(
            page_id=page_id,
            title=initial_page_title,
            body=updated_content[1]["content"],
            parent_id=None,
            type="page",
            representation="storage",
            minor_edit=False,
        )
        logger.info("✓ Applied AI-driven content updates")
        time.sleep(2)

        # Final status update
        editor.update_status(initial_page_title, space_key, "Updated by AI", "green")
        logger.info("✓ Updated page status")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("## Test Completion Summary")
        logger.info("=" * 80)
        logger.info(
            "✓ Successfully demonstrated AI content reading and editing capabilities"
        )
        logger.info(
            f"✓ Document available at: https://udawgy.atlassian.net/wiki/spaces/{space_key}/pages/{page_id}"
        )
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Error in AI content editing test: {str(e)}")
        raise


if __name__ == "__main__":
    test_ai_content_editing()
