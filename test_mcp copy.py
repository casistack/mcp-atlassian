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


async def test_confluence_create_page():
    """Test Confluence page creation functionality using direct code calls."""
    try:
        if not validate_config():
            print("ERROR: Configuration validation failed")
            return

        print("\n=== Testing Confluence Create Page ===")

        # Initialize the ConfluenceFetcher and ContentEditor
        confluence = ConfluenceFetcher()
        editor = ContentEditor()

        # Test Case 1: Create basic page with title and text
        print("\n1. Testing basic page creation...")
        try:
            title = "Test Page - Basic Content"
            content = "This is a test page created by the automated test suite."
            space_key = "IS"  # Using IT Support space

            # Create the page
            page = confluence.create_page(space_key, title, content)
            if page:
                print(f"Successfully created basic page:")
                print(f"Title: {page.metadata['title']}")
                print(f"Space: {page.metadata['space_key']}")
                print(f"ID: {page.metadata['page_id']}")
                test_page_id = page.metadata["page_id"]  # Save for cleanup
            else:
                print("Failed to create basic page")
        except Exception as e:
            print(f"Error creating basic page: {str(e)}")

        # Test Case 2: Create page with rich formatting
        print("\n2. Testing page creation with rich formatting...")
        try:
            title = "Test Page - Rich Formatting"
            content_editor = ContentEditor()
            rich_editor = content_editor.create_editor()

            # Add formatted content
            rich_editor.heading("Main Heading", 1)
            rich_editor.text("This is a test page with rich formatting.")
            rich_editor.bold("This text should be bold.")
            rich_editor.italic("This text should be italic.")
            rich_editor.bullet_list(["Item 1", "Item 2", "Item 3"])
            rich_editor.table(
                headers=["Header 1", "Header 2"],
                rows=[["Cell 1", "Cell 2"], ["Cell 3", "Cell 4"]],
            )
            rich_editor.status("In Progress", "blue")
            rich_editor.code("print('Hello, World!')", "python")

            # Convert content to storage format
            formatted_content = content_editor.create_rich_content(
                rich_editor.get_content()
            )

            # Create the page using the formatted content
            page = confluence.create_page(
                space_key=space_key,
                title=title,
                body=formatted_content,
                representation="storage",
            )
            if page:
                print(f"Successfully created rich formatted page:")
                print(f"Title: {page.metadata['title']}")
                print(f"ID: {page.metadata['page_id']}")
                rich_page_id = page.metadata["page_id"]  # Save for cleanup
            else:
                print("Failed to create rich formatted page")
        except Exception as e:
            print(f"Error creating rich formatted page: {str(e)}")

        # Test Case 3: Create page with parent page
        print("\n3. Testing page creation with parent page...")
        try:
            # First, search for a suitable parent page
            parent_results = confluence.search(
                'type = page AND space = "IS" AND title ~ "Project Best Practices"',
                limit=1,
            )
            if parent_results:
                parent_page = parent_results[0]
                parent_id = parent_page.metadata["page_id"]

                title = "Test Page - With Parent"
                content = "This is a child page created under Project Best Practices."

                # Create the page with parent_id
                page = confluence.create_page(
                    space_key=space_key,
                    title=title,
                    body=content,
                    parent_id=parent_id,
                    representation="storage",  # Ensure we use storage format
                )

                if page:
                    print(f"Successfully created child page:")
                    print(f"Title: {page.metadata['title']}")
                    print(f"Parent: {parent_page.metadata['title']}")
                    print(f"ID: {page.metadata['page_id']}")
                    child_page_id = page.metadata["page_id"]  # Save for cleanup
                else:
                    print("Failed to create child page")
                    print(
                        "This might be due to permissions or parent page restrictions"
                    )
            else:
                print("Could not find suitable parent page")
        except Exception as e:
            print(f"Error creating page with parent: {str(e)}")
            print("This might be due to permissions or parent page configuration")

        # Test Case 4: Create page with invalid space
        print("\n4. Testing page creation with invalid space...")
        try:
            title = "Test Page - Invalid Space"
            content = "This page should not be created."
            invalid_space = "INVALID_SPACE"

            page = confluence.create_page(invalid_space, title, content)
            if page:
                print("Error: Successfully created page in invalid space")
            else:
                print("Successfully handled invalid space error")
        except Exception as e:
            print(f"Expected error for invalid space: {str(e)}")

        # Cleanup: Delete test pages
        print("\nCleaning up test pages...")
        try:
            if "test_page_id" in locals():
                confluence.delete_page(test_page_id)
                print(f"Deleted test page with ID: {test_page_id}")
            if "rich_page_id" in locals():
                confluence.delete_page(rich_page_id)
                print(f"Deleted rich formatted page with ID: {rich_page_id}")
            if "child_page_id" in locals():
                confluence.delete_page(child_page_id)
                print(f"Deleted child page with ID: {child_page_id}")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

    except Exception as e:
        print(f"ERROR: Error during test execution: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


async def test_confluence_update_page():
    """Test Confluence page update functionality using direct code calls."""
    try:
        if not validate_config():
            print("ERROR: Configuration validation failed")
            return

        print("\n=== Testing Confluence Update Page ===")

        # Initialize the ConfluenceFetcher and ContentEditor
        confluence = ConfluenceFetcher()
        editor = ContentEditor()

        # First create a test page to update
        print("\n1. Creating test page for updates...")
        try:
            title = "Test Page - For Updates"
            # Create initial content with proper Confluence storage format
            rich_editor = editor.create_editor()
            rich_editor.heading("Initial Content", 1)
            rich_editor.text("This is a test page that will be updated.")
            rich_editor.bullet_list(["Initial item 1", "Initial item 2"])

            formatted_content = editor.create_rich_content(rich_editor.get_content())
            space_key = "IS"

            page = confluence.create_page(space_key, title, formatted_content)
            if page:
                print(f"Successfully created test page:")
                print(f"Title: {page.metadata['title']}")
                print(f"ID: {page.metadata['page_id']}")
                print(f"URL: {page.metadata['url']}")
                test_page_id = page.metadata["page_id"]

                # Verify the page exists
                verify_page = confluence.get_page_content(test_page_id)
                if verify_page:
                    print("✓ Page verified - accessible via API")
                else:
                    print("✗ Page verification failed - not accessible via API")
            else:
                print("Failed to create test page")
                return
        except Exception as e:
            print(f"Error creating test page: {e}")
            return

        # Add a pause to allow manual verification
        print("\nPage has been created. Please verify it in your browser:")
        print(f"URL: {page.metadata['url']}")
        input("Press Enter to continue with updates...")

        # Test Case 1: Update page title
        print("\n2. Testing page title update...")
        try:
            # First get the existing page content
            print("Fetching current page content...")
            current_page = confluence.confluence.get_page_by_id(
                page_id=test_page_id, expand="body.storage,version"
            )
            if not current_page:
                print("Failed to get current page content")
                return

            current_version = current_page.get("version", {}).get("number", 0)
            print(f"Current page version: {current_version}")
            print(f"Current page title: {current_page.get('title')}")
            print(
                "Current page content length:",
                len(current_page["body"]["storage"]["value"]),
            )

            new_title = "Test Page - Updated Title"
            print(f"Attempting to update title to: {new_title}")

            # Keep the existing content but update the title
            print("Making update_page API call...")
            page = confluence.update_page(
                page_id=test_page_id,
                title=new_title,
                body=current_page["body"]["storage"]["value"],
                type="page",
                representation="storage",
                minor_edit=False,
            )
            if page:
                print(f"Successfully updated page title to: {page.metadata['title']}")
                print(f"New version: {page.metadata.get('version')}")
                print(f"URL: {page.metadata['url']}")
            else:
                print("Failed to update page title")
                print("Debug info:")
                print(f"Page ID: {test_page_id}")
                print(f"Attempted new title: {new_title}")
                print("Content length:", len(current_page["body"]["storage"]["value"]))
                print("Current version:", current_version)

        except Exception as e:
            print(f"Error updating page title: {e}")
            import traceback

            print("Full error details:")
            print(traceback.format_exc())

        # Test Case 2: Update page content with rich formatting
        print("\n3. Testing content update with rich formatting...")
        try:
            # First get the current page again as it may have changed
            print("Fetching current page content for content update...")
            current_page = confluence.confluence.get_page_by_id(
                page_id=test_page_id, expand="body.storage,version"
            )
            if not current_page:
                print("Failed to get current page content")
                return

            current_version = current_page.get("version", {}).get("number", 0)
            print(f"Current page version: {current_version}")
            print(f"Current page title: {current_page.get('title')}")
            print(
                "Current page content length:",
                len(current_page["body"]["storage"]["value"]),
            )

            # Create new content while preserving the title
            print("Creating new rich content...")
            rich_editor = editor.create_editor()
            rich_editor.heading("Updated Content", 1)
            rich_editor.text("This page has been updated with rich formatting.")
            rich_editor.bullet_list(["Update item 1", "Update item 2"])
            rich_editor.status("Updated", "green")

            formatted_content = editor.create_rich_content(rich_editor.get_content())
            print("New content length:", len(formatted_content))

            print("Making update_page API call...")
            page = confluence.update_page(
                page_id=test_page_id,
                title=current_page["title"],  # Keep the current title
                body=formatted_content,
                type="page",
                representation="storage",
                minor_edit=False,
            )
            if page:
                print("Successfully updated page content with rich formatting")
                print(f"New version: {page.metadata['version']}")
                print(f"URL: {page.metadata['url']}")
            else:
                print("Failed to update page content")
                print("Debug info:")
                print(f"Page ID: {test_page_id}")
                print(f"Current title: {current_page['title']}")
                print("New content length:", len(formatted_content))
                print("Current version:", current_version)

        except Exception as e:
            print(f"Error updating page content: {e}")
            import traceback

            print("Full error details:")
            print(traceback.format_exc())

        # Test Case 3: Update non-existent page
        print("\n4. Testing update of non-existent page...")
        try:
            invalid_page_id = "99999999"
            page = confluence.update_page(
                page_id=invalid_page_id,
                title="Invalid Page",
                body="This should fail",
                representation="storage",
            )
            if page:
                print("Error: Successfully updated non-existent page")
            else:
                print("Successfully handled non-existent page error")
        except Exception as e:
            print(f"Expected error for non-existent page: {e}")

        # Add a pause before cleanup
        input("\nPress Enter to proceed with cleanup...")

        # Cleanup
        print("\nCleaning up test pages...")
        try:
            if "test_page_id" in locals():
                confluence.delete_page(test_page_id)
                print(f"Deleted test page with ID: {test_page_id}")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

    except Exception as e:
        print(f"ERROR: Error during test execution: {str(e)}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


async def test_jira_get_issue():
    """Test Jira issue retrieval functionality."""
    try:
        if not validate_config():
            print("ERROR: Configuration validation failed")
            return

        print("\n=== Testing Jira Issue Retrieval ===")

        # Initialize the JiraFetcher
        jira = JiraFetcher()

        # Test Case 1: Get basic issue details
        print("\n1. Testing basic issue retrieval...")
        try:
            # First create a test issue
            print("Creating test issue...")
            issue = jira.create_issue(
                project_key="IS",
                summary="Test Issue for API Testing",
                description="This is a test issue created for API testing.",
                issue_type="Task",
            )
            if issue:
                print(f"Successfully created test issue:")
                print(f"Key: {issue.metadata['key']}")
                print(f"Summary: {issue.metadata['summary']}")
                print(f"URL: {issue.metadata['url']}")
                test_issue_key = issue.metadata["key"]

                # Now retrieve the issue
                print("\nRetrieving issue details...")
                retrieved_issue = jira.get_issue(test_issue_key)
                if retrieved_issue:
                    print("✓ Successfully retrieved issue")
                    print(f"Key: {retrieved_issue.metadata['key']}")
                    print(f"Summary: {retrieved_issue.metadata['summary']}")
                    print(f"Status: {retrieved_issue.metadata['status']}")
                    print(f"Issue Type: {retrieved_issue.metadata['issue_type']}")
                else:
                    print("✗ Failed to retrieve issue")
            else:
                print("Failed to create test issue")
                return
        except Exception as e:
            print(f"Error in basic issue retrieval: {e}")
            import traceback

            print("Full error details:")
            print(traceback.format_exc())

        # Test Case 2: Get issue with expanded fields
        print("\n2. Testing issue retrieval with expanded fields...")
        try:
            if test_issue_key:
                retrieved_issue = jira.get_issue(
                    test_issue_key, expand=["renderedFields", "names", "changelog"]
                )
                if retrieved_issue:
                    print("✓ Successfully retrieved issue with expanded fields")
                    print(f"Key: {retrieved_issue.metadata['key']}")
                    print(f"Summary: {retrieved_issue.metadata['summary']}")
                    print(
                        f"Description: {retrieved_issue.metadata.get('description', 'N/A')}"
                    )
                    print(f"Created: {retrieved_issue.metadata.get('created')}")
                    print(f"Updated: {retrieved_issue.metadata.get('updated')}")
                else:
                    print("✗ Failed to retrieve issue with expanded fields")
        except Exception as e:
            print(f"Error retrieving issue with expanded fields: {e}")
            import traceback

            print("Full error details:")
            print(traceback.format_exc())

        # Test Case 3: Get non-existent issue
        print("\n3. Testing retrieval of non-existent issue...")
        try:
            invalid_key = "IS-99999"
            retrieved_issue = jira.get_issue(invalid_key)
            if retrieved_issue:
                print("Error: Successfully retrieved non-existent issue")
            else:
                print("✓ Successfully handled non-existent issue error")
        except Exception as e:
            print(f"Expected error for non-existent issue: {e}")

        # Cleanup
        print("\nCleaning up test issues...")
        try:
            if "test_issue_key" in locals():
                if jira.delete_issue(test_issue_key):
                    print(f"Deleted test issue: {test_issue_key}")
                else:
                    print(f"Failed to delete test issue: {test_issue_key}")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    except Exception as e:
        print(f"ERROR: Error during test execution: {e}")
        import traceback

        print("\nFull error details:")
        print(traceback.format_exc())


async def main():
    print("Starting Confluence update page tests...")
    await test_confluence_update_page()
    print("\nTests completed.")


if __name__ == "__main__":
    asyncio.run(main())
