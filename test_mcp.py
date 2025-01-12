import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import ContentEditor, RichTextEditor
from mcp_atlassian.config import Config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-atlassian")


def validate_config():
    """Validate the configuration and environment variables."""
    print("\nValidating configuration...")

    required_vars = [
        "CONFLUENCE_URL",
        "CONFLUENCE_USERNAME",
        "CONFLUENCE_API_TOKEN",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(
            f"ERROR: Missing required environment variables: {', '.join(missing_vars)}"
        )
        return False

    config = Config.from_env()

    # Print actual config values for debugging
    print("\nCurrent Configuration:")
    print(f"URL: {config.confluence.url}")
    print(f"Username: {config.confluence.username}")
    print(f"API Token: {'Set' if config.confluence.api_token else 'Not Set'}")

    if (
        not config.confluence.url
        or not config.confluence.username
        or not config.confluence.api_token
    ):
        print("ERROR: Invalid Confluence configuration")
        return False

    print("Configuration validation successful")
    return True


async def test_search_page():
    """Test searching for a page by title without specifying space."""
    try:
        if not validate_config():
            print("ERROR: Configuration validation failed")
            return

        print("\nInitializing Confluence fetcher...")
        confluence = ConfluenceFetcher()

        print("\nTesting direct page search...")
        title = "Project Best Practices"
        print(f"Searching for page titled: {title}")

        try:
            # First try direct CQL query
            print("\nTrying direct CQL query...")
            cql = f'type = page AND title ~ "{title}"'
            print(f"CQL Query: {cql}")

            raw_results = confluence.confluence.cql(
                cql, limit=1, expand="body.storage,version,space"
            )
            print(f"\nRaw CQL Results: {raw_results}")

            if raw_results and "results" in raw_results and raw_results["results"]:
                print("\nFound results in raw CQL query")

                # Now try our search_pages method
                print("\nTrying search_pages method...")
                results = confluence.search_pages(title, limit=1)

                if results:
                    print("\nSearch Results:")
                    for doc in results:
                        print(f"\nTitle: {doc.metadata['title']}")
                        print(
                            f"Space: {doc.metadata['space_name']} ({doc.metadata['space_key']})"
                        )
                        print(f"URL: {doc.metadata['url']}")
                        print(f"Last Modified: {doc.metadata['last_modified']}")
                        print(f"Author: {doc.metadata['author_name']}")
                        print("\nContent Preview:")
                        print(f"{doc.page_content[:200]}...")
                else:
                    print(
                        "\nNo results from search_pages method despite finding raw results"
                    )
            else:
                print("\nNo results found in raw CQL query")

                # List available spaces
                print("\nListing available spaces:")
                spaces = confluence.get_spaces()
                if spaces and "results" in spaces:
                    for space in spaces["results"]:
                        print(f"- {space.get('name')} ({space.get('key')})")

                        # Try to list some pages in this space
                        print(f"\nListing pages in space {space.get('key')}:")
                        pages = confluence.confluence.get_all_pages_from_space(
                            space=space.get("key"), start=0, limit=5, expand="title"
                        )
                        for page in pages:
                            print(f"  - {page.get('title')}")
                else:
                    print("No spaces found or error getting spaces")

        except Exception as search_error:
            print(f"\nERROR during search operation: {str(search_error)}")
            import traceback

            print("\nSearch operation error details:")
            print(traceback.format_exc())

    except Exception as e:
        print(f"ERROR: Error during test execution: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


async def main():
    print("Starting test...")
    await test_search_page()
    print("\nTest completed.")


if __name__ == "__main__":
    asyncio.run(main())
