import asyncio
import logging
import os
import sys
from pathlib import Path
import json
from typing import Any, Optional
import time

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent))

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import ContentEditor, RichTextEditor
from mcp_atlassian.config import Config
from mcp_atlassian.server import Tool, list_tools, call_tool, TextContent
from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.tool_handlers.confluence_tools import handle_confluence_tools

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


async def test_get_confluence_templates():
    """Test getting Confluence templates."""
    print("\n=== Testing Get Confluence Templates ===")

    # Test Case 1: Get all templates
    print("\n1. Testing get all templates...")
    result = await call_tool("get_confluence_templates", {})
    formatted_result = format_tool_result(result)
    print(
        f"All templates: {json.dumps(formatted_result, indent=2) if formatted_result else 'No templates found'}"
    )

    # Test Case 2: Get space-specific templates
    print("\n2. Testing space-specific templates...")
    result = await call_tool("get_confluence_templates", {"space_key": "IS"})
    formatted_result = format_tool_result(result)
    print(
        f"Space templates: {json.dumps(formatted_result, indent=2) if formatted_result else 'No templates found'}"
    )

    # Test Case 3: Test with non-existent space
    print("\n3. Testing with non-existent space...")
    result = await call_tool("get_confluence_templates", {"space_key": "NONEXISTENT"})
    formatted_result = format_tool_result(result)
    print(
        f"Non-existent space templates: {json.dumps(formatted_result, indent=2) if formatted_result else 'No templates found'}"
    )


async def test_get_jira_templates():
    """Test getting Jira templates."""
    print("\n=== Testing Get Jira Templates ===")

    try:
        # Test Case 1: Get all templates
        print("\n1. Testing get all templates...")
        try:
            result = await call_tool("get_jira_templates", {})
            formatted_result = format_tool_result(result)
            print(
                f"All templates: {json.dumps(formatted_result, indent=2) if formatted_result else 'No templates found'}"
            )
        except Exception as e:
            print(f"Error getting all templates: {str(e)}")
            import traceback

            print(traceback.format_exc())

        # Test Case 2: Get project-specific templates
        print("\n2. Testing project-specific templates...")
        try:
            result = await call_tool("get_jira_templates", {"project_key": "KAN"})
            formatted_result = format_tool_result(result)
            print(
                f"Project templates: {json.dumps(formatted_result, indent=2) if formatted_result else 'No templates found'}"
            )
        except Exception as e:
            print(f"Error getting project templates: {str(e)}")
            import traceback

            print(traceback.format_exc())

        # Test Case 3: Test with non-existent project
        print("\n3. Testing with non-existent project...")
        try:
            result = await call_tool(
                "get_jira_templates", {"project_key": "NONEXISTENT"}
            )
            formatted_result = format_tool_result(result)
            print(
                f"Non-existent project templates: {json.dumps(formatted_result, indent=2) if formatted_result else 'No templates found'}"
            )
        except Exception as e:
            print(f"Error getting templates for non-existent project: {str(e)}")
            import traceback

            print(traceback.format_exc())

    except Exception as e:
        print(f"ERROR: Error during test execution: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


async def test_create_from_confluence_template():
    """Test creating a page from a Confluence template."""
    print("\n=== Testing Create From Confluence Template ===")

    # First, get available templates to use for testing
    print("\n1. Getting available templates...")
    try:
        result = await call_tool("get_confluence_templates", {"space_key": "IS"})
        templates = format_tool_result(result)
        print(f"Available templates: {json.dumps(templates, indent=2)}")

        if not templates:
            print("No templates found for testing")
            return

        # Find the Product Requirements template
        product_req_template = next(
            (t for t in templates if t["name"].lower() == "product requirements"),
            templates[0],  # Fallback to first template if not found
        )
        template_id = product_req_template["id"]

        # Generate unique timestamp for test titles
        timestamp = int(time.time())

        # Test Case 1: Complex template usage with flattened parameters
        print("\n2. Testing complex template usage with flattened parameters...")
        try:
            result = await call_tool(
                "create_from_confluence_template",
                {
                    "template_id": template_id,
                    "space_key": "IS",
                    "title": f"Test Product Requirements Document {timestamp}",
                    "template_parameters": {
                        "product_name": "Test Product",
                        "product_owner": "Test Owner",
                        "product_description": "A test product for automated testing",
                        "requirement_1": "First test requirement (High Priority)",
                        "requirement_2": "Second test requirement (Medium Priority)",
                        "stakeholder_1": "Test Team (Development)",
                        "stakeholder_2": "Test Manager (Product Owner)",
                        "overview_section": "Test product overview section",
                        "features_section": "Test product features section",
                    },
                },
            )
            formatted_result = format_tool_result(result)
            print(
                f"Create from template result: {json.dumps(formatted_result, indent=2)}"
            )

            # If page was created successfully, clean it up
            if formatted_result and formatted_result.get("success"):
                page_id = formatted_result.get("page_id")
                if page_id:
                    print(f"\nCleaning up test page {page_id}...")
                    cleanup_result = await call_tool(
                        "confluence_delete_page", {"page_id": page_id}
                    )
                    print("Cleanup complete")

        except Exception as e:
            print(f"Error in complex template usage: {str(e)}")
            import traceback

            print(traceback.format_exc())

        # Test Case 2: Template without parameters
        print("\n3. Testing template without parameters...")
        try:
            result = await call_tool(
                "create_from_confluence_template",
                {
                    "template_id": template_id,
                    "space_key": "IS",
                    "title": f"Test Template Page - No Params {timestamp}",
                },
            )
            formatted_result = format_tool_result(result)
            print(f"No parameters result: {json.dumps(formatted_result, indent=2)}")

            # Clean up if page was created
            if formatted_result and formatted_result.get("success"):
                page_id = formatted_result.get("page_id")
                if page_id:
                    print(f"\nCleaning up test page {page_id}...")
                    cleanup_result = await call_tool(
                        "confluence_delete_page", {"page_id": page_id}
                    )
                    print("Cleanup complete")

        except Exception as e:
            print(f"Error in no parameters test: {str(e)}")
            import traceback

            print(traceback.format_exc())

        # Test Case 3: Invalid template ID
        print("\n4. Testing with invalid template ID...")
        try:
            result = await call_tool(
                "create_from_confluence_template",
                {
                    "template_id": "invalid_template_id",
                    "space_key": "IS",
                    "title": f"Test Template Page - Invalid Template {timestamp}",
                },
            )
            formatted_result = format_tool_result(result)
            print(
                f"Invalid template ID result: {json.dumps(formatted_result, indent=2)}"
            )

        except Exception as e:
            print(f"Error in invalid template ID test: {str(e)}")
            import traceback

            print(traceback.format_exc())

    except Exception as e:
        print(f"Error getting templates: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


async def test_space_key_validation():
    """Test space key validation and lookup functionality."""
    print("\n=== Testing Space Key Validation ===")

    # First get available spaces for validation
    print("\nFetching available spaces...")
    try:
        config = Config.from_env()
        confluence = ConfluenceFetcher()
        spaces = confluence.get_spaces()
        if not spaces or "results" not in spaces:
            print("ERROR: Failed to fetch spaces")
            return False

        valid_space = spaces["results"][0] if spaces["results"] else None
        if not valid_space:
            print("ERROR: No spaces available for testing")
            return False

        valid_space_key = valid_space["key"]
        valid_space_name = valid_space["name"]

        # Generate a unique timestamp for this test run
        timestamp = int(time.time())

        # Test Case 1: Valid space key
        print("\n1. Testing valid space key...")
        try:
            result = await call_tool(
                "confluence_create_page",
                {
                    "space_key": valid_space_key,
                    "title": f"Test Valid Space Key {timestamp}",
                    "content": [
                        {
                            "type": "text",
                            "content": "This is a test page for space key validation.",
                        }
                    ],
                },
            )
            formatted_result = format_tool_result(result)
            print(f"Valid space key result: {json.dumps(formatted_result, indent=2)}")

            # Clean up if successful
            if formatted_result and formatted_result.get("success"):
                page_id = formatted_result.get("page_id")
                if page_id:
                    await call_tool("confluence_delete_page", {"page_id": page_id})

        except Exception as e:
            print(f"Error testing valid space key: {str(e)}")

        # Test Case 2: Space name instead of key
        print("\n2. Testing space name instead of key...")
        try:
            result = await call_tool(
                "confluence_create_page",
                {
                    "space_key": valid_space_name,  # Using name instead of key
                    "title": f"Test Space Name {timestamp}",
                    "content": [
                        {
                            "type": "text",
                            "content": "This is a test page using space name.",
                        }
                    ],
                },
            )
            formatted_result = format_tool_result(result)
            print(f"Space name result: {json.dumps(formatted_result, indent=2)}")

            # Clean up if successful
            if formatted_result and formatted_result.get("success"):
                page_id = formatted_result.get("page_id")
                if page_id:
                    await call_tool("confluence_delete_page", {"page_id": page_id})

        except Exception as e:
            print(f"Error testing space name: {str(e)}")

        # Test Case 3: Invalid space key
        print("\n3. Testing invalid space key...")
        try:
            result = await call_tool(
                "confluence_create_page",
                {
                    "space_key": "NONEXISTENT",
                    "title": f"Test Invalid Space Key {timestamp}",
                    "content": [
                        {"type": "text", "content": "This page should not be created."}
                    ],
                },
            )
            formatted_result = format_tool_result(result)
            print(f"Invalid space key result: {json.dumps(formatted_result, indent=2)}")

            # Clean up if somehow successful
            if formatted_result and formatted_result.get("success"):
                page_id = formatted_result.get("page_id")
                if page_id:
                    await call_tool("confluence_delete_page", {"page_id": page_id})

        except Exception as e:
            print(f"Error testing invalid space key: {str(e)}")

        # Test Case 4: Case-insensitive space key
        print("\n4. Testing case-insensitive space key...")
        try:
            result = await call_tool(
                "confluence_create_page",
                {
                    "space_key": valid_space_key.lower(),  # Using lowercase version
                    "title": f"Test Case Insensitive {timestamp}",
                    "content": [
                        {
                            "type": "text",
                            "content": "This is a test page using case-insensitive key.",
                        }
                    ],
                },
            )
            formatted_result = format_tool_result(result)
            print(f"Case-insensitive result: {json.dumps(formatted_result, indent=2)}")

            # Clean up if successful
            if formatted_result and formatted_result.get("success"):
                page_id = formatted_result.get("page_id")
                if page_id:
                    await call_tool("confluence_delete_page", {"page_id": page_id})

        except Exception as e:
            print(f"Error testing case-insensitive key: {str(e)}")

    except Exception as e:
        print(f"ERROR: Error during test execution: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())
        return False

    return True


async def test_confluence_update_page():
    """Test updating a Confluence page with rich formatting."""
    print("\n1. Testing update with rich formatting...")
    page_id = "10651592"  # Using existing page ID
    print(f"\nAttempting to update page {page_id}...")

    # Test updating with rich formatting
    result = await call_tool(
        "confluence_update_page",
        {
            "page_id": page_id,
            "title": "Test Update Page",
            "content": [
                {
                    "type": "heading",
                    "content": "Test Update",
                    "properties": {"level": 1},
                },
                {"type": "text", "content": "This is a test update."},
                {
                    "type": "list",
                    "style": "bullet",
                    "items": ["Item 1", "Item 2", "Item 3"],
                },
                {
                    "type": "panel",
                    "content": "This is a panel",
                    "properties": {"type": "info", "title": "Info Panel"},
                },
                {
                    "type": "code",
                    "content": "print('Hello World')",
                    "properties": {"language": "python"},
                },
            ],
        },
    )
    formatted_result = format_tool_result(result)
    print(f"Update result: {formatted_result}")

    # Test case 2: Update with invalid content format
    print("\n2. Testing update with invalid content format...")
    try:
        invalid_result = await call_tool(
            "confluence_update_page",
            {
                "page_id": "invalid_id",
                "title": "Test Invalid Update",
                "content": "Invalid content format",  # This should fail as content needs to be a list
            },
        )
        formatted_invalid_result = format_tool_result(invalid_result)
        print(f"Invalid content format result: {formatted_invalid_result}")
    except Exception as e:
        print(f"Expected error occurred: {str(e)}")

    return True


if __name__ == "__main__":
    # asyncio.run(test_unified_search())
    # asyncio.run(test_get_confluence_templates())
    # asyncio.run(test_get_jira_templates())
    # asyncio.run(test_create_from_confluence_template())
    # asyncio.run(test_confluence_update_page())
    asyncio.run(test_space_key_validation())
