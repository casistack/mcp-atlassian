import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Set testing environment
os.environ["TESTING"] = "1"

# Import directly from content module
from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import ContentEditor, TemplateHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_template_operations():
    """Test AI's ability to work with Confluence templates."""
    editor = ContentEditor()
    template_handler = TemplateHandler()
    space_key = "IS"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    logger.info("\n" + "=" * 80)
    logger.info("## AI Template Operations Test Suite")
    logger.info("=" * 80 + "\n")

    try:
        # List available templates
        logger.info("# Fetching Available Templates")
        templates = template_handler.get_content_templates(space_key)
        blueprints = template_handler.get_blueprint_templates(space_key)
        logger.info(
            f"✓ Found {len(templates)} content templates and {len(blueprints)} blueprints"
        )

        # Create page from template
        logger.info("\n# Creating Page from Template")
        if templates:
            template_id = templates[0]["id"]
            page_title = f"Template Test {timestamp}"
            template_params = {
                "title": page_title,
                "description": "This page was created from a template by AI",
                "owner": "AI Assistant",
            }
            page = template_handler.create_from_template(
                space_key, template_id, page_title, template_params
            )
            logger.info("✓ Created page from template")

            # Add custom sections to templated page
            logger.info("\n# Enhancing Template with Custom Sections")
            editor.add_section(
                page_title,
                space_key,
                "AI Modifications",
                [
                    {
                        "type": "text",
                        "content": "This section demonstrates AI's ability to modify templated content.",
                    }
                ],
            )
            logger.info("✓ Added custom section to templated page")

        # Create and test a new template
        logger.info("\n# Creating New Template")
        new_template_name = f"AI Test Template {timestamp}"
        template_body = {
            "value": """
<h1>Project Documentation Template</h1>
<ac:structured-macro ac:name="status"/>

<h2>Overview</h2>
<p>$project_description$</p>

<h2>Technical Details</h2>
<ac:structured-macro ac:name="code">
    <ac:parameter ac:name="language">python</ac:parameter>
    <ac:plain-text-body><![CDATA[$code_example$]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Implementation Steps</h2>
<ac:structured-macro ac:name="table-excerpt"/>

<h2>Notes and Warnings</h2>
<ac:structured-macro ac:name="warning"/>
""",
            "representation": "storage",
        }

        new_template = template_handler.create_or_update_template(
            name=new_template_name,
            body=template_body,
            template_type="page",
            description="Template created by AI for testing",
            space=space_key,
        )
        logger.info("✓ Created new template")

        # Test using the new template
        logger.info("\n# Testing New Template")
        test_page_title = f"AI Template Test Page {timestamp}"
        template_params = {
            "project_description": "This is a test project created by AI",
            "code_example": "def hello_world():\n    print('Hello from AI')",
        }
        page = template_handler.create_from_template(
            space_key, new_template["id"], test_page_title, template_params
        )
        logger.info("✓ Created page from new template")

        # Add dynamic content to templated page
        logger.info("\n# Adding Dynamic Content")

        # Add table
        editor.add_section(
            test_page_title,
            space_key,
            "Implementation Progress",
            [
                {
                    "type": "table",
                    "headers": ["Step", "Status", "Notes"],
                    "rows": [
                        ["Setup", "Complete", "Initial setup done"],
                        ["Configuration", "In Progress", "Pending review"],
                        ["Testing", "Not Started", "Scheduled for next week"],
                    ],
                }
            ],
        )
        logger.info("✓ Added implementation progress table")

        # Add warning panel
        editor.add_panel(
            test_page_title,
            space_key,
            "Notes and Warnings",
            "This is an automatically generated warning by AI",
            "warning",
            "AI Warning",
        )
        logger.info("✓ Added warning panel")

        # Update status
        editor.update_status(test_page_title, space_key, "In Progress", "blue")
        logger.info("✓ Updated page status")

        # Cleanup
        logger.info("\n# Cleanup")
        template_handler.remove_template(new_template["id"])
        logger.info("✓ Removed test template")

        logger.info("\n" + "=" * 80)
        logger.info("## Test Completion Summary")
        logger.info("=" * 80)
        logger.info("✓ Successfully tested template operations")
        logger.info(
            f"✓ Test page available at: https://udawgy.atlassian.net/wiki/spaces/{space_key}/pages/{test_page_title}"
        )
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Error in template operations test: {str(e)}")
        raise


def test_advanced_content_types():
    """Test AI's ability to work with advanced content types."""
    editor = ContentEditor()
    space_key = "IS"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    page_title = f"Advanced Content Test {timestamp}"

    logger.info("\n" + "=" * 80)
    logger.info("## Advanced Content Types Test Suite")
    logger.info("=" * 80 + "\n")

    try:
        # Create initial page
        logger.info("# Creating Test Page")
        initial_content = [
            {"type": "status", "text": "Draft", "color": "grey"},
            {
                "type": "text",
                "content": "This page demonstrates advanced content handling capabilities.",
            },
        ]
        editor.create_page(space_key, page_title, initial_content)
        logger.info("✓ Created test page")

        # Test nested lists
        logger.info("\n# Testing Nested Lists")
        nested_list_content = [
            {
                "type": "list",
                "style": "bullet",
                "items": [
                    "Main Item 1",
                    "  - Sub Item 1.1",
                    "  - Sub Item 1.2",
                    "    * Sub Sub Item 1.2.1",
                    "Main Item 2",
                    "  - Sub Item 2.1",
                ],
            }
        ]
        editor.add_section(
            page_title, space_key, "Nested Lists Example", nested_list_content
        )
        logger.info("✓ Added nested lists")

        # Test code blocks with different languages
        logger.info("\n# Testing Code Blocks")
        editor.add_section(page_title, space_key, "Code Examples", [])
        editor.add_code_block(
            page_title,
            space_key,
            "Code Examples",
            "def example():\n    return 'Hello World'",
            "python",
            "Python Example",
        )
        editor.add_code_block(
            page_title,
            space_key,
            "Code Examples",
            "function example() {\n    return 'Hello World';\n}",
            "javascript",
            "JavaScript Example",
        )
        logger.info("✓ Added code blocks in different languages")

        # Test table with complex content
        logger.info("\n# Testing Complex Tables")
        complex_table_content = [
            {
                "type": "table",
                "headers": ["Feature", "Description", "Status", "Notes"],
                "rows": [
                    [
                        editor.format_text("Authentication", ["bold"]),
                        "User authentication system",
                        '<ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">green</ac:parameter><ac:parameter ac:name="title">Complete</ac:parameter></ac:structured-macro>',
                        "Ready for production",
                    ],
                    [
                        editor.format_text("Authorization", ["bold"]),
                        "Role-based access control",
                        '<ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">yellow</ac:parameter><ac:parameter ac:name="title">In Progress</ac:parameter></ac:structured-macro>',
                        "Under review",
                    ],
                ],
            }
        ]
        editor.add_section(
            page_title, space_key, "Feature Status", complex_table_content
        )
        logger.info("✓ Added complex table with formatted content")

        # Test expandable sections with rich content
        logger.info("\n# Testing Rich Expandable Sections")
        editor.add_expandable_section(
            page_title,
            space_key,
            "Feature Status",
            "Technical Details",
            editor.format_text("Configuration Settings", ["bold"])
            + "\n"
            + "1. Authentication timeout: 30 minutes\n"
            + "2. Maximum retry attempts: 3\n"
            + "3. Password policy: Strong",
        )
        logger.info("✓ Added expandable section with rich content")

        # Update status to complete
        editor.update_status(page_title, space_key, "Ready for Review", "blue")
        logger.info("\n✓ Updated page status")

        logger.info("\n" + "=" * 80)
        logger.info("## Test Completion Summary")
        logger.info("=" * 80)
        logger.info("✓ Successfully tested advanced content types")
        logger.info(
            f"✓ Document available at: https://udawgy.atlassian.net/wiki/spaces/{space_key}/pages/{page_title}"
        )
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Error in advanced content test: {str(e)}")
        raise


if __name__ == "__main__":
    test_template_operations()
    test_advanced_content_types()
