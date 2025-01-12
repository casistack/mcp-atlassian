import asyncio
import logging
import os
import sys
from pathlib import Path
import json
from typing import Any

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import ContentEditor, RichTextEditor
from mcp_atlassian.config import Config
from mcp_atlassian.server import Tool, list_tools, call_tool, TextContent

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
        "JIRA_URL",
        "JIRA_USERNAME",
        "JIRA_API_TOKEN",
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
    print(f"Confluence URL: {config.confluence.url}")
    print(f"Confluence Username: {config.confluence.username}")
    print(
        f"Confluence API Token: {'Set' if config.confluence.api_token else 'Not Set'}"
    )
    print(f"Jira URL: {config.jira.url}")
    print(f"Jira Username: {config.jira.username}")
    print(f"Jira API Token: {'Set' if config.jira.api_token else 'Not Set'}")

    if (
        not config.confluence.url
        or not config.confluence.username
        or not config.confluence.api_token
        or not config.jira.url
        or not config.jira.username
        or not config.jira.api_token
    ):
        print("ERROR: Invalid configuration")
        return False

    print("Configuration validation successful")
    return True


def format_tool_result(result: list[TextContent]) -> Any:
    """Format tool result for display."""
    if not result:
        return None

    # Get the first text content
    text_content = result[0]

    # If it's JSON, parse it
    try:
        return json.loads(text_content.text)
    except json.JSONDecodeError:
        return text_content.text


async def test_unified_search():
    """Test unified search functionality across Confluence and Jira."""
    try:
        if not validate_config():
            print("ERROR: Configuration validation failed")
            return

        print("\n=== Testing Unified Search ===")

        # First, verify the tool is available
        tools = await list_tools()
        if not any(tool.name == "unified_search" for tool in tools):
            print("ERROR: unified_search tool not found in available tools")
            return

        # Test Case 1: Search with query only
        print("\n1. Testing search with query only...")
        query = "project documentation"
        try:
            result = await call_tool("unified_search", {"query": query})
            print(f"Search results for '{query}':")
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results found"
            )
        except Exception as e:
            print(f"Error in basic search: {str(e)}")

        # Test Case 2: Search with specific platforms
        print("\n2. Testing search with specific platforms...")
        try:
            result = await call_tool(
                "unified_search",
                {"query": query, "platforms": ["confluence"]},
            )
            print("Search results for Confluence only:")
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results found"
            )
        except Exception as e:
            print(f"Error in platform-specific search: {str(e)}")

        # Test Case 3: Search with custom limit
        print("\n3. Testing search with custom limit...")
        try:
            result = await call_tool(
                "unified_search",
                {"query": query, "limit": 5},
            )
            print("Search results with limit 5:")
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results found"
            )
        except Exception as e:
            print(f"Error in limited search: {str(e)}")

        # Test Case 4: Search with special characters
        print("\n4. Testing search with special characters...")
        special_query = "project & documentation + testing"
        try:
            result = await call_tool(
                "unified_search",
                {"query": special_query},
            )
            print(f"Search results for '{special_query}':")
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results found"
            )
        except Exception as e:
            print(f"Error in special character search: {str(e)}")

        # Test Case 5: Search with empty query
        print("\n5. Testing search with empty query...")
        try:
            result = await call_tool(
                "unified_search",
                {"query": ""},
            )
            print("Search results for empty query:")
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results found"
            )
        except Exception as e:
            print(f"Error in empty query search: {str(e)}")

    except Exception as e:
        print(f"ERROR: Error during test execution: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


async def test_confluence_search():
    """Test Confluence search functionality using direct code calls."""
    try:
        if not validate_config():
            print("ERROR: Configuration validation failed")
            return

        print("\n=== Testing Confluence Search ===")

        # Initialize the actual ConfluenceFetcher
        confluence = ConfluenceFetcher()

        # Test Case 1: Search by title
        print("\n1. Testing search by title...")
        title = "Project Best Practices"
        try:
            # Using the actual search method from ConfluenceFetcher
            cql = f'type = page AND title ~ "{title}"'
            results = confluence.search(cql, limit=10)
            print(f"Search results for title '{title}':")
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
        except Exception as e:
            print(f"Error in title search: {str(e)}")

        # Test Case 2: Search with CQL query
        print("\n2. Testing search with CQL query...")
        cql = 'type = page AND space = "IS" AND text ~ "documentation"'
        try:
            results = confluence.search(cql, limit=5)
            print(f"Search results for CQL '{cql}':")
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
        except Exception as e:
            print(f"Error in CQL search: {str(e)}")

        # Test Case 3: Search with limit
        print("\n3. Testing search with limit...")
        try:
            results = confluence.search('type = page AND text ~ "test"', limit=2)
            print("Search results with limit 2:")
            for doc in results:
                print(f"\nTitle: {doc.metadata['title']}")
                print(
                    f"Space: {doc.metadata['space_name']} ({doc.metadata['space_key']})"
                )
        except Exception as e:
            print(f"Error in limited search: {str(e)}")

        # Test Case 4: Search in specific space
        print("\n4. Testing search in specific space...")
        try:
            results = confluence.search('type = page AND space = "IS"', limit=5)
            print('Search results in space "IS":')
            for doc in results:
                print(f"\nTitle: {doc.metadata['title']}")
                print(
                    f"Space: {doc.metadata['space_name']} ({doc.metadata['space_key']})"
                )
        except Exception as e:
            print(f"Error in space search: {str(e)}")

        # Test Case 5: Search with invalid query
        print("\n5. Testing search with invalid query...")
        try:
            results = confluence.search("invalid:query:format", limit=5)
            print("Search results with invalid query:")
            if not results:
                print("No results found (expected for invalid query)")
            for doc in results:
                print(f"\nTitle: {doc.metadata['title']}")
        except Exception as e:
            print(f"Error handling for invalid query: {str(e)}")

    except Exception as e:
        print(f"ERROR: Error during test execution: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


async def main():
    print("Starting Confluence search tests...")
    await test_confluence_search()
    print("\nTests completed.")


if __name__ == "__main__":
    asyncio.run(main())
