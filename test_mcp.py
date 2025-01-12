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


async def test_jira_get_project_issues():
    """Test retrieving all issues for a Jira project."""
    try:
        if not validate_config():
            print("ERROR: Configuration validation failed")
            return

        print("\n=== Testing Jira Project Issues Retrieval ===")

        # Initialize the JiraFetcher
        jira = JiraFetcher()
        print("\nJira connection initialized")

        # Test Case 1: Get issues with default limit
        print("\n1. Testing issue retrieval with default limit...")
        try:
            # Get project key first
            projects = jira.jira.projects()
            if not projects:
                print("No projects found. Please create a project in Jira first.")
                return

            project_key = projects[0].get("key")
            print(f"Using project: {project_key}")

            print("\nFetching issues with default limit...")
            results = jira.get_project_issues(project_key)
            if results:
                print("\nProject issues (default limit):")
                for doc in results:
                    print(f"\nKey: {doc.metadata['key']}")
                    print(f"Summary: {doc.metadata['summary']}")
                    print(f"Status: {doc.metadata['status']}")
                    print(f"Type: {doc.metadata['type']}")
            else:
                print("No issues found in project")

        except Exception as e:
            print(f"Error in default limit retrieval: {e}")
            import traceback

            print("\nFull error details:")
            print(traceback.format_exc())

        # Test Case 2: Get issues with custom limit
        print("\n2. Testing issue retrieval with custom limit...")
        try:
            print("\nFetching issues with limit of 2...")
            results = jira.get_project_issues(project_key, limit=2)
            if results:
                print("\nProject issues (limit: 2):")
                for doc in results:
                    print(f"\nKey: {doc.metadata['key']}")
                    print(f"Summary: {doc.metadata['summary']}")
            else:
                print("No issues found in project")

        except Exception as e:
            print(f"Error in custom limit retrieval: {e}")

        # Test Case 3: Get issues from non-existent project
        print("\n3. Testing retrieval from non-existent project...")
        try:
            invalid_project = "NONEXIST"
            print(f"\nAttempting to fetch issues from project: {invalid_project}")
            results = jira.get_project_issues(invalid_project)
            if results:
                print("Error: Retrieved issues from non-existent project")
            else:
                print("✓ Successfully handled non-existent project")

        except Exception as e:
            print(f"Expected error for non-existent project: {e}")

    except Exception as e:
        print(f"ERROR: Error during test execution: {e}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


async def test_create_jira_issue():
    """Test Jira issue creation functionality."""
    try:
        if not validate_config():
            print("ERROR: Configuration validation failed")
            return

        print("\n=== Testing Jira Issue Creation ===")

        # Initialize the JiraFetcher
        jira = JiraFetcher()
        print("\nJira connection initialized")

        # Keep track of created issues for cleanup
        created_issues = []

        # Test Case 1: Create basic issue
        print("\n1. Testing basic issue creation...")
        try:
            # Get project key first
            projects = jira.jira.projects()
            if not projects:
                print("No projects found. Please create a project in Jira first.")
                return

            project_key = projects[0].get("key")
            print(f"Using project: {project_key}")

            # Get available issue types
            print("\nFetching available issue types...")
            issue_types = jira.jira.get_issue_types()
            print("Available Issue Types:")
            for itype in issue_types:
                print(f"- {itype.get('name')} (ID: {itype.get('id')})")

            # Find a Task or Story issue type, defaulting to the first available type
            issue_type = next(
                (
                    t.get("name")
                    for t in issue_types
                    if t.get("name") in ["Task", "Story"]
                ),
                issue_types[0].get("name") if issue_types else "Task",
            )
            print(f"\nUsing issue type: {issue_type}")

            print("\nCreating basic issue...")
            issue = jira.create_issue(
                project_key=project_key,
                summary="Basic Test Issue",
                description="This is a basic test issue created by the test suite.",
                issue_type=issue_type,
            )

            if issue:
                print("✓ Successfully created basic issue")
                print(f"Key: {issue.metadata['key']}")
                print(f"Summary: {issue.metadata['summary']}")
                print(f"Type: {issue.metadata['type']}")
                print(f"Status: {issue.metadata['status']}")
                created_issues.append(issue.metadata["key"])
            else:
                print("✗ Failed to create basic issue")

        except Exception as e:
            print(f"Error in basic issue creation: {e}")
            import traceback

            print("\nFull error details:")
            print(traceback.format_exc())

        # Test Case 2: Create issue with custom fields
        print("\n2. Testing issue creation with custom fields...")
        try:
            print("\nFetching available priorities...")
            # Use get_all_priorities() instead of get_priorities()
            priorities = jira.jira.get_all_priorities()
            if not priorities:
                print("No priorities found in Jira instance")
                return

            print("Available Priorities:")
            for priority in priorities:
                print(f"- {priority.get('name')} (ID: {priority.get('id')})")

            # Use the first priority found
            priority = priorities[0]
            print(f"\nUsing priority: {priority.get('name')}")

            print("\nCreating issue with priority and labels...")
            issue = jira.create_issue(
                project_key=project_key,
                summary="Test Issue with Custom Fields",
                description="This is a test issue with custom fields.",
                issue_type=issue_type,
                priority=priority.get("id"),  # Use ID instead of name
                labels=["test", "automated"],
            )

            if issue:
                print("✓ Successfully created issue with custom fields")
                print(f"Key: {issue.metadata['key']}")
                print(f"Summary: {issue.metadata['summary']}")
                print(f"Priority: {issue.metadata.get('priority', 'Not set')}")
                print(f"Labels: {', '.join(['test', 'automated'])}")
                created_issues.append(issue.metadata["key"])
            else:
                print("✗ Failed to create issue with custom fields")
                print(
                    "Please check if the priority field is configured correctly in your Jira instance"
                )

        except Exception as e:
            print(f"Error in custom fields issue creation: {e}")
            import traceback

            print("\nFull error details:")
            print(traceback.format_exc())

        # Test Case 3: Create issue with attachment
        print("\n3. Testing issue creation with attachment...")
        try:
            # Create a test file
            with open("test_attachment.txt", "w") as f:
                f.write("This is a test attachment")

            print("\nCreating issue with attachment...")
            issue = jira.create_issue(
                project_key=project_key,
                summary="Test Issue with Attachment",
                description="This is a test issue that will have an attachment.",
                issue_type=issue_type,
            )

            if issue:
                print("✓ Successfully created issue")
                print(f"Key: {issue.metadata['key']}")

                # Add attachment
                attachment = jira.jira.add_attachment_object(
                    issue_key=issue.metadata["key"], attachment="test_attachment.txt"
                )

                if attachment:
                    print("✓ Successfully added attachment")
                else:
                    print("✗ Failed to add attachment")

                created_issues.append(issue.metadata["key"])

                # Clean up test file
                os.remove("test_attachment.txt")
            else:
                print("✗ Failed to create issue for attachment")

        except Exception as e:
            print(f"Error in attachment issue creation: {e}")
            if os.path.exists("test_attachment.txt"):
                os.remove("test_attachment.txt")

        # Test Case 4: Create issue with invalid project
        print("\n4. Testing issue creation with invalid project...")
        try:
            invalid_project = "NONEXIST"
            print(f"\nAttempting to create issue in project: {invalid_project}")
            issue = jira.create_issue(
                project_key=invalid_project,
                summary="Test Issue in Invalid Project",
                description="This issue should not be created.",
                issue_type=issue_type,
            )

            if issue:
                print("Error: Successfully created issue in non-existent project")
                created_issues.append(issue.metadata["key"])
            else:
                print("✓ Successfully handled invalid project")

        except Exception as e:
            print(f"Expected error for invalid project: {e}")

        # Cleanup
        print("\nCleaning up test issues...")
        for issue_key in created_issues:
            try:
                if jira.delete_issue(issue_key):
                    print(f"Deleted test issue: {issue_key}")
                else:
                    print(f"Failed to delete test issue: {issue_key}")
            except Exception as e:
                print(f"Error deleting issue {issue_key}: {e}")

    except Exception as e:
        print(f"ERROR: Error during test execution: {e}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


if __name__ == "__main__":
    # asyncio.run(test_jira_get_issue())
    # asyncio.run(test_jira_search())
    # asyncio.run(test_jira_get_project_issues())
    asyncio.run(test_create_jira_issue())
