import pytest
from mcp_atlassian.content import MarkupFormatter, ContentEditor, TemplateHandler


class TestMarkupFormatter:
    def test_heading(self):
        # Test valid heading levels
        assert MarkupFormatter.heading("Test", 1) == "h1. Test\n\n"
        assert MarkupFormatter.heading("Test", 2) == "h2. Test\n\n"
        assert MarkupFormatter.heading("Test", 6) == "h6. Test\n\n"

        # Test default level
        assert MarkupFormatter.heading("Test") == "h1. Test\n\n"

        # Test invalid heading level
        with pytest.raises(ValueError, match="Heading level must be between 1 and 6"):
            MarkupFormatter.heading("Test", 0)
        with pytest.raises(ValueError, match="Heading level must be between 1 and 6"):
            MarkupFormatter.heading("Test", 7)

    def test_bullet_list(self):
        items = ["Item 1", "Item 2", "Item 3"]
        # Test default level
        expected = "* Item 1\n* Item 2\n* Item 3\n"
        assert MarkupFormatter.bullet_list(items) == expected

        # Test indented level
        expected_level2 = "  * Item 1\n  * Item 2\n  * Item 3\n"
        assert MarkupFormatter.bullet_list(items, level=2) == expected_level2

    def test_numbered_list(self):
        items = ["Item 1", "Item 2", "Item 3"]
        # Test default level
        expected = "# Item 1\n# Item 2\n# Item 3\n"
        assert MarkupFormatter.numbered_list(items) == expected

        # Test indented level
        expected_level2 = "  # Item 1\n  # Item 2\n  # Item 3\n"
        assert MarkupFormatter.numbered_list(items, level=2) == expected_level2

    def test_code_block(self):
        # Test without language
        code = "def test():\n    pass"
        expected = "{code}\ndef test():\n    pass\n{code}\n\n"
        assert MarkupFormatter.code_block(code) == expected

        # Test with language
        expected_python = "{code:python}\ndef test():\n    pass\n{code}\n\n"
        assert MarkupFormatter.code_block(code, "python") == expected_python

    def test_table(self):
        headers = ["Name", "Age"]
        rows = [["John", "30"], ["Jane", "25"]]
        expected = "||Name||Age||\n|John|30|\n|Jane|25|\n\n"
        assert MarkupFormatter.table(headers, rows) == expected

    def test_quote(self):
        text = "This is a quote"
        expected = "bq. This is a quote\n\n"
        assert MarkupFormatter.quote(text) == expected

    def test_link(self):
        text = "Click here"
        url = "https://example.com"
        expected = "[Click here|https://example.com]"
        assert MarkupFormatter.link(text, url) == expected

    def test_bold(self):
        text = "bold text"
        expected = "*bold text*"
        assert MarkupFormatter.bold(text) == expected

    def test_italic(self):
        text = "italic text"
        expected = "_italic text_"
        assert MarkupFormatter.italic(text) == expected

    def test_panel(self):
        # Test default panel
        content = "Panel content"
        expected = "{panel:type=info}\nPanel content\n{panel}\n\n"
        assert MarkupFormatter.panel(content) == expected

        # Test with title
        expected_with_title = (
            "{panel:title=Test Title:type=info}\nPanel content\n{panel}\n\n"
        )
        assert MarkupFormatter.panel(content, title="Test Title") == expected_with_title

        # Test with different panel type
        expected_warning = "{panel:type=warning}\nPanel content\n{panel}\n\n"
        assert MarkupFormatter.panel(content, panel_type="warning") == expected_warning

        # Test invalid panel type
        with pytest.raises(ValueError):
            MarkupFormatter.panel(content, panel_type="invalid")

    def test_status(self):
        # Test default color
        text = "Done"
        expected = "{status:colour=green|title=Done}\n\n"
        assert MarkupFormatter.status(text) == expected

        # Test with different colors
        assert (
            MarkupFormatter.status(text, "red") == "{status:colour=red|title=Done}\n\n"
        )
        assert (
            MarkupFormatter.status(text, "yellow")
            == "{status:colour=yellow|title=Done}\n\n"
        )
        assert (
            MarkupFormatter.status(text, "blue")
            == "{status:colour=blue|title=Done}\n\n"
        )

        # Test invalid color
        with pytest.raises(ValueError):
            MarkupFormatter.status(text, "invalid")

    def test_expand(self):
        summary = "Click to expand"
        content = "Hidden content"
        expected = "{expand:summary=Click to expand}\nHidden content\n{expand}\n\n"
        assert MarkupFormatter.expand(summary, content) == expected

    def test_code_inline(self):
        code = "print('hello')"
        expected = "{{code}}print('hello'){{code}}"
        assert MarkupFormatter.code_inline(code) == expected

    def test_table_of_contents(self):
        # Test default levels
        expected = "{toc:minLevel=1|maxLevel=6}\n\n"
        assert MarkupFormatter.table_of_contents() == expected

        # Test custom levels
        expected_custom = "{toc:minLevel=2|maxLevel=4}\n\n"
        assert MarkupFormatter.table_of_contents(2, 4) == expected_custom

    def test_info_macro(self):
        title = "Info Title"
        content = "Info content"
        expected = "{info:title=Info Title}\nInfo content\n{info}\n\n"
        assert MarkupFormatter.info_macro(title, content) == expected

    def test_note_macro(self):
        title = "Note Title"
        content = "Note content"
        expected = "{note:title=Note Title}\nNote content\n{note}\n\n"
        assert MarkupFormatter.note_macro(title, content) == expected

    def test_warning_macro(self):
        title = "Warning Title"
        content = "Warning content"
        expected = "{warning:title=Warning Title}\nWarning content\n{warning}\n\n"
        assert MarkupFormatter.warning_macro(title, content) == expected

    def test_tip_macro(self):
        title = "Tip Title"
        content = "Tip content"
        expected = "{tip:title=Tip Title}\nTip content\n{tip}\n\n"
        assert MarkupFormatter.tip_macro(title, content) == expected

    def test_task_list(self):
        items = [(True, "Completed task"), (False, "Pending task")]
        expected = "- [x] Completed task\n- [ ] Pending task\n"
        assert MarkupFormatter.task_list(items) == expected

    def test_column_layout(self):
        columns = ["Left content", "Right content"]
        # Test without widths
        expected = "{section:border=true}\n{column}\nLeft content\n{column}\n{column}\nRight content\n{column}\n{section}\n\n"
        assert MarkupFormatter.column_layout(columns) == expected

        # Test with widths
        widths = ["30%", "70%"]
        expected_with_widths = "{section:border=true}\n{column:width=30%}\nLeft content\n{column}\n{column:width=70%}\nRight content\n{column}\n{section}\n\n"
        assert MarkupFormatter.column_layout(columns, widths) == expected_with_widths

    def test_details(self):
        content = "Hidden details"
        # Test default indent
        expected = "{details}\nHidden details\n{details}\n\n"
        assert MarkupFormatter.details(content) == expected

        # Test with indent
        expected_indented = "  {details}\n  Hidden details\n  {details}\n\n"
        assert MarkupFormatter.details(content, indent_level=1) == expected_indented

    def test_highlight(self):
        text = "Important text"
        # Test default color
        expected = "{color:yellow}Important text{color}"
        assert MarkupFormatter.highlight(text) == expected

        # Test custom color
        expected_custom = "{color:red}Important text{color}"
        assert MarkupFormatter.highlight(text, "red") == expected_custom

    def test_divider(self):
        expected = "----\n\n"
        assert MarkupFormatter.divider() == expected

    def test_column_layout_invalid_widths(self):
        columns = ["Left content", "Right content"]
        widths = ["30%"]  # Only one width for two columns
        with pytest.raises(
            ValueError, match="Number of widths must match number of columns"
        ):
            MarkupFormatter.column_layout(columns, widths)

    def test_highlight_invalid_color(self):
        text = "Important text"
        with pytest.raises(ValueError) as exc_info:
            MarkupFormatter.highlight(text, "purple")

        # Check that the error message contains all valid colors
        error_msg = str(exc_info.value)
        assert "Color must be one of:" in error_msg
        assert "yellow" in error_msg
        assert "red" in error_msg
        assert "green" in error_msg
        assert "blue" in error_msg


class TestContentEditor:
    def test_find_section(self):
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

        # Test finding non-existent section
        start, end = ContentEditor.find_section(content, "Non-existent Section")
        assert start == -1 and end == -1

    def test_insert_after_heading(self):
        content = """h1. Test Section
Existing content

h1. Next Section
More content"""

        new_content = "New content to insert"
        result = ContentEditor.insert_after_heading(
            content, "Test Section", new_content
        )

        assert "h1. Test Section" in result
        assert "Existing content" in result
        assert "New content to insert" in result
        assert result.index("New content to insert") > result.index("Existing content")
        assert "h1. Next Section" in result

        # Test inserting after non-existent heading
        result = ContentEditor.insert_after_heading(
            content, "Non-existent", new_content
        )
        assert result == content

    def test_replace_section(self):
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

    def test_append_to_list(self):
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
        assert result == "No list here"

    def test_update_table_row(self):
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


class TestTemplateHandler:
    def test_get_confluence_templates(self, mock_confluence_client):
        # Mock the response for blueprint templates
        mock_confluence_client.get_blueprint_templates.return_value = {
            "blueprints": [
                {
                    "templateId": "123",
                    "name": "Template 1",
                    "description": "Blueprint template",
                    "spaceKey": "SPACE",
                }
            ]
        }

        # Mock the response for custom templates
        mock_confluence_client.get_content.return_value = {
            "results": [
                {
                    "id": "456",
                    "title": "Template 2",
                    "description": "Custom template",
                    "type": "template",
                    "space": {"key": "SPACE"},
                    "body": {"storage": {"value": "Template content"}},
                }
            ]
        }

        templates = TemplateHandler.get_confluence_templates(mock_confluence_client)
        assert len(templates) == 2

        # Check blueprint template
        assert templates[0]["id"] == "123"
        assert templates[0]["name"] == "Template 1"
        assert templates[0]["type"] == "blueprint"
        assert templates[0]["content"] is None

        # Check custom template
        assert templates[1]["id"] == "456"
        assert templates[1]["name"] == "Template 2"
        assert templates[1]["type"] == "custom"
        assert templates[1]["content"] == "Template content"

        # Verify the correct API calls were made
        mock_confluence_client.get_blueprint_templates.assert_called_once()
        mock_confluence_client.get_content.assert_called_once_with(
            type="template", expand="body.storage,version,space"
        )

    def test_get_jira_templates(self, mock_jira_client):
        # Mock the response for issue type schemes
        mock_jira_client.issue_type_schemes.return_value = [{"id": "scheme1"}]

        # Mock the response for issue templates
        mock_jira_client.issue_templates.return_value = [
            {
                "id": "789",
                "name": "Bug Template",
                "description": "Template for bug reports",
                "projectKey": "PROJ1",
                "issueType": {"name": "Bug"},
                "fields": {"field1": "value1"},
            }
        ]

        templates = TemplateHandler.get_jira_templates(mock_jira_client)
        assert len(templates) == 1
        assert templates[0]["id"] == "789"
        assert templates[0]["name"] == "Bug Template"
        assert templates[0]["project_key"] == "PROJ1"
        assert templates[0]["issue_type"] == "Bug"
        assert templates[0]["fields"] == {"field1": "value1"}

        # Verify the correct API calls were made
        mock_jira_client.issue_type_schemes.assert_called_once()
        mock_jira_client.issue_templates.assert_called_once_with("scheme1")

    def test_apply_confluence_template(self, mock_confluence_client):
        template_id = "123"
        space_key = "SPACE"
        title = "New Page"
        template_parameters = {"var1": "value1", "var2": "value2"}

        # Mock the response for template content
        mock_confluence_client.get_content_by_id.return_value = {
            "body": {"storage": {"value": "Template with ${var1} and ${var2}"}}
        }

        # Mock the response for creating content
        mock_confluence_client.create_content.return_value = {
            "id": "new-page-id",
            "type": "page",
            "title": title,
            "space": {"key": space_key},
        }

        result = TemplateHandler.apply_confluence_template(
            mock_confluence_client, template_id, space_key, title, template_parameters
        )

        assert result is not None
        assert isinstance(result, str)
        assert "value1" in result
        assert "value2" in result

        # Test with missing template
        mock_confluence_client.get_content_by_id.side_effect = Exception("Not found")
        result = TemplateHandler.apply_confluence_template(
            mock_confluence_client, template_id, space_key, title, template_parameters
        )
        assert result is None

    def test_apply_jira_template(self, mock_jira_client):
        template_id = "789"
        project_key = "PROJ"
        summary = "New Issue"
        template_parameters = {"field1": "value1", "field2": "value2"}

        # Mock the response for template content
        mock_jira_client.issue_template.return_value = {
            "fields": {
                "description": "Template with ${field1} and ${field2}",
                "issuetype": {"name": "Bug"},
                "project": {"key": project_key},
            }
        }

        result = TemplateHandler.apply_jira_template(
            mock_jira_client, template_id, project_key, summary, template_parameters
        )

        assert result is not None
        assert isinstance(result, dict)
        assert result["project"]["key"] == project_key
        assert result["summary"] == summary
        mock_jira_client.issue_template.assert_called_once_with(template_id)

        # Test with missing template
        mock_jira_client.issue_template.side_effect = Exception("Not found")
        result = TemplateHandler.apply_jira_template(
            mock_jira_client, template_id, project_key, summary, template_parameters
        )
        assert result is None

    def test_list_template_variables(self):
        # Test with multiple variables
        content = "This is a ${variable1} template with ${variable2} and ${another_var}"
        variables = TemplateHandler.list_template_variables(content)
        assert set(variables) == {"variable1", "variable2", "another_var"}

        # Test with repeated variables
        content = "This ${var} has ${var} repeated ${var} multiple times"
        variables = TemplateHandler.list_template_variables(content)
        assert variables == ["var"]

        # Test with no variables
        content = "This template has no variables"
        variables = TemplateHandler.list_template_variables(content)
        assert variables == []

        # Test with empty content
        variables = TemplateHandler.list_template_variables("")
        assert variables == []

    def test_get_confluence_templates_error(self, mock_confluence_client):
        # Test API error handling
        mock_confluence_client.get_blueprint_templates.side_effect = Exception(
            "API Error"
        )
        templates = TemplateHandler.get_confluence_templates(mock_confluence_client)
        assert templates == []

        # Test malformed response handling
        mock_confluence_client.get_blueprint_templates.side_effect = None
        mock_confluence_client.get_blueprint_templates.return_value = (
            {}
        )  # Missing blueprints key
        mock_confluence_client.get_content.return_value = {}  # Missing results key
        templates = TemplateHandler.get_confluence_templates(mock_confluence_client)
        assert templates == []

    def test_get_jira_templates_error(self, mock_jira_client):
        # Test API error handling
        mock_jira_client.issue_type_schemes.side_effect = Exception("API Error")
        templates = TemplateHandler.get_jira_templates(mock_jira_client)
        assert templates == []

        # Test malformed response handling
        mock_jira_client.issue_type_schemes.side_effect = None
        mock_jira_client.issue_type_schemes.return_value = [{"id": "scheme1"}]
        mock_jira_client.issue_templates.side_effect = Exception("Template API Error")
        templates = TemplateHandler.get_jira_templates(mock_jira_client)
        assert templates == []

    def test_apply_confluence_template_blueprint(self, mock_confluence_client):
        template_id = "blueprint-123"
        space_key = "SPACE"
        title = "New Page"
        template_parameters = {"var1": "value1", "var2": "value2"}

        # Mock the response for blueprint template
        mock_confluence_client.create_page_from_blueprint.return_value = {
            "body": {"storage": {"value": "Blueprint content with var1 and var2"}}
        }

        result = TemplateHandler.apply_confluence_template(
            mock_confluence_client, template_id, space_key, title, template_parameters
        )

        assert result == "Blueprint content with var1 and var2"
        mock_confluence_client.create_page_from_blueprint.assert_called_once_with(
            space=space_key,
            title=title,
            blueprint_id=template_id,
            template_parameters=template_parameters,
        )

        # Test with empty template parameters
        result = TemplateHandler.apply_confluence_template(
            mock_confluence_client, template_id, space_key, title
        )
        assert result == "Blueprint content with var1 and var2"
        mock_confluence_client.create_page_from_blueprint.assert_called_with(
            space=space_key,
            title=title,
            blueprint_id=template_id,
            template_parameters={},
        )

        # Test error handling
        mock_confluence_client.create_page_from_blueprint.side_effect = Exception(
            "Blueprint Error"
        )
        result = TemplateHandler.apply_confluence_template(
            mock_confluence_client, template_id, space_key, title, template_parameters
        )
        assert result is None
