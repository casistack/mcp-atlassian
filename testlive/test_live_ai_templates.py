import os
import sys
import time
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
        blueprints = template_handler.get_blueprint_templates(space_key)
        logger.info(f"✓ Found {len(blueprints)} blueprints")

        # Log blueprint structure
        if blueprints:
            logger.info("\n# Blueprint Structure Example:")
            logger.info(f"Blueprint Keys: {list(blueprints[0].keys())}")
            logger.info(f"First Blueprint: {blueprints[0]}")

        # Create page from blueprint
        logger.info("\n# Creating Page from Blueprint")
        if blueprints:
            blueprint = next(
                (
                    bp
                    for bp in blueprints
                    if "documentation" in str(bp.get("name", "")).lower()
                ),
                blueprints[0],
            )
            page_title = f"Blueprint Test {timestamp}"
            template_params = {
                "title": page_title,
                "description": "This page was created from a blueprint by AI",
                "owner": "AI Assistant",
            }

            # Use the correct key for blueprint ID
            blueprint_id = (
                blueprint.get("templateId")
                or blueprint.get("id")
                or blueprint.get("blueprintId")
            )
            if not blueprint_id:
                logger.error(f"Could not find blueprint ID in: {blueprint}")
                return

            page = template_handler.create_from_template(
                space_key, blueprint_id, page_title, template_params
            )
            logger.info(
                f"✓ Created page from blueprint: {blueprint.get('name', 'Unknown')}"
            )

            # Add custom sections to blueprint page
            logger.info("\n# Enhancing Blueprint with Custom Sections")
            editor.add_section(
                page_title,
                space_key,
                "AI Modifications",
                [
                    {
                        "type": "text",
                        "content": "This section demonstrates AI's ability to modify blueprint content.",
                    }
                ],
            )
            logger.info("✓ Added custom section to blueprint page")

            # Add dynamic content
            logger.info("\n# Adding Dynamic Content")

            # Add table
            editor.add_section(
                page_title,
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
                page_title,
                space_key,
                "Notes and Warnings",
                "This is an automatically generated warning by AI",
                "warning",
                "AI Warning",
            )
            logger.info("✓ Added warning panel")

            # Update status
            editor.update_status(page_title, space_key, "In Progress", "blue")
            logger.info("✓ Updated page status")

            logger.info("\n" + "=" * 80)
            logger.info("## Test Completion Summary")
            logger.info("=" * 80)
            logger.info("✓ Successfully tested blueprint operations")
            logger.info(
                f"✓ Test page available at: https://your-domain.atlassian.net/wiki/spaces/{space_key}/pages/{page_title}"
            )
            logger.info("=" * 80 + "\n")
        else:
            logger.warning("No blueprints found to test with")

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
        page = editor.create_page(space_key, page_title, initial_content)
        logger.info("✓ Created test page")
        time.sleep(2)  # Add delay between operations

        # Test nested lists
        logger.info("\n# Testing Nested Lists")
        nested_list_content = [
            {
                "type": "text",
                "content": '<ac:structured-macro ac:name="info"><ac:rich-text-body><ul>'
                + "<li>Main Item 1"
                + "<ul><li>Sub Item 1.1</li>"
                + "<li>Sub Item 1.2"
                + "<ul><li>Sub Sub Item 1.2.1</li></ul>"
                + "</li></ul></li>"
                + "<li>Main Item 2"
                + "<ul><li>Sub Item 2.1</li></ul>"
                + "</li></ul></ac:rich-text-body></ac:structured-macro>",
            }
        ]
        editor.add_section(
            page_title, space_key, "Nested Lists Example", nested_list_content
        )
        logger.info("✓ Added nested lists")
        time.sleep(2)  # Add delay between operations

        # Test code blocks with different languages
        logger.info("\n# Testing Code Blocks")
        code_content = [
            {
                "type": "text",
                "content": '<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">python</ac:parameter><ac:parameter ac:name="title">Python Example</ac:parameter><ac:plain-text-body><![CDATA[def example():\n    return "Hello World"]]></ac:plain-text-body></ac:structured-macro>',
            },
            {
                "type": "text",
                "content": '<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">javascript</ac:parameter><ac:parameter ac:name="title">JavaScript Example</ac:parameter><ac:plain-text-body><![CDATA[function example() {\n    return "Hello World";\n}]]></ac:plain-text-body></ac:structured-macro>',
            },
        ]
        editor.add_section(page_title, space_key, "Code Examples", code_content)
        logger.info("✓ Added code blocks in different languages")
        time.sleep(2)  # Add delay between operations

        # Test table with complex content
        logger.info("\n# Testing Complex Tables")
        complex_table_content = [
            {
                "type": "text",
                "content": '<ac:structured-macro ac:name="table-excerpt"><ac:rich-text-body>'
                + "<table><thead><tr>"
                + "<th>Feature</th><th>Description</th><th>Status</th><th>Notes</th>"
                + "</tr></thead><tbody>"
                + "<tr><td><strong>Authentication</strong></td><td>User authentication system</td>"
                + '<td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">green</ac:parameter><ac:parameter ac:name="title">Complete</ac:parameter></ac:structured-macro></td>'
                + "<td>Ready for production</td></tr>"
                + "<tr><td><strong>Authorization</strong></td><td>Role-based access control</td>"
                + '<td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">yellow</ac:parameter><ac:parameter ac:name="title">In Progress</ac:parameter></ac:structured-macro></td>'
                + "<td>Under review</td></tr>"
                + "</tbody></table></ac:rich-text-body></ac:structured-macro>",
            }
        ]
        editor.add_section(
            page_title, space_key, "Feature Status", complex_table_content
        )
        logger.info("✓ Added complex table with formatted content")
        time.sleep(2)  # Add delay between operations

        # Test expandable sections with rich content
        logger.info("\n# Testing Rich Expandable Sections")
        expandable_content = [
            {
                "type": "text",
                "content": '<ac:structured-macro ac:name="expand"><ac:parameter ac:name="title">Technical Details</ac:parameter><ac:rich-text-body>'
                + "<strong>Configuration Settings</strong><br/>"
                + "<ol><li>Authentication timeout: 30 minutes</li>"
                + "<li>Maximum retry attempts: 3</li>"
                + "<li>Password policy: Strong</li></ol>"
                + "</ac:rich-text-body></ac:structured-macro>",
            }
        ]
        editor.add_section(
            page_title, space_key, "Expandable Content", expandable_content
        )
        logger.info("✓ Added expandable section with rich content")
        time.sleep(2)  # Add delay between operations

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


def test_advanced_formatting():
    """Test AI's ability to work with advanced formatting features in Confluence."""
    editor = ContentEditor()
    space_key = "IS"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    page_title = f"Advanced Formatting Test {timestamp}"

    logger.info("\n" + "=" * 80)
    logger.info("## Advanced Formatting Test Suite")
    logger.info("=" * 80 + "\n")

    try:
        # Create initial page with all advanced formatting
        logger.info("# Creating Test Page with Advanced Formatting")
        content = [
            {"type": "status", "text": "Draft", "color": "grey"},
            {
                "type": "text",
                "content": (
                    # Header with advanced formatting
                    "<h1><strong><u>Advanced Formatting Capabilities</u></strong></h1>"
                    + '<ac:structured-macro ac:name="info">'
                    + '<ac:parameter ac:name="title">Document Purpose</ac:parameter>'
                    + "<ac:rich-text-body><em>This document demonstrates advanced formatting capabilities available to AI.</em></ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    +
                    # Advanced text formatting section
                    "<h2>Text Formatting Examples</h2>"
                    + "<strong><u>Combined Formatting Example:</u></strong><br/>"
                    + '<span style="text-decoration: line-through;"><strong><em><u>This text combines multiple styles</u></em></strong></span><br/>'
                    + '<span style="color: #ff0000;">Red text</span> and '
                    + '<span style="background-color: #ffff00;">highlighted text</span>'
                    +
                    # Advanced table with merged cells
                    "<h2>Advanced Table Example</h2>"
                    + '<ac:structured-macro ac:name="table-excerpt"><ac:rich-text-body>'
                    + "<table><thead><tr>"
                    + "<th>Category</th><th>Details</th><th>Status</th><th>Notes</th>"
                    + "</tr></thead><tbody>"
                    + '<tr><td rowspan="2"><strong>Feature Set 1</strong></td>'
                    + "<td>Basic Features</td>"
                    + '<td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">green</ac:parameter><ac:parameter ac:name="title">Complete</ac:parameter></ac:structured-macro></td>'
                    + "<td>Released</td></tr>"
                    + "<tr><td>Advanced Features</td>"
                    + '<td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">yellow</ac:parameter><ac:parameter ac:name="title">In Progress</ac:parameter></ac:structured-macro></td>'
                    + "<td>In Development</td></tr>"
                    + "</tbody></table></ac:rich-text-body></ac:structured-macro>"
                    +
                    # Custom panels section
                    "<h2>Information Panels</h2>"
                    + '<ac:structured-macro ac:name="info">'
                    + '<ac:parameter ac:name="title">Important Note</ac:parameter>'
                    + "<ac:rich-text-body>This is a standard note panel with structured macro</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    + '<ac:structured-macro ac:name="warning">'
                    + '<ac:parameter ac:name="title">Warning</ac:parameter>'
                    + "<ac:rich-text-body>This is a warning panel with custom formatting</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    + '<ac:structured-macro ac:name="tip">'
                    + '<ac:parameter ac:name="title">Success</ac:parameter>'
                    + '<ac:parameter ac:name="icon">true</ac:parameter>'
                    + "<ac:rich-text-body>Operation completed successfully</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    +
                    # Advanced macros section
                    "<h2>Advanced Macros</h2>"
                    + '<ac:structured-macro ac:name="toc">'
                    + '<ac:parameter ac:name="maxLevel">3</ac:parameter>'
                    + "</ac:structured-macro>"
                    + '<ac:structured-macro ac:name="info">'
                    + '<ac:parameter ac:name="title">Information Macro</ac:parameter>'
                    + '<ac:parameter ac:name="icon">true</ac:parameter>'
                    + "<ac:rich-text-body>This is an information macro with custom parameters</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    + '<ac:structured-macro ac:name="code">'
                    + '<ac:parameter ac:name="language">python</ac:parameter>'
                    + '<ac:parameter ac:name="title">Example Code</ac:parameter>'
                    + '<ac:parameter ac:name="lineNumbers">true</ac:parameter>'
                    + '<ac:parameter ac:name="collapse">true</ac:parameter>'
                    + '<ac:plain-text-body><![CDATA[def advanced_function():\n    print("Advanced formatting")]]></ac:plain-text-body>'
                    + "</ac:structured-macro>"
                    +
                    # Page layout with columns
                    "<h2>Page Layout</h2>"
                    + '<ac:layout><ac:layout-section ac:type="two_equal">'
                    + "<ac:layout-cell>"
                    + '<ac:structured-macro ac:name="info"><ac:rich-text-body>Left Column Content</ac:rich-text-body></ac:structured-macro>'
                    + "</ac:layout-cell>"
                    + "<ac:layout-cell>"
                    + '<ac:structured-macro ac:name="note"><ac:rich-text-body>Right Column Content</ac:rich-text-body></ac:structured-macro>'
                    + "</ac:layout-cell>"
                    + "</ac:layout-section></ac:layout>"
                ),
            },
        ]

        editor.create_page(space_key, page_title, content)
        logger.info("✓ Created page with advanced formatting")
        time.sleep(2)  # Add delay before status update

        # Update status
        editor.update_status(page_title, space_key, "Ready for Review", "green")
        logger.info("✓ Updated page status")

        logger.info("\n" + "=" * 80)
        logger.info("## Test Completion Summary")
        logger.info("=" * 80)
        logger.info("✓ Successfully tested advanced formatting features")
        logger.info(
            f"✓ Document available at: https://udawgy.atlassian.net/wiki/spaces/{space_key}/pages/{page_title}"
        )
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Error in advanced formatting test: {str(e)}")
        raise


if __name__ == "__main__":
    test_template_operations()
    test_advanced_content_types()
    test_advanced_formatting()
