import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# Set testing environment
os.environ["TESTING"] = "1"

import logging
from datetime import datetime
from dotenv import load_dotenv
from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import MarkupFormatter, ContentEditor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-test-advanced-edit")

# Load environment variables
load_dotenv()


def test_advanced_editing():
    logger.info("\n=== Testing Advanced Editing Capabilities ===")
    try:
        confluence = ConfluenceFetcher()

        # Get the first available space
        spaces = confluence.get_spaces()
        if not spaces.get("results"):
            logger.error("No spaces available")
            return

        space_key = spaces["results"][0]["key"]
        target_title = "Advanced Formatting Test 20250111191528"

        # Get the existing page
        logger.info(f"Getting existing page: {target_title}")
        page = confluence.get_page_by_title(space_key, target_title)

        if not page:
            logger.error(f"Could not find page: {target_title}")
            return

        page_id = page.metadata["page_id"]
        logger.info(f"Found page: {page.metadata['url']}")

        # Debug: Get the current content
        current_page = confluence.confluence.get_page_by_id(
            page_id=page_id, expand="body.storage,version"
        )
        logger.info("Current page content:")
        logger.info(current_page["body"]["storage"]["value"])

        # Test 1: Add new list item
        logger.info("\nTest 1: Adding new list item")
        current_content = current_page["body"]["storage"]["value"]
        new_content = current_content.replace(
            "<h2>Lists</h2>",
            "<h2>Lists</h2>\n\n<ul><li>New Test Item - Added by API</li></ul>",
        )

        # Update the page
        confluence.confluence.update_page(
            page_id=page_id,
            title=target_title,
            body=new_content,
            type="page",
            representation="storage",
            minor_edit=True,
        )
        logger.info("Successfully added new list item")

        # Test 2: Add new table row
        logger.info("\nTest 2: Adding new table row")
        current_page = confluence.confluence.get_page_by_id(
            page_id=page_id, expand="body.storage"
        )
        current_content = current_page["body"]["storage"]["value"]
        new_content = current_content.replace(
            "</tbody></table>",
            "<tr><td><p>New Value</p></td><td><p>Added by API</p></td></tr></tbody></table>",
        )

        confluence.confluence.update_page(
            page_id=page_id,
            title=target_title,
            body=new_content,
            type="page",
            representation="storage",
            minor_edit=True,
        )
        logger.info("Successfully added new table row")

        # Test 3: Add new section with code
        logger.info("\nTest 3: Adding new section with code")
        current_page = confluence.confluence.get_page_by_id(
            page_id=page_id, expand="body.storage"
        )
        current_content = current_page["body"]["storage"]["value"]

        new_section = """
<h2>New Section</h2>

<p>This section was added via the API</p>

<ac:structured-macro ac:name="code" ac:schema-version="1">
<ac:parameter ac:name="language">python</ac:parameter>
<ac:plain-text-body><![CDATA[
def hello_world():
    print("Hello from API!")
]]></ac:plain-text-body>
</ac:structured-macro>
"""

        new_content = current_content + new_section

        confluence.confluence.update_page(
            page_id=page_id,
            title=target_title,
            body=new_content,
            type="page",
            representation="storage",
            minor_edit=True,
        )
        logger.info("Successfully added new section")

        # Debug: Get the final content
        final_page = confluence.confluence.get_page_by_id(
            page_id=page_id, expand="body.storage"
        )
        logger.info("\nFinal page content:")
        logger.info(final_page["body"]["storage"]["value"])

        logger.info("\nAll editing tests completed!")
        logger.info(f"You can view the final page at: {page.metadata['url']}")

    except Exception as e:
        logger.error(f"Error in advanced editing test: {str(e)}", exc_info=True)


if __name__ == "__main__":
    test_advanced_editing()
