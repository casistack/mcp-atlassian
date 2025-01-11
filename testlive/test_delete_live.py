import os

os.environ["TESTING"] = "1"  # Set testing environment

import logging
from dotenv import load_dotenv
from mcp_atlassian.confluence import ConfluenceFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-test-cleanup")

# Load environment variables
load_dotenv()


def cleanup_test_pages():
    """Find and delete test pages created during testing."""
    try:
        confluence = ConfluenceFetcher()

        # Get all spaces
        spaces = confluence.get_spaces()
        if not spaces.get("results"):
            logger.error("No spaces found")
            return

        total_deleted = 0

        # Search through each space
        for space in spaces["results"]:
            space_key = space["key"]
            logger.info(f"\nSearching in space: {space_key}")

            # Search for test pages using CQL with case-insensitive and broader patterns
            test_pages = confluence.search(
                f'space = "{space_key}" AND ('
                'title ~ "MCP Test Page" OR '
                'title ~ "Blueprint Test" OR '
                'title ~ "Advanced Content Test" OR '
                'title ~ "Advanced Formatting Test" OR '
                'title ~ "Test Page" OR '
                'title ~ "Formatting Test" OR '
                'title ~ "test_" OR '
                'title ~ "MCP*Test")'
            )

            if not test_pages:
                logger.info(f"No test pages found in space {space_key}")
                continue

            logger.info(f"Found {len(test_pages)} test page(s) in space {space_key}")

            # Delete each test page
            for page in test_pages:
                page_id = page.metadata["page_id"]
                page_title = page.metadata["title"]

                logger.info(f"Deleting page: {page_title}")
                if confluence.delete_page(page_id):
                    logger.info(f"✓ Successfully deleted: {page_title}")
                    total_deleted += 1
                else:
                    logger.error(f"Failed to delete page: {page_title}")

        logger.info(f"\nCleanup complete. Total pages deleted: {total_deleted}")

    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}", exc_info=True)


if __name__ == "__main__":
    cleanup_test_pages()
