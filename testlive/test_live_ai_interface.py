import os
import sys
import time
from typing import Optional

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# Set testing environment
os.environ["TESTING"] = "1"

import logging
from datetime import datetime
from dotenv import load_dotenv
from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import MarkupFormatter, ContentEditor


# Configure logging with colors and formatting
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and markdown-style formatting"""

    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    green = "\x1b[32m"
    bold = "\x1b[1m"

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt

    def format(self, record):
        if record.levelno == logging.INFO:
            if record.msg.startswith("##"):  # Main section header
                color = self.blue + self.bold
            elif record.msg.startswith("#"):  # Sub-section header
                color = self.green + self.bold
            else:
                color = self.grey
        elif record.levelno == logging.ERROR:
            color = self.red
        elif record.levelno == logging.WARNING:
            color = self.yellow
        elif record.levelno == logging.DEBUG:
            color = self.grey
        else:
            color = self.grey

        record.msg = f"{color}{record.msg}{self.reset}"
        return logging.Formatter.format(self, record)


# Configure logger
logger = logging.getLogger("mcp-ai-test")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = ColoredFormatter("%(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Load environment variables
load_dotenv()


def simulate_ai_documentation_tasks():
    """
    This function simulates how an AI would use our MCP tools to create and manage
    documentation based on user requests.
    """
    try:
        # Initialize our tools
        editor = ContentEditor()
        confluence = ConfluenceFetcher()
        space_key = "IS"  # AI would get this from context

        logger.info("\n" + "=" * 80)
        logger.info("## AI Documentation Test Suite")
        logger.info("=" * 80 + "\n")

        # Scenario 1: User asks AI to "Create a server migration guide"
        logger.info("# Scenario 1: Creating Server Migration Documentation")
        logger.info("User Request: 'Create a comprehensive server migration guide'")

        # AI creates a new page with initial structure
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        page_title = f"Server Migration Guide {timestamp}"

        logger.info("Creating main documentation page...")
        initial_content = [
            {"type": "status", "text": "In Progress", "color": "blue"},
            {
                "type": "panel",
                "title": "Document Status",
                "content": "This guide is being actively developed",
                "panel_type": "info",
            },
            {
                "type": "text",
                "content": "This guide provides step-by-step instructions for migrating servers safely and efficiently.",
            },
            {"type": "toc", "min_level": 1, "max_level": 3},
        ]

        editor.create_page(
            space_key=space_key, title=page_title, content=initial_content
        )

        time.sleep(1)  # Small delay for better log readability
        logger.info("✓ Created main page with initial structure")

        # AI adds prerequisites section
        logger.info("\n# Adding Prerequisites Section")
        prerequisites = [
            "Access to both source and target servers",
            "Backup solution in place",
            "Network connectivity between servers",
            "Required permissions and credentials",
            "Maintenance window approval",
        ]

        editor.add_section(
            page_title=page_title,
            space_key=space_key,
            section_title="Prerequisites",
            content=[
                {
                    "type": "text",
                    "content": "Ensure all the following prerequisites are met before beginning the migration:",
                },
                {"type": "list", "style": "bullet", "items": prerequisites},
            ],
        )

        time.sleep(1)
        logger.info("✓ Added prerequisites section with checklist")

        # AI adds migration steps
        logger.info("\n# Adding Migration Steps")
        steps = [
            {
                "step": "Preparation",
                "description": "Document current server configuration",
            },
            {"step": "Backup", "description": "Create full backup of source server"},
            {"step": "Installation", "description": "Set up target server environment"},
            {"step": "Migration", "description": "Transfer data and configurations"},
            {"step": "Validation", "description": "Verify migrated services"},
        ]

        editor.add_section(
            page_title=page_title,
            space_key=space_key,
            section_title="Migration Process",
            content=[
                {"type": "text", "content": "Follow these steps in order:"},
                {
                    "type": "table",
                    "headers": ["Step", "Description"],
                    "rows": [[step["step"], step["description"]] for step in steps],
                },
            ],
        )

        time.sleep(1)
        logger.info("✓ Added migration steps with detailed table")

        # AI adds code examples
        logger.info("\n# Adding Technical Examples")
        backup_script = """
#!/bin/bash
# Backup script for server migration
SOURCE_DIR="/var/www"
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d)

# Create backup
tar -czf $BACKUP_DIR/server_backup_$DATE.tar.gz $SOURCE_DIR

# Verify backup
if [ $? -eq 0 ]; then
    echo "Backup completed successfully"
else
    echo "Backup failed"
    exit 1
fi
"""

        editor.add_code_block(
            page_title=page_title,
            space_key=space_key,
            section="Migration Process",
            code=backup_script,
            language="bash",
            title="Example Backup Script",
        )

        time.sleep(1)
        logger.info("✓ Added technical examples with code blocks")

        # AI adds warning notices
        logger.info("\n# Adding Important Notices")
        editor.add_panel(
            page_title=page_title,
            space_key=space_key,
            section="Migration Process",
            content="Always verify your backup before proceeding with migration. Failed backups can result in data loss.",
            panel_type="warning",
            title="Critical Warning",
        )

        time.sleep(1)
        logger.info("✓ Added warning notices and important information")

        # AI adds validation checklist
        logger.info("\n# Adding Validation Checklist")
        validation_steps = [
            "Verify all services are running",
            "Check application logs for errors",
            "Validate data integrity",
            "Test all critical functionality",
            "Verify network connectivity",
            "Check SSL certificates",
            "Validate backup systems",
        ]

        editor.add_section(
            page_title=page_title,
            space_key=space_key,
            section_title="Post-Migration Validation",
            content=[
                {"type": "text", "content": "Complete the following validation steps:"},
                {"type": "list", "style": "numbered", "items": validation_steps},
                {
                    "type": "panel",
                    "title": "Validation Period",
                    "content": "Monitor the migrated server for at least 24 hours after migration.",
                    "panel_type": "note",
                },
            ],
        )

        time.sleep(1)
        logger.info("✓ Added validation checklist and monitoring instructions")

        # AI updates the status
        logger.info("\n# Finalizing Documentation")
        editor.update_status(
            page_title=page_title,
            space_key=space_key,
            status="Ready for Review",
            color="yellow",
        )

        logger.info("✓ Updated document status to 'Ready for Review'")

        # Final success message
        logger.info("\n" + "=" * 80)
        logger.info("## Test Completion Summary")
        logger.info("=" * 80)
        logger.info("✓ Successfully created comprehensive server migration guide")
        logger.info(
            f"✓ Document available at: {confluence.config.url}/wiki/spaces/{space_key}/pages/{page_title}"
        )
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Error in AI documentation test: {str(e)}")
        raise


if __name__ == "__main__":
    simulate_ai_documentation_tasks()
