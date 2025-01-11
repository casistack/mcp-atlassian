import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Set testing environment
os.environ["TESTING"] = "1"

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import ContentEditor
from mcp_atlassian.jira import JiraHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_team_information_management():
    """Test AI's ability to manage team information in Confluence."""
    editor = ContentEditor()
    space_key = "IS"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    page_title = f"Team Information Test {timestamp}"

    logger.info("\n" + "=" * 80)
    logger.info("## Team Information Management Test Suite")
    logger.info("=" * 80 + "\n")

    try:
        # Create team information page
        logger.info("# Creating Team Information Page")
        initial_content = [
            {"type": "status", "text": "Current", "color": "green"},
            {
                "type": "text",
                "content": "This page contains team information managed by AI.",
            },
        ]
        editor.create_page(space_key, page_title, initial_content)
        logger.info("✓ Created team information page")

        # Add team member table
        logger.info("\n# Adding Team Member Information")
        team_table = {
            "type": "table",
            "headers": ["Name", "Role", "Department", "Contact", "Projects"],
            "rows": [
                [
                    "John Doe",
                    "Tech Lead",
                    "Engineering",
                    "john@example.com",
                    "Project A, Project B",
                ],
                [
                    "Jane Smith",
                    "Developer",
                    "Engineering",
                    "jane@example.com",
                    "Project C",
                ],
                [
                    "Bob Wilson",
                    "Product Owner",
                    "Product",
                    "bob@example.com",
                    "Project A",
                ],
            ],
        }
        editor.add_section(page_title, space_key, "Team Members", [team_table])
        logger.info("✓ Added team member table")

        # Add responsibilities section
        logger.info("\n# Adding Role Responsibilities")
        responsibilities = {
            "type": "list",
            "style": "bullet",
            "items": [
                "Tech Lead:",
                "  - Technical decision making",
                "  - Code review management",
                "  - Architecture planning",
                "Developer:",
                "  - Feature implementation",
                "  - Unit testing",
                "  - Documentation",
                "Product Owner:",
                "  - Backlog management",
                "  - Stakeholder communication",
                "  - Sprint planning",
            ],
        }
        editor.add_section(
            page_title, space_key, "Role Responsibilities", [responsibilities]
        )
        logger.info("✓ Added role responsibilities")

        # Add project relationships
        logger.info("\n# Adding Project Relationships")
        project_info = [
            {
                "type": "table",
                "headers": ["Project", "Status", "Dependencies", "Key Stakeholders"],
                "rows": [
                    ["Project A", "In Progress", "Project B", "John, Bob"],
                    ["Project B", "Planning", "None", "John"],
                    ["Project C", "Active", "Project A", "Jane"],
                ],
            },
            {
                "type": "text",
                "content": "For detailed project information, please refer to the respective project pages.",
            },
        ]
        editor.add_section(page_title, space_key, "Project Relationships", project_info)
        logger.info("✓ Added project relationships")

        # Add contact information panel
        logger.info("\n# Adding Contact Information Panel")
        editor.add_panel(
            page_title,
            space_key,
            "Contact Information",
            "For urgent matters, please contact the team lead at: team-lead@example.com",
            "note",
            "Important Contacts",
        )
        logger.info("✓ Added contact information panel")

        logger.info("\n" + "=" * 80)
        logger.info("## Test Completion Summary")
        logger.info("=" * 80)
        logger.info("✓ Successfully tested team information management")
        logger.info(
            f"✓ Test page available at: https://your-domain.atlassian.net/wiki/spaces/{space_key}/pages/{page_title}"
        )
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Error in team information management test: {str(e)}")
        raise


def test_project_timeline_management():
    """Test AI's ability to manage project timelines in Confluence."""
    editor = ContentEditor()
    jira = JiraHandler()
    space_key = "IS"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    page_title = f"Project Timeline Test {timestamp}"

    logger.info("\n" + "=" * 80)
    logger.info("## Project Timeline Management Test Suite")
    logger.info("=" * 80 + "\n")

    try:
        # Create project timeline page
        logger.info("# Creating Project Timeline Page")
        initial_content = [
            {"type": "status", "text": "In Progress", "color": "blue"},
            {
                "type": "text",
                "content": "This page tracks project timeline and milestones.",
            },
        ]
        editor.create_page(space_key, page_title, initial_content)
        logger.info("✓ Created project timeline page")

        # Add milestone table
        logger.info("\n# Adding Project Milestones")
        milestone_table = {
            "type": "table",
            "headers": ["Milestone", "Due Date", "Status", "Dependencies", "Owner"],
            "rows": [
                [
                    "Project Kickoff",
                    "2024-01-15",
                    "Completed",
                    "None",
                    "Project Manager",
                ],
                ["Design Phase", "2024-02-01", "In Progress", "Kickoff", "Design Lead"],
                [
                    "Development Start",
                    "2024-02-15",
                    "Not Started",
                    "Design Phase",
                    "Tech Lead",
                ],
                [
                    "Beta Release",
                    "2024-03-15",
                    "Not Started",
                    "Development",
                    "Release Manager",
                ],
            ],
        }
        editor.add_section(
            page_title, space_key, "Project Milestones", [milestone_table]
        )
        logger.info("✓ Added milestone table")

        # Add dependencies visualization
        logger.info("\n# Adding Dependencies Section")
        dependencies = [
            {
                "type": "text",
                "content": "Critical Path Dependencies:",
            },
            {
                "type": "list",
                "style": "bullet",
                "items": [
                    "Kickoff → Design Phase",
                    "Design Phase → Development Start",
                    "Development Start → Beta Release",
                ],
            },
        ]
        editor.add_section(page_title, space_key, "Dependencies", dependencies)
        logger.info("✓ Added dependencies section")

        # Add risk assessment
        logger.info("\n# Adding Risk Assessment")
        risk_table = {
            "type": "table",
            "headers": ["Risk", "Impact", "Probability", "Mitigation"],
            "rows": [
                ["Resource Availability", "High", "Medium", "Early resource planning"],
                ["Technical Challenges", "High", "Low", "Technical spike planned"],
                ["Timeline Slip", "Medium", "Medium", "Buffer included in schedule"],
            ],
        }
        editor.add_section(page_title, space_key, "Risk Assessment", [risk_table])
        logger.info("✓ Added risk assessment")

        # Add progress tracking
        logger.info("\n# Adding Progress Tracking")
        progress = [
            {
                "type": "status",
                "text": "25% Complete",
                "color": "blue",
            },
            {
                "type": "panel",
                "panelType": "info",
                "title": "Current Sprint Progress",
                "content": "Sprint 1 is currently in progress with 5 out of 20 story points completed.",
            },
        ]
        editor.add_section(page_title, space_key, "Progress Tracking", progress)
        logger.info("✓ Added progress tracking")

        logger.info("\n" + "=" * 80)
        logger.info("## Test Completion Summary")
        logger.info("=" * 80)
        logger.info("✓ Successfully tested project timeline management")
        logger.info(
            f"✓ Test page available at: https://your-domain.atlassian.net/wiki/spaces/{space_key}/pages/{page_title}"
        )
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Error in project timeline management test: {str(e)}")
        raise


if __name__ == "__main__":
    test_team_information_management()
    test_project_timeline_management()
