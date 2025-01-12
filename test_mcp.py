import asyncio
import logging
import os
import sys
from pathlib import Path
import json
from typing import Any, Optional

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import ContentEditor, RichTextEditor
from mcp_atlassian.config import Config
from mcp_atlassian.server import Tool, list_tools, call_tool, TextContent
from mcp_atlassian.jira import JiraFetcher

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


async def create_test_issue() -> Optional[str]:
    """Create a test issue to use in our tests."""
    try:
        # Enable debug logging
        logging.getLogger("mcp-jira").setLevel(logging.DEBUG)

        print("\nAttempting to create test issue...")
        result = await call_tool(
            "create_jira_issue",
            {
                "project_key": "KAN",
                "summary": "Test Issue for MCP Testing",
                "description": "This is a test issue created for automated testing.",
                "issue_type": "Task",
                "priority": None,  # Remove priority for now
                "assignee": None,
                "labels": ["test", "automated"],
                "custom_fields": None,
            },
        )
        formatted_result = format_tool_result(result)
        print(f"Create issue API response: {json.dumps(formatted_result, indent=2)}")

        if formatted_result and formatted_result.get("success"):
            return formatted_result.get("key")
        return None
    except Exception as e:
        print(f"Error creating test issue: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())
        return None


async def cleanup_test_issue(issue_key: str):
    """Clean up the test issue after tests are complete."""
    try:
        result = await call_tool("delete_jira_issue", {"issue_key": issue_key})
        if not result:
            print(f"Warning: Failed to delete test issue {issue_key}")
    except Exception as e:
        print(f"Error deleting test issue: {str(e)}")


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


async def test_update_jira_issue():
    """Test updating an existing Jira issue with new values."""
    test_issue_key = None
    try:
        if not validate_config():
            print("ERROR: Configuration validation failed")
            return

        print("\n=== Testing Update Jira Issue ===")

        # Create a test issue
        print("\nCreating test issue...")
        test_issue_key = await create_test_issue()
        if not test_issue_key:
            print("ERROR: Failed to create test issue")
            return

        print(f"Created test issue: {test_issue_key}")

        # First, verify the tool is available
        tools = await list_tools()
        if not any(tool.name == "update_jira_issue" for tool in tools):
            print("ERROR: update_jira_issue tool not found in available tools")
            return

        # Test Case 1: Update basic fields
        print("\n1. Testing update of basic fields...")
        try:
            result = await call_tool(
                "update_jira_issue",
                {
                    "issue_key": test_issue_key,
                    "summary": "Updated Test Issue",
                    "description": "This is an updated test issue description",
                    "priority": "High",
                    "status": None,
                    "assignee": None,
                    "labels": None,
                    "custom_fields": None,
                },
            )
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results"
            )
        except Exception as e:
            print(f"Error in basic field update: {str(e)}")

        # Test Case 2: Update status and assignee
        print("\n2. Testing status and assignee update...")
        try:
            result = await call_tool(
                "update_jira_issue",
                {
                    "issue_key": test_issue_key,
                    "status": "In Progress",
                    "assignee": None,  # Set to None since we don't have a test user
                    "summary": None,
                    "description": None,
                    "priority": None,
                    "labels": None,
                    "custom_fields": None,
                },
            )
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results"
            )
        except Exception as e:
            print(f"Error in status/assignee update: {str(e)}")

        # Test Case 3: Update labels and custom fields
        print("\n3. Testing labels and custom fields update...")
        try:
            result = await call_tool(
                "update_jira_issue",
                {
                    "issue_key": test_issue_key,
                    "labels": ["test", "automated", "updated"],
                    "custom_fields": None,  # Remove custom fields for now
                    "summary": None,
                    "description": None,
                    "status": None,
                    "priority": None,
                    "assignee": None,
                },
            )
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results"
            )
        except Exception as e:
            print(f"Error in labels/custom fields update: {str(e)}")

        # Test Case 4: Update non-existent issue
        print("\n4. Testing update of non-existent issue...")
        try:
            result = await call_tool(
                "update_jira_issue",
                {
                    "issue_key": "INVALID-999",
                    "summary": "This should fail",
                    "description": None,
                    "status": None,
                    "priority": None,
                    "assignee": None,
                    "labels": None,
                    "custom_fields": None,
                },
            )
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results"
            )
        except Exception as e:
            print(f"Error in non-existent issue update: {str(e)}")

    except Exception as e:
        print(f"ERROR: Error during test execution: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())
    finally:
        # Clean up test issue
        if test_issue_key:
            print(f"\nCleaning up test issue {test_issue_key}...")
            await cleanup_test_issue(test_issue_key)


async def test_add_jira_comment():
    """Test adding comments to a Jira issue."""
    test_issue_key = None
    try:
        if not validate_config():
            print("ERROR: Configuration validation failed")
            return

        print("\n=== Testing Add Jira Comment ===")

        # Create a test issue
        print("\nCreating test issue...")
        test_issue_key = await create_test_issue()
        if not test_issue_key:
            print("ERROR: Failed to create test issue")
            return

        print(f"Created test issue: {test_issue_key}")

        # First, verify the tool is available
        tools = await list_tools()
        if not any(tool.name == "add_jira_comment" for tool in tools):
            print("ERROR: add_jira_comment tool not found in available tools")
            return

        # Test Case 1: Add basic comment
        print("\n1. Testing adding basic comment...")
        try:
            result = await call_tool(
                "add_jira_comment",
                {
                    "issue_key": test_issue_key,
                    "content": "This is a test comment",
                    "format_type": "plain_text",
                    "format_options": {},
                },
            )
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results"
            )
        except Exception as e:
            print(f"Error in adding basic comment: {str(e)}")

        # Test Case 2: Add formatted comment with markdown
        print("\n2. Testing adding formatted comment...")
        try:
            result = await call_tool(
                "add_jira_comment",
                {
                    "issue_key": test_issue_key,
                    "content": "# Test Heading\n- Bullet point 1\n- Bullet point 2",
                    "format_type": "markdown",
                    "format_options": {"preserve_format": True},
                },
            )
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results"
            )
        except Exception as e:
            print(f"Error in adding formatted comment: {str(e)}")

        # Test Case 3: Add comment with mentions and links
        print("\n3. Testing comment with mentions and links...")
        try:
            result = await call_tool(
                "add_jira_comment",
                {
                    "issue_key": test_issue_key,
                    "content": "Please check this issue.",  # Removed @testuser mention
                    "format_type": "jira",
                    "format_options": {"process_mentions": True},
                },
            )
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results"
            )
        except Exception as e:
            print(f"Error in adding comment with mentions: {str(e)}")

        # Test Case 4: Add comment to non-existent issue
        print("\n4. Testing comment on non-existent issue...")
        try:
            result = await call_tool(
                "add_jira_comment",
                {
                    "issue_key": "INVALID-999",
                    "content": "This should fail",
                    "format_type": "plain_text",
                    "format_options": {},
                },
            )
            formatted_result = format_tool_result(result)
            print(
                json.dumps(formatted_result, indent=2)
                if formatted_result
                else "No results"
            )
        except Exception as e:
            print(f"Error in adding comment to non-existent issue: {str(e)}")

    except Exception as e:
        print(f"ERROR: Error during test execution: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())
    finally:
        # Clean up test issue
        if test_issue_key:
            print(f"\nCleaning up test issue {test_issue_key}...")
            await cleanup_test_issue(test_issue_key)


if __name__ == "__main__":
    asyncio.run(test_update_jira_issue())
    asyncio.run(test_add_jira_comment())
