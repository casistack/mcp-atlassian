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

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.content import ContentEditor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_professional_document_features():
    """Test AI's ability to create professional-looking documents with advanced features."""
    editor = ContentEditor()
    space_key = "IS"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    page_title = f"Professional Documentation {timestamp}"

    logger.info("\n" + "=" * 80)
    logger.info("## Professional Document Features Test Suite")
    logger.info("=" * 80 + "\n")

    try:
        # Create initial page with professional header
        logger.info("# Creating Professional Document")
        content = [
            {"type": "status", "text": "Draft", "color": "grey"},
            {
                "type": "text",
                "content": (
                    # Professional Header with Logo and Metadata
                    '<ac:layout><ac:layout-section ac:type="two_left_sidebar">'
                    + "<ac:layout-cell>"
                    + "<p><em>Company Logo</em></p>"
                    + "</ac:layout-cell>"
                    + "<ac:layout-cell>"
                    + "<h1>Professional Documentation Example</h1>"
                    + '<ac:structured-macro ac:name="details">'
                    + "<ac:rich-text-body>"
                    + "<table><tbody>"
                    + "<tr><th>Document Status:</th><td>Draft</td></tr>"
                    + "<tr><th>Last Updated:</th><td>"
                    + datetime.now().strftime("%Y-%m-%d")
                    + "</td></tr>"
                    + "<tr><th>Version:</th><td>1.0</td></tr>"
                    + "</tbody></table>"
                    + "</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    + "</ac:layout-cell>"
                    + "</ac:layout-section>"
                    +
                    # Table of Contents with Custom Styling
                    '<ac:structured-macro ac:name="toc">'
                    + '<ac:parameter ac:name="maxLevel">3</ac:parameter>'
                    + '<ac:parameter ac:name="minLevel">1</ac:parameter>'
                    + '<ac:parameter ac:name="style">disc</ac:parameter>'
                    + '<ac:parameter ac:name="class">rm-contents</ac:parameter>'
                    + "</ac:structured-macro>"
                    +
                    # Executive Summary Section
                    '<ac:layout><ac:layout-section ac:type="single">'
                    + "<ac:layout-cell>"
                    + '<ac:structured-macro ac:name="info">'
                    + '<ac:parameter ac:name="title">Executive Summary</ac:parameter>'
                    + "<ac:rich-text-body>"
                    + "This document demonstrates professional documentation capabilities with advanced formatting."
                    + "</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    + "</ac:layout-cell>"
                    + "</ac:layout-section>"
                    +
                    # Advanced Navigation Section
                    "<h2>Document Navigation</h2>"
                    + '<ac:structured-macro ac:name="children">'
                    + '<ac:parameter ac:name="style">h4</ac:parameter>'
                    + '<ac:parameter ac:name="sort">title</ac:parameter>'
                    + "</ac:structured-macro>"
                    +
                    # Rich Media Section
                    "<h2>Rich Media Integration</h2>"
                    + '<ac:layout><ac:layout-section ac:type="three_with_sidebars">'
                    + "<ac:layout-cell>"
                    + "<p><em>System Architecture Diagram</em></p>"
                    + "</ac:layout-cell>"
                    + "<ac:layout-cell>"
                    + "<p><em>Interactive Diagram</em></p>"
                    + "</ac:layout-cell>"
                    + "<ac:layout-cell>"
                    + "<p><em>External Content</em></p>"
                    + "</ac:layout-cell>"
                    + "</ac:layout-section>"
                    +
                    # Advanced Table Formatting
                    "<h2>Feature Comparison</h2>"
                    + '<table class="wrapped"><colgroup><col/><col/><col/><col/></colgroup>'
                    + "<thead><tr>"
                    + "<th>Feature</th><th>Basic</th><th>Pro</th><th>Enterprise</th>"
                    + "</tr></thead><tbody>"
                    + "<tr><td><strong>Feature 1</strong></td><td>✓</td><td>✓</td><td>✓</td></tr>"
                    + "<tr><td><strong>Feature 2</strong></td><td>-</td><td>✓</td><td>✓</td></tr>"
                    + "<tr><td><strong>Feature 3</strong></td><td>-</td><td>-</td><td>✓</td></tr>"
                    + "</tbody></table>"
                    +
                    # Interactive Elements
                    "<h2>Interactive Elements</h2>"
                    + '<ac:structured-macro ac:name="expand">'
                    + '<ac:parameter ac:name="title">Click to view implementation details</ac:parameter>'
                    + "<ac:rich-text-body>"
                    + '<ac:structured-macro ac:name="code">'
                    + '<ac:parameter ac:name="language">python</ac:parameter>'
                    + '<ac:parameter ac:name="theme">Darkula</ac:parameter>'
                    + '<ac:parameter ac:name="linenumbers">true</ac:parameter>'
                    + '<ac:plain-text-body><![CDATA[def example():\n    """Advanced implementation example."""\n    return True]]></ac:plain-text-body>'
                    + "</ac:structured-macro>"
                    + "</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    +
                    # Tabbed Content
                    '<ac:structured-macro ac:name="tabs">'
                    + '<ac:parameter ac:name="selectedTab">1</ac:parameter>'
                    + "<ac:rich-text-body>"
                    + '<ac:structured-macro ac:name="tab">'
                    + '<ac:parameter ac:name="title">Overview</ac:parameter>'
                    + "<ac:rich-text-body>Tab 1 content</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    + '<ac:structured-macro ac:name="tab">'
                    + '<ac:parameter ac:name="title">Details</ac:parameter>'
                    + "<ac:rich-text-body>Tab 2 content</ac:rich-text-body>"
                    + "</ac:structured-macro>"
                    + "</ac:structured-macro>"
                    +
                    # Advanced Status Section
                    "<h2>Implementation Status</h2>"
                    + '<table class="wrapped"><colgroup><col/><col/></colgroup>'
                    + "<tbody>"
                    + '<tr><td>Phase 1</td><td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">green</ac:parameter><ac:parameter ac:name="title">Complete</ac:parameter></ac:structured-macro></td></tr>'
                    + '<tr><td>Phase 2</td><td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">yellow</ac:parameter><ac:parameter ac:name="title">In Progress</ac:parameter></ac:structured-macro></td></tr>'
                    + "</tbody></table>"
                    +
                    # Jira Integration Section
                    "<h2>Related Issues</h2>"
                    + '<ac:structured-macro ac:name="jira">'
                    + '<ac:parameter ac:name="columns">key,summary,status,created,updated,due,assignee</ac:parameter>'
                    + '<ac:parameter ac:name="maximumIssues">10</ac:parameter>'
                    + '<ac:parameter ac:name="jqlQuery">project = DEMO AND status != Closed ORDER BY priority DESC</ac:parameter>'
                    + "</ac:structured-macro>"
                    +
                    # Roadmap Section
                    "<h2>Project Roadmap</h2>"
                    + '<ac:structured-macro ac:name="jira">'
                    + '<ac:parameter ac:name="columns">key,summary,duedate</ac:parameter>'
                    + '<ac:parameter ac:name="maximumIssues">5</ac:parameter>'
                    + '<ac:parameter ac:name="jqlQuery">project = DEMO AND issuetype = Epic ORDER BY duedate ASC</ac:parameter>'
                    + "</ac:structured-macro>"
                    +
                    # Footer with References
                    "<hr/>"
                    + "<p><small>"
                    + "Last updated: "
                    + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    + "<br/>"
                    + "Document ID: DOC-"
                    + timestamp
                    + "<br/>"
                    + 'Related Jira Project: <a href="https://your-domain.atlassian.net/browse/DEMO">DEMO</a>'
                    + "</small></p>"
                ),
            },
        ]

        editor.create_page(space_key, page_title, content)
        logger.info("✓ Created professional document with advanced formatting")
        time.sleep(2)  # Add delay before status update

        # Update status
        editor.update_status(page_title, space_key, "Ready for Review", "green")
        logger.info("✓ Updated page status")

        logger.info("\n" + "=" * 80)
        logger.info("## Test Completion Summary")
        logger.info("=" * 80)
        logger.info("✓ Successfully tested professional document features")
        logger.info(
            f"✓ Document available at: https://udawgy.atlassian.net/wiki/spaces/{space_key}/pages/{page_title}"
        )
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Error in professional document test: {str(e)}")
        raise


if __name__ == "__main__":
    test_professional_document_features()
