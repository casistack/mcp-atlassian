import os

os.environ["TESTING"] = "1"

import logging
from dotenv import load_dotenv
from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.content import MarkupFormatter
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-test")

# Load environment variables
load_dotenv()


def validate_credentials():
    """Validate that all required environment variables are set and credentials work."""
    logger.info("Validating environment variables and credentials...")

    # Check environment variables
    required_vars = [
        "CONFLUENCE_URL",
        "CONFLUENCE_USERNAME",
        "CONFLUENCE_API_TOKEN",
        "JIRA_URL",
        "JIRA_USERNAME",
        "JIRA_API_TOKEN",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    # Print all environment variables and their values
    print("Environment variables loaded:")
    for var in required_vars:
        value = os.getenv(var)
        # Mask sensitive values
        if value and ("TOKEN" in var or "PASSWORD" in var):
            masked_value = value[:4] + "*" * (len(value) - 4)
            print(f"{var}: {masked_value}")
        else:
            print(f"{var}: {value}")

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        return False

    # Test Confluence credentials
    try:
        logger.info("Testing Confluence credentials...")
        confluence = ConfluenceFetcher()
        spaces = confluence.get_spaces()
        if spaces is None:
            logger.error("Failed to connect to Confluence - check your credentials")
            return False
        logger.info("✓ Confluence credentials validated successfully")
    except Exception as e:
        logger.error(f"Confluence credential validation failed: {str(e)}")
        return False

    # Test Jira credentials
    try:
        logger.info("Testing Jira credentials...")
        jira = JiraFetcher()
        projects = jira.jira.projects()
        if projects is None:
            logger.error("Failed to connect to Jira - check your credentials")
            return False
        logger.info("✓ Jira credentials validated successfully")
    except Exception as e:
        logger.error(f"Jira credential validation failed: {str(e)}")
        return False

    return True


def test_confluence():
    logger.info("\n=== Testing Confluence Integration ===")
    try:
        confluence = ConfluenceFetcher()

        # List spaces
        logger.info("Listing Confluence spaces:")
        spaces = confluence.get_spaces()
        for space in spaces.get("results", []):
            logger.info(f"- {space['name']} ({space['key']})")

        if spaces.get("results"):
            space_key = spaces["results"][0]["key"]

            # Create a test page
            logger.info(f"Creating test page in space {space_key}")
            content = (
                MarkupFormatter.heading("Test Page")
                + MarkupFormatter.panel(
                    "This is a test page created by the MCP Atlassian integration.",
                    title="Description",
                    panel_type="info",
                )
                + MarkupFormatter.bullet_list(["Item 1", "Item 2", "Item 3"])
            )

            # Add timestamp to ensure unique page title
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            page_title = f"MCP Test Page {timestamp}"
            page = confluence.create_page(
                space_key=space_key, title=page_title, body=content
            )

            if page:
                logger.info(f"Created page: {page.metadata['url']}")

                # Update the page
                logger.info("Updating test page")
                updated_content = content + MarkupFormatter.note_macro(
                    "Update", "This page was updated!"
                )

                # Get current page version
                current_page = confluence.confluence.get_page_by_id(
                    page_id=page.metadata["page_id"], expand="version"
                )
                version = current_page.get("version", {}).get("number", 0)

                # Update the page with the correct signature from Atlassian API
                updated_page = confluence.confluence.update_existing_page(
                    page_id=page.metadata["page_id"],
                    title=page_title,
                    body=updated_content,
                    type="page",
                    representation="storage",
                    minor_edit=True,
                )

                if updated_page:
                    logger.info(
                        f"Updated page: {confluence.config.url}/wiki/spaces/{space_key}/pages/{updated_page['id']}"
                    )

                # Add attachment
                logger.info("Adding test attachment")
                # Create a test file
                with open("test_attachment.txt", "w") as f:
                    f.write("This is a test attachment")

                # For Confluence, use the direct API call with correct signature
                with open("test_attachment.txt", "rb") as f:
                    attachment = confluence.confluence.attach_file(
                        filename="test_attachment.txt", page_id=page.metadata["page_id"]
                    )

                if attachment:
                    logger.info(
                        f"Added attachment: {attachment[0].get('title', 'unknown') if isinstance(attachment, list) else attachment.get('title', 'unknown')}"
                    )

                # Clean up
                os.remove("test_attachment.txt")
                logger.info("Test attachment cleaned up")

    except Exception as e:
        logger.error(f"Error testing Confluence: {str(e)}", exc_info=True)


def test_jira():
    logger.info("\n=== Testing Jira Integration ===")
    try:
        jira = JiraFetcher()

        # List projects
        logger.info("Listing Jira projects:")
        projects = jira.jira.projects()
        for project in projects:
            logger.info(f"- {project['name']} ({project['key']})")

        if projects:
            project_key = projects[0]["key"]

            # Create a test issue
            logger.info(f"Creating test issue in project {project_key}")
            issue = jira.create_issue(
                project_key=project_key,
                summary="Test Issue from MCP",
                description="This is a test issue created by the MCP Atlassian integration.",
                issue_type="Task",
            )

            if issue:
                logger.info(f"Created issue: {issue.metadata['link']}")

                # Update the issue
                logger.info("Updating test issue")
                updated_issue = jira.update_issue(
                    issue_key=issue.metadata["key"],
                    summary="Test Issue from MCP (Updated)",
                    description="This issue was updated by the MCP Atlassian integration.",
                )

                if updated_issue:
                    logger.info(f"Updated issue: {updated_issue.metadata['link']}")

                # Add attachment
                logger.info("Adding test attachment")
                # Create a test file
                with open("test_attachment.txt", "w") as f:
                    f.write("This is a test attachment")

                # For Jira, use the direct API call with correct signature
                attachment = jira.jira.add_attachment_object(
                    issue_key=issue.metadata["key"], attachment="test_attachment.txt"
                )

                if attachment:
                    logger.info(
                        f"Added attachment: {attachment[0].get('filename', 'unknown') if isinstance(attachment, list) else attachment.get('filename', 'unknown')}"
                    )

                # Clean up
                os.remove("test_attachment.txt")
                logger.info("Test attachment cleaned up")

    except Exception as e:
        logger.error(f"Error testing Jira: {str(e)}", exc_info=True)


if __name__ == "__main__":
    # First validate credentials
    if validate_credentials():
        logger.info("Credentials validated successfully. Starting tests...")

        # Test Confluence integration
        test_confluence()

        # Test Jira integration
        test_jira()
    else:
        logger.error(
            "Credential validation failed. Please check your .env file and API tokens."
        )
