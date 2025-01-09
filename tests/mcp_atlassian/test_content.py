import pytest
from mcp_atlassian.content import MarkupFormatter, ContentEditor, TemplateHandler
from unittest.mock import MagicMock


def test_heading():
    # Test valid heading levels
    assert MarkupFormatter.heading("Test Heading", 1) == "h1. Test Heading\n\n"
    assert MarkupFormatter.heading("Test Heading", 2) == "h2. Test Heading\n\n"
    assert MarkupFormatter.heading("Test Heading", 6) == "h6. Test Heading\n\n"

    # Test default level
    assert MarkupFormatter.heading("Test Heading") == "h1. Test Heading\n\n"

    # Test invalid heading level
    with pytest.raises(ValueError, match="Heading level must be between 1 and 6"):
        MarkupFormatter.heading("Test Heading", 0)
    with pytest.raises(ValueError, match="Heading level must be between 1 and 6"):
        MarkupFormatter.heading("Test Heading", 7)


def test_bullet_list():
    items = ["Item 1", "Item 2", "Item 3"]

    # Test default level
    expected = "* Item 1\n* Item 2\n* Item 3\n"
    assert MarkupFormatter.bullet_list(items) == expected

    # Test indented level
    expected_level2 = "  * Item 1\n  * Item 2\n  * Item 3\n"
    assert MarkupFormatter.bullet_list(items, 2) == expected_level2

    # Test empty list
    assert MarkupFormatter.bullet_list([]) == ""


def test_numbered_list():
    items = ["Item 1", "Item 2", "Item 3"]

    # Test default level
    expected = "# Item 1\n# Item 2\n# Item 3\n"
    assert MarkupFormatter.numbered_list(items) == expected

    # Test indented level
    expected_level2 = "  # Item 1\n  # Item 2\n  # Item 3\n"
    assert MarkupFormatter.numbered_list(items, 2) == expected_level2

    # Test empty list
    assert MarkupFormatter.numbered_list([]) == ""


def test_code_block():
    code = "def test():\n    pass"

    # Test without language
    expected = "{code}\ndef test():\n    pass\n{code}\n\n"
    assert MarkupFormatter.code_block(code) == expected

    # Test with language
    expected_python = "{code:python}\ndef test():\n    pass\n{code}\n\n"
    assert MarkupFormatter.code_block(code, "python") == expected_python


def test_table():
    headers = ["Name", "Age", "City"]
    rows = [["John", "30", "New York"], ["Jane", "25", "London"]]

    expected = "||Name||Age||City||\n|John|30|New York|\n|Jane|25|London|\n\n"
    assert MarkupFormatter.table(headers, rows) == expected

    # Test empty table
    assert MarkupFormatter.table([], []) == "||||\n\n"


def test_text_formatting():
    # Test quote
    assert MarkupFormatter.quote("Test quote") == "bq. Test quote\n\n"

    # Test link
    assert MarkupFormatter.link("Test", "http://test.com") == "[Test|http://test.com]"

    # Test bold
    assert MarkupFormatter.bold("Test") == "*Test*"

    # Test italic
    assert MarkupFormatter.italic("Test") == "_Test_"


def test_panel():
    content = "Test content"

    # Test default panel
    expected = "{panel:type=info}\nTest content\n{panel}\n\n"
    assert MarkupFormatter.panel(content) == expected

    # Test with title
    expected_title = "{panel:title=Test Title:type=info}\nTest content\n{panel}\n\n"
    assert MarkupFormatter.panel(content, "Test Title") == expected_title

    # Test different types
    assert "type=warning" in MarkupFormatter.panel(content, panel_type="warning")
    assert "type=note" in MarkupFormatter.panel(content, panel_type="note")

    # Test invalid type
    with pytest.raises(ValueError, match="Panel type must be one of:"):
        MarkupFormatter.panel(content, panel_type="invalid")


def test_status():
    # Test default color
    assert MarkupFormatter.status("Done") == "{status:colour=green|title=Done}\n\n"

    # Test different colors
    assert "colour=red" in MarkupFormatter.status("Failed", "red")
    assert "colour=yellow" in MarkupFormatter.status("Pending", "yellow")

    # Test invalid color
    with pytest.raises(ValueError, match="Color must be one of:"):
        MarkupFormatter.status("Test", "purple")


def test_expand():
    summary = "Click to expand"
    content = "Hidden content"
    expected = "{expand:summary=Click to expand}\nHidden content\n{expand}\n\n"
    assert MarkupFormatter.expand(summary, content) == expected


def test_task_list():
    tasks = [(True, "Completed task"), (False, "Pending task")]
    expected = "- [x] Completed task\n- [ ] Pending task\n"
    assert MarkupFormatter.task_list(tasks) == expected


def test_column_layout():
    columns = ["Column 1", "Column 2"]

    # Test without widths
    expected = "{section:border=true}\n{column}\nColumn 1\n{column}\n{column}\nColumn 2\n{column}\n{section}\n\n"
    assert MarkupFormatter.column_layout(columns) == expected

    # Test with widths
    widths = ["50%", "50%"]
    expected_widths = "{section:border=true}\n{column:width=50%}\nColumn 1\n{column}\n{column:width=50%}\nColumn 2\n{column}\n{section}\n\n"
    assert MarkupFormatter.column_layout(columns, widths) == expected_widths

    # Test mismatched widths
    with pytest.raises(
        ValueError, match="Number of widths must match number of columns"
    ):
        MarkupFormatter.column_layout(columns, ["50%"])


def test_highlight():
    # Test default color
    assert MarkupFormatter.highlight("Test") == "{color:yellow}Test{color}"

    # Test different colors
    assert "{color:red}" in MarkupFormatter.highlight("Test", "red")
    assert "{color:green}" in MarkupFormatter.highlight("Test", "green")

    # Test invalid color
    with pytest.raises(ValueError, match="Color must be one of:"):
        MarkupFormatter.highlight("Test", "purple")


def test_divider():
    assert MarkupFormatter.divider() == "----\n\n"


def test_find_section():
    content = """h1. First Section
Content of first section

h2. Subsection
Content of subsection

h1. Second Section
Content of second section"""

    # Test finding first section
    start, end = ContentEditor.find_section(content, "First Section")
    assert start != -1 and end != -1
    section_content = content[start:end].strip()
    assert "Content of first section" in section_content
    assert "Content of subsection" in section_content
    assert "Second Section" not in section_content

    # Test finding second section
    start, end = ContentEditor.find_section(content, "Second Section")
    assert start != -1 and end != -1
    section_content = content[start:end].strip()
    assert "Content of second section" in section_content
    assert "First Section" not in section_content

    # Test finding non-existent section
    start, end = ContentEditor.find_section(content, "Non-existent Section")
    assert start == -1 and end == -1


def test_insert_after_heading():
    content = """h1. Test Section
Existing content

h1. Next Section
More content"""

    new_content = "New content to insert"
    result = ContentEditor.insert_after_heading(content, "Test Section", new_content)

    assert "h1. Test Section" in result
    assert "Existing content" in result
    assert "New content to insert" in result
    assert result.index("New content to insert") > result.index("Existing content")
    assert "h1. Next Section" in result

    # Test inserting after non-existent heading
    result = ContentEditor.insert_after_heading(content, "Non-existent", new_content)
    assert result == content


def test_replace_section():
    content = """h1. First Section
Old content

h1. Second Section
More content"""

    new_content = "Updated content"
    result = ContentEditor.replace_section(content, "First Section", new_content)

    assert "h1. First Section" in result
    assert "Old content" not in result
    assert "Updated content" in result
    assert "h1. Second Section" in result
    assert "More content" in result

    # Test replacing non-existent section
    result = ContentEditor.replace_section(content, "Non-existent", new_content)
    assert result == content


def test_append_to_list():
    # Test bullet list
    content = """Some text
* Item 1
* Item 2
More text"""
    result = ContentEditor.append_to_list(content, "*", "Item 3")
    assert "* Item 1" in result
    assert "* Item 2" in result
    assert "* Item 3" in result
    assert result.index("* Item 3") > result.index("* Item 2")

    # Test numbered list
    content = """Some text
# First
# Second
More text"""
    result = ContentEditor.append_to_list(content, "#", "Third")
    assert "# First" in result
    assert "# Second" in result
    assert "# Third" in result
    assert result.index("# Third") > result.index("# Second")

    # Test with non-existent list
    result = ContentEditor.append_to_list("No list here", "*", "New item")
    assert result == "No list here"  # Should not modify content when no list exists


def test_update_table_row():
    content = """Some text
||Header 1||Header 2||
|Value 1|Value 2|
|Old 1|Old 2|
More text"""

    # Test updating existing row
    new_values = ["New 1", "New 2"]
    result = ContentEditor.update_table_row(
        content, "||Header 1||Header 2||", "Old 1", new_values
    )
    assert "|Value 1|Value 2|" in result
    assert "|Old 1|Old 2|" not in result
    assert "|New 1|New 2|" in result

    # Test with non-existent table
    result = ContentEditor.update_table_row(
        content, "||Wrong Header||", "Old 1", new_values
    )
    assert result == content

    # Test with non-existent row
    result = ContentEditor.update_table_row(
        content, "||Header 1||Header 2||", "Non-existent", new_values
    )
    assert result == content

    # Test with mismatched column count
    new_values = ["New 1", "New 2", "New 3"]  # Too many values
    result = ContentEditor.update_table_row(
        content, "||Header 1||Header 2||", "Old 1", new_values
    )
    assert result == content  # Should not modify content when column counts don't match


@pytest.fixture
def mock_confluence_client():
    return MagicMock()


@pytest.fixture
def mock_jira_client():
    return MagicMock()


def test_get_confluence_templates(mock_confluence_client):
    # Mock the response for blueprint templates
    mock_confluence_client.get_blueprint_templates.return_value = {
        "blueprints": [
            {
                "templateId": "blueprint-123",
                "name": "Meeting Notes",
                "description": "Template for meeting notes",
                "spaceKey": "TEAM",
            }
        ]
    }

    # Mock the response for custom templates
    mock_confluence_client.get_content.return_value = {
        "results": [
            {
                "id": "456",
                "title": "Project Template",
                "description": "Template for project pages",
                "type": "template",
                "space": {"key": "TEAM"},
                "body": {"storage": {"value": "Template content"}},
            }
        ]
    }

    templates = TemplateHandler.get_confluence_templates(mock_confluence_client)
    assert len(templates) == 2

    # Verify blueprint template
    blueprint = templates[0]
    assert blueprint["id"] == "blueprint-123"
    assert blueprint["name"] == "Meeting Notes"
    assert blueprint["type"] == "blueprint"
    assert blueprint["space_key"] == "TEAM"
    assert blueprint["content"] is None

    # Verify custom template
    custom = templates[1]
    assert custom["id"] == "456"
    assert custom["name"] == "Project Template"
    assert custom["type"] == "custom"
    assert custom["space_key"] == "TEAM"
    assert custom["content"] == "Template content"


def test_get_jira_templates(mock_jira_client):
    # Mock the response for issue type schemes
    mock_jira_client.issue_type_schemes.return_value = [{"id": "scheme1"}]

    # Mock the response for issue templates
    mock_jira_client.issue_templates.return_value = [
        {
            "id": "789",
            "name": "Bug Report",
            "description": "Template for bug reports",
            "projectKey": "PROJ",
            "issueType": {"name": "Bug"},
            "fields": {"priority": {"name": "High"}},
        }
    ]

    templates = TemplateHandler.get_jira_templates(mock_jira_client)
    assert len(templates) == 1

    template = templates[0]
    assert template["id"] == "789"
    assert template["name"] == "Bug Report"
    assert template["project_key"] == "PROJ"
    assert template["issue_type"] == "Bug"
    assert template["fields"] == {"priority": {"name": "High"}}


def test_apply_confluence_template(mock_confluence_client):
    # Test blueprint template
    mock_confluence_client.create_page_from_blueprint.return_value = {
        "body": {"storage": {"value": "Created from blueprint"}}
    }

    result = TemplateHandler.apply_confluence_template(
        mock_confluence_client,
        "blueprint-123",
        "TEAM",
        "New Page",
        {"variable": "value"},
    )
    assert result == "Created from blueprint"
    mock_confluence_client.create_page_from_blueprint.assert_called_once()

    # Test custom template
    mock_confluence_client.get_content_by_id.return_value = {
        "body": {"storage": {"value": "Template with ${variable}"}}
    }

    result = TemplateHandler.apply_confluence_template(
        mock_confluence_client,
        "456",
        "TEAM",
        "New Page",
        {"variable": "value"},
    )
    assert result == "Template with value"
    mock_confluence_client.get_content_by_id.assert_called_once()


def test_apply_jira_template(mock_jira_client):
    # Mock template response
    mock_jira_client.issue_template.return_value = {
        "fields": {
            "description": "Template with ${description}",
            "issuetype": {"name": "Bug"},
            "priority": {"name": "High"},
        }
    }

    result = TemplateHandler.apply_jira_template(
        mock_jira_client,
        "789",
        "PROJ",
        "Bug Summary",
        {"description": "Bug description"},
    )

    assert result is not None
    assert result["project"]["key"] == "PROJ"
    assert result["summary"] == "Bug Summary"
    assert "description" in result
    mock_jira_client.issue_template.assert_called_once_with("789")


def test_list_template_variables():
    # Test with multiple variables
    content = "This is a ${variable1} template with ${variable2} and ${another_var}"
    variables = TemplateHandler.list_template_variables(content)
    assert set(variables) == {"variable1", "variable2", "another_var"}

    # Test with repeated variables
    content = "This ${var} has ${var} repeated ${var} multiple times"
    variables = TemplateHandler.list_template_variables(content)
    assert len(variables) == 1
    assert variables[0] == "var"

    # Test with no variables
    content = "This template has no variables"
    variables = TemplateHandler.list_template_variables(content)
    assert variables == []


def test_template_error_handling(mock_confluence_client, mock_jira_client):
    # Test Confluence template errors
    mock_confluence_client.get_blueprint_templates.side_effect = Exception("API Error")
    templates = TemplateHandler.get_confluence_templates(mock_confluence_client)
    assert templates == []

    # Test Jira template errors
    mock_jira_client.issue_type_schemes.side_effect = Exception("API Error")
    templates = TemplateHandler.get_jira_templates(mock_jira_client)
    assert templates == []

    # Test template application errors
    mock_confluence_client.create_page_from_blueprint.side_effect = Exception(
        "API Error"
    )
    result = TemplateHandler.apply_confluence_template(
        mock_confluence_client, "blueprint-123", "TEAM", "New Page"
    )
    assert result is None

    mock_jira_client.issue_template.side_effect = Exception("API Error")
    result = TemplateHandler.apply_jira_template(
        mock_jira_client, "789", "PROJ", "Summary"
    )
    assert result is None
