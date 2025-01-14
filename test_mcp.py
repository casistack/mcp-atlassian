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
    print(f"\nDEBUG: Raw tool result: {result}")

    if not result:
        print("DEBUG: Empty result")
        return None

    # Get the first text content
    try:
        text_content = result[0]
        print(f"DEBUG: Text content: {text_content}")

        # If it's JSON, parse it
        try:
            return json.loads(text_content.text)
        except json.JSONDecodeError:
            return text_content.text
    except (IndexError, AttributeError) as e:
        print(f"DEBUG: Error processing result: {str(e)}")
        return None


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


async def test_rest_api_guide_update():
    """Test updating a Confluence page with the REST API Development Guide content."""
    print("\n=== Testing REST API Guide Update ===")
    page_id = "13107341"  # The specific page ID that failed
    print(f"\nAttempting to update page {page_id}...")

    try:
        config = Config.from_env()
        confluence = ConfluenceFetcher()
        content_editor = ContentEditor()

        print("\nFetching current page state...")
        current_page = confluence.confluence.get_page_by_id(
            page_id=page_id, expand="body.storage,version,space"
        )

        if not current_page:
            print(f"ERROR: Page {page_id} not found")
            return

        print(f"Current page version: {current_page.get('version', {}).get('number')}")
        print(f"Current page title: {current_page.get('title')}")
        print(f"Current space key: {current_page.get('space', {}).get('key')}")

        # This is the exact content structure the AI tried to use
        result = await call_tool(
            "confluence_update_page",
            {
                "page_id": page_id,
                "title": "REST API Development Guide",
                "content": [
                    {"type": "toc"},
                    {
                        "type": "heading",
                        "content": "Executive Summary",
                        "properties": {"level": 2},
                    },
                    {
                        "type": "status",
                        "content": "Current Version: 2.0",
                        "properties": {"color": "blue"},
                    },
                    {
                        "type": "text",
                        "content": "This guide provides comprehensive documentation for developing and consuming REST APIs, covering best practices, technical details, implementation guidance, and troubleshooting.",
                    },
                    {
                        "type": "heading",
                        "content": "1. Overview",
                        "properties": {"level": 2},
                    },
                    {
                        "type": "text",
                        "content": "REST (Representational State Transfer) is an architectural style for distributed systems. Key principles include:",
                    },
                    {
                        "type": "list",
                        "items": [
                            "➤ Client-server architecture",
                            "➤ Statelessness",
                            "➤ Cacheability",
                            "➤ Uniform interface",
                            "➤ Layered system",
                            "➤ Code on demand (optional)",
                        ],
                        "style": "bullet",
                    },
                    {
                        "type": "heading",
                        "content": "2. Technical Details",
                        "properties": {"level": 2},
                    },
                    {
                        "type": "heading",
                        "content": "2.1 Authentication Methods",
                        "properties": {"level": 3},
                    },
                    {
                        "type": "table",
                        "headers": ["Method", "Description", "Security Level"],
                        "rows": [
                            ["API Key", "Simple key-based authentication", "Medium"],
                            ["OAuth 2.0", "Token-based authentication", "High"],
                            ["Basic Auth", "Username/password in header", "Low"],
                            ["JWT", "JSON Web Tokens", "High"],
                        ],
                    },
                    {
                        "type": "heading",
                        "content": "2.2 Request/Response Formats",
                        "properties": {"level": 3},
                    },
                    {
                        "type": "code",
                        "content": "GET /api/v1/users HTTP/1.1\nHost: api.example.com\nAccept: application/json\nAuthorization: Bearer {token}",
                        "properties": {"language": "http"},
                    },
                    {
                        "type": "code",
                        "content": 'HTTP/1.1 200 OK\nContent-Type: application/json\n\n{\n  "data": [\n    {\n      "id": 1,\n      "name": "John Doe"\n    }\n  ]\n}',
                        "properties": {"language": "http"},
                    },
                    {
                        "type": "heading",
                        "content": "2.3 Rate Limiting",
                        "properties": {"level": 3},
                    },
                    {
                        "type": "panel",
                        "content": "API rate limits are enforced to ensure fair usage and system stability. Default limits are 1000 requests per hour per API key.",
                        "properties": {"type": "warning", "title": "Important"},
                    },
                    {
                        "type": "heading",
                        "content": "3. Implementation Guide",
                        "properties": {"level": 2},
                    },
                    {
                        "type": "heading",
                        "content": "3.1 Setup Steps",
                        "properties": {"level": 3},
                    },
                    {
                        "type": "list",
                        "items": [
                            "① Install required dependencies",
                            "② Configure environment variables",
                            "③ Initialize API client",
                            "④ Set up authentication",
                            "⑤ Implement error handling",
                            "⑥ Add logging",
                            "⑦ Configure rate limiting",
                        ],
                        "style": "numbered",
                    },
                    {
                        "type": "heading",
                        "content": "3.2 Best Practices",
                        "properties": {"level": 3},
                    },
                    {
                        "type": "list",
                        "items": [
                            "• Use HTTPS for all API endpoints",
                            "• Implement proper error handling",
                            "• Use versioning in API endpoints",
                            "• Document all endpoints thoroughly",
                            "• Implement rate limiting",
                            "• Use appropriate HTTP status codes",
                            "• Validate all input data",
                        ],
                        "style": "bullet",
                    },
                    {
                        "type": "heading",
                        "content": "3.3 Common Patterns",
                        "properties": {"level": 3},
                    },
                    {
                        "type": "code",
                        "content": "// Example of pagination\nGET /api/v1/users?page=2&limit=50",
                        "properties": {"language": "http"},
                    },
                    {
                        "type": "code",
                        "content": "// Example of filtering\nGET /api/v1/users?status=active&role=admin",
                        "properties": {"language": "http"},
                    },
                    {
                        "type": "heading",
                        "content": "4. Troubleshooting",
                        "properties": {"level": 2},
                    },
                    {
                        "type": "heading",
                        "content": "4.1 Common Issues",
                        "properties": {"level": 3},
                    },
                    {
                        "type": "heading",
                        "content": "4.2 Error Codes",
                        "properties": {"level": 3},
                    },
                    {
                        "type": "table",
                        "headers": ["Code", "Description"],
                        "rows": [
                            ["400", "Bad Request"],
                            ["401", "Unauthorized"],
                            ["403", "Forbidden"],
                            ["404", "Not Found"],
                            ["429", "Too Many Requests"],
                            ["500", "Internal Server Error"],
                        ],
                    },
                    {
                        "type": "heading",
                        "content": "5. Examples",
                        "properties": {"level": 2},
                    },
                    {
                        "type": "code",
                        "content": '// Create User\nPOST /api/v1/users\nContent-Type: application/json\n\n{\n  "name": "Jane Doe",\n  "email": "jane@example.com"\n}',
                        "properties": {"language": "http"},
                    },
                    {
                        "type": "code",
                        "content": '// Successful Response\nHTTP/1.1 201 Created\nContent-Type: application/json\n\n{\n  "id": 123,\n  "name": "Jane Doe",\n  "email": "jane@example.com"\n}',
                        "properties": {"language": "http"},
                    },
                    {
                        "type": "code",
                        "content": '// Error Response\nHTTP/1.1 400 Bad Request\nContent-Type: application/json\n\n{\n  "error": {\n    "code": "invalid_email",\n    "message": "Invalid email format"\n  }\n}',
                        "properties": {"language": "http"},
                    },
                ],
            },
        )
        formatted_result = format_tool_result(result)
        print(f"Update result: {json.dumps(formatted_result, indent=2)}")

        if not formatted_result.get("success"):
            print("\nDebug information:")
            print(f"Page ID: {page_id}")
            print(f"Current version: {current_page.get('version', {}).get('number')}")
            print(f"Current title: {current_page.get('title')}")
            print(f"Space key: {current_page.get('space', {}).get('key')}")
            print(f"Error message: {formatted_result.get('error')}")

    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


async def test_draw_io_diagrams():
    """Test creating and managing draw.io diagrams in Confluence."""
    print("\n=== Testing Draw.io Diagram Tools ===")

    try:
        # First, get a valid space key
        print("\nFetching available spaces...")
        config = Config.from_env()
        confluence = ConfluenceFetcher()
        spaces = confluence.get_spaces()

        if not spaces or "results" not in spaces or not spaces["results"]:
            print("ERROR: No Confluence spaces available")
            return

        space = spaces["results"][0]
        space_key = space["key"]
        print(f"Using space: {space['name']} (key: {space_key})")

        # Create a new page to hold our test diagrams
        print("\nCreating test page...")
        page_result = await call_tool(
            "confluence_create_page",
            {
                "space_key": space_key,
                "title": f"Test Network Diagram {int(time.time())}",
                "content": [
                    {"type": "text", "content": "This page contains test diagrams."}
                ],
            },
        )

        print(f"\nDEBUG: Page creation result: {page_result}")
        formatted_result = format_tool_result(page_result)

        if formatted_result is None:
            print("ERROR: Failed to create test page - invalid result format")
            return

        if isinstance(formatted_result, str):
            print(f"ERROR: Unexpected result format: {formatted_result}")
            return

        page_id = formatted_result.get("page_id")
        if not page_id:
            print("ERROR: Failed to create test page - no page ID returned")
            print(f"Result: {formatted_result}")
            return

        print(f"Created test page with ID: {page_id}")

        # Create a network diagram
        print("\nCreating network diagram...")
        diagram_result = await call_tool(
            "create_diagram",
            {
                "page_id": page_id,
                "diagram_name": "Test Network Infrastructure",
                "diagram_type": "network",
                "elements": [
                    {
                        "id": "internet",
                        "type": "mxgraph.networks.cloud",
                        "x": 50,
                        "y": 50,
                        "width": 100,
                        "height": 80,
                        "label": "Internet",
                        "style": {
                            "fill_color": "#f5f5f5",
                            "stroke_color": "#666666",
                        },
                    },
                    {
                        "id": "firewall",
                        "type": "mxgraph.networks.firewall",
                        "x": 200,
                        "y": 60,
                        "width": 60,
                        "height": 60,
                        "label": "Firewall",
                        "style": {
                            "fill_color": "#ff9999",
                            "stroke_color": "#ff0000",
                        },
                    },
                    {
                        "id": "router",
                        "type": "mxgraph.networks.router",
                        "x": 320,
                        "y": 60,
                        "width": 60,
                        "height": 60,
                        "label": "Core Router",
                        "style": {
                            "fill_color": "#99ccff",
                            "stroke_color": "#0066cc",
                        },
                    },
                    {
                        "id": "switch1",
                        "type": "mxgraph.networks.switch",
                        "x": 320,
                        "y": 180,
                        "width": 60,
                        "height": 60,
                        "label": "Main Switch",
                        "style": {
                            "fill_color": "#99ff99",
                            "stroke_color": "#009900",
                        },
                    },
                    {
                        "id": "server1",
                        "type": "mxgraph.networks.server",
                        "x": 200,
                        "y": 300,
                        "width": 80,
                        "height": 100,
                        "label": "Web Server",
                        "style": {
                            "fill_color": "#ffcc99",
                            "stroke_color": "#ff9900",
                        },
                    },
                    {
                        "id": "server2",
                        "type": "mxgraph.networks.server",
                        "x": 440,
                        "y": 300,
                        "width": 80,
                        "height": 100,
                        "label": "Database",
                        "style": {
                            "fill_color": "#ffcc99",
                            "stroke_color": "#ff9900",
                        },
                    },
                ],
                "connections": [
                    {
                        "source": "internet",
                        "target": "firewall",
                        "type": "straight",
                        "label": "WAN",
                    },
                    {
                        "source": "firewall",
                        "target": "router",
                        "type": "straight",
                        "label": "DMZ",
                    },
                    {
                        "source": "router",
                        "target": "switch1",
                        "type": "straight",
                        "label": "1Gbps",
                    },
                    {
                        "source": "switch1",
                        "target": "server1",
                        "type": "straight",
                        "label": "LAN 1",
                    },
                    {
                        "source": "switch1",
                        "target": "server2",
                        "type": "straight",
                        "label": "LAN 2",
                    },
                ],
                "style": {
                    "theme": "default",
                    "background": "white",
                    "grid": True,
                    "shadow": True,
                },
            },
        )
        formatted_result = format_tool_result(diagram_result)
        print(f"Create diagram result: {json.dumps(formatted_result, indent=2)}")

        # Wait for the page to be updated
        time.sleep(5)  # Wait 5 seconds

        # Test Case 2: Get diagram data
        print("\n2. Testing diagram data retrieval...")
        if formatted_result and formatted_result.get("macro_id"):
            macro_id = formatted_result.get("macro_id")
            get_result = await call_tool(
                "get_diagram", {"page_id": page_id, "macro_id": macro_id}
            )
            print(
                f"Get diagram result: {json.dumps(format_tool_result(get_result), indent=2)}"
            )

        # Test Case 3: Update diagram
        print("\n3. Testing diagram update...")
        if formatted_result and formatted_result.get("macro_id"):
            update_result = await call_tool(
                "update_diagram",
                {
                    "page_id": page_id,
                    "macro_id": macro_id,
                    "elements": [
                        # Add a new server
                        {
                            "id": "server3",
                            "type": "mxgraph.networks.server",
                            "x": 320,
                            "y": 300,
                            "width": 80,
                            "height": 100,
                            "label": "Cache Server",
                            "style": {
                                "fill_color": "#ffcc99",
                                "stroke_color": "#ff9900",
                            },
                        }
                    ],
                    "connections": [
                        {
                            "source": "switch1",
                            "target": "server3",
                            "type": "straight",
                            "label": "LAN 3",
                        }
                    ],
                },
            )
            print(
                f"Update diagram result: {json.dumps(format_tool_result(update_result), indent=2)}"
            )

        # Clean up - delete the test page
        print("\n4. Cleaning up...")
        await call_tool("confluence_delete_page", {"page_id": page_id})

    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


if __name__ == "__main__":
    # asyncio.run(test_unified_search())
    # asyncio.run(test_get_confluence_templates())
    # asyncio.run(test_get_jira_templates())
    # asyncio.run(test_create_from_confluence_template())
    # asyncio.run(test_confluence_update_page())
    # asyncio.run(test_space_key_validation())
    # asyncio.run(test_rest_api_guide_update())
    asyncio.run(test_draw_io_diagrams())
