from typing import List, Optional, Tuple
import logging

# Configure logging
logger = logging.getLogger("mcp-atlassian")


class MarkupFormatter:
    """Utility class for formatting Confluence and Jira markup."""

    @staticmethod
    def heading(text: str, level: int = 1) -> str:
        """Create a heading of specified level (1-6)."""
        if not 1 <= level <= 6:
            raise ValueError("Heading level must be between 1 and 6")
        return f"h{level}. {text}\n\n"

    @staticmethod
    def bullet_list(items: list[str], level: int = 1) -> str:
        """Create a bullet list at specified indent level."""
        indent = "  " * (level - 1)
        return "".join(f"{indent}* {item}\n" for item in items)

    @staticmethod
    def numbered_list(items: list[str], level: int = 1) -> str:
        """Create a numbered list at specified indent level."""
        indent = "  " * (level - 1)
        return "".join(f"{indent}# {item}\n" for item in items)

    @staticmethod
    def code_block(code: str, language: str = "") -> str:
        """Create a code block with optional language specification."""
        lang_spec = f":{language}" if language else ""
        return f"{{code{lang_spec}}}\n{code}\n{{code}}\n\n"

    @staticmethod
    def table(headers: list[str], rows: list[list[str]]) -> str:
        """Create a table with headers and rows."""
        table = "||" + "||".join(headers) + "||\n"
        for row in rows:
            table += "|" + "|".join(row) + "|\n"
        return table + "\n"

    @staticmethod
    def quote(text: str) -> str:
        """Create a quote block."""
        return f"bq. {text}\n\n"

    @staticmethod
    def link(text: str, url: str) -> str:
        """Create a link."""
        return f"[{text}|{url}]"

    @staticmethod
    def bold(text: str) -> str:
        """Make text bold."""
        return f"*{text}*"

    @staticmethod
    def italic(text: str) -> str:
        """Make text italic."""
        return f"_{text}_"

    @staticmethod
    def panel(
        content: str, title: Optional[str] = None, panel_type: str = "info"
    ) -> str:
        """Create a panel (info, note, warning, success, error).

        Args:
            content: The panel content
            title: Optional panel title
            panel_type: Panel type (info, note, warning, success, error)
        """
        valid_types = {"info", "note", "warning", "success", "error"}
        if panel_type not in valid_types:
            raise ValueError(f"Panel type must be one of: {', '.join(valid_types)}")

        panel_start = "{panel"
        if title:
            panel_start += f":title={title}"
        panel_start += f":type={panel_type}"
        panel_start += "}"

        return f"{panel_start}\n{content}\n{{panel}}\n\n"

    @staticmethod
    def status(text: str, color: str = "green") -> str:
        """Create a status macro.

        Args:
            text: The status text
            color: Status color (grey, red, yellow, green, blue)
        """
        valid_colors = {"grey", "red", "yellow", "green", "blue"}
        if color not in valid_colors:
            raise ValueError(f"Color must be one of: {', '.join(valid_colors)}")

        return f"{{status:colour={color}|title={text}}}\n\n"

    @staticmethod
    def expand(summary: str, content: str) -> str:
        """Create an expandable section.

        Args:
            summary: Text shown when collapsed
            content: Content shown when expanded
        """
        return f"{{expand:summary={summary}}}\n{content}\n{{expand}}\n\n"

    @staticmethod
    def code_inline(code: str) -> str:
        """Create inline code formatting."""
        return f"{{{{code}}}}{code}{{{{code}}}}"

    @staticmethod
    def table_of_contents(min_level: int = 1, max_level: int = 6) -> str:
        """Create a table of contents macro.

        Args:
            min_level: Minimum heading level to include
            max_level: Maximum heading level to include
        """
        return f"{{toc:minLevel={min_level}|maxLevel={max_level}}}\n\n"

    @staticmethod
    def info_macro(title: str, content: str) -> str:
        """Create an info macro."""
        return f"{{info:title={title}}}\n{content}\n{{info}}\n\n"

    @staticmethod
    def note_macro(title: str, content: str) -> str:
        """Create a note macro."""
        return f"{{note:title={title}}}\n{content}\n{{note}}\n\n"

    @staticmethod
    def warning_macro(title: str, content: str) -> str:
        """Create a warning macro."""
        return f"{{warning:title={title}}}\n{content}\n{{warning}}\n\n"

    @staticmethod
    def tip_macro(title: str, content: str) -> str:
        """Create a tip macro."""
        return f"{{tip:title={title}}}\n{content}\n{{tip}}\n\n"

    @staticmethod
    def task_list(items: list[tuple[bool, str]]) -> str:
        """Create a task list with checkboxes.

        Args:
            items: List of (is_checked, task_text) tuples
        """
        return "".join(
            f"- [{'x' if checked else ' '}] {task}\n" for checked, task in items
        )

    @staticmethod
    def column_layout(columns: list[str], widths: Optional[list[str]] = None) -> str:
        """Create a multi-column layout.

        Args:
            columns: List of column contents
            widths: Optional list of column widths (e.g., ["50%", "50%"])
        """
        if widths and len(widths) != len(columns):
            raise ValueError("Number of widths must match number of columns")

        result = ""
        for i, content in enumerate(columns):
            width_str = f":width={widths[i]}" if widths and widths[i] else ""
            result += f"{{column{width_str}}}\n{content}\n{{column}}\n"

        return f"{{section:border=true}}\n{result}{{section}}\n\n"

    @staticmethod
    def details(content: str, indent_level: int = 0) -> str:
        """Add indentation and section details.

        Args:
            content: The content to format
            indent_level: Number of spaces to indent
        """
        indent = "  " * indent_level
        return "\n".join(f"{indent}{line}" for line in content.split("\n"))

    @staticmethod
    def highlight(text: str, color: str = "yellow") -> str:
        """Highlight text with a background color.

        Args:
            text: Text to highlight
            color: Background color (yellow, red, green, blue)
        """
        valid_colors = {"yellow", "red", "green", "blue"}
        if color not in valid_colors:
            raise ValueError(f"Color must be one of: {', '.join(valid_colors)}")

        return f"{{color:{color}}}{text}{{color}}"

    @staticmethod
    def divider() -> str:
        """Add a horizontal divider line."""
        return "----\n\n"


class ContentEditor:
    """Utility class for manipulating Confluence and Jira content."""

    @staticmethod
    def find_section(content: str, heading: str) -> Tuple[int, int]:
        """Find the start and end positions of a section by its heading."""
        heading_marker = f"h1. {heading}\n"
        start = content.find(heading_marker)
        if start == -1:
            return -1, -1

        start += len(heading_marker)
        next_heading = content.find("\nh1. ", start)
        end = next_heading if next_heading != -1 else len(content)

        return start, end

    @staticmethod
    def insert_after_heading(content: str, heading: str, new_content: str) -> str:
        """Insert content after a specific heading."""
        start, end = ContentEditor.find_section(content, heading)
        if start == -1:
            return content

        section_content = content[start:end].strip()
        return (
            f"{content[:start]}{section_content}\n\n" f"{new_content}\n{content[end:]}"
        )

    @staticmethod
    def replace_section(content: str, heading: str, new_content: str) -> str:
        """Replace content of a section identified by its heading."""
        start, end = ContentEditor.find_section(content, heading)
        if start == -1:
            return content

        return f"{content[:start]}{new_content}\n{content[end:]}"

    @staticmethod
    def append_to_list(content: str, list_marker: str, new_item: str) -> str:
        """Append an item to an existing list."""
        lines = content.split("\n")
        list_end = -1

        for i, line in enumerate(lines):
            if line.strip().startswith(list_marker):
                list_end = i
                while list_end + 1 < len(lines) and lines[
                    list_end + 1
                ].strip().startswith(list_marker):
                    list_end += 1

        if list_end != -1:
            indent = len(lines[list_end]) - len(lines[list_end].lstrip())
            lines.insert(list_end + 1, " " * indent + f"{list_marker} {new_item}")

        return "\n".join(lines)

    @staticmethod
    def update_table_row(
        content: str, table_start: str, row_identifier: str, new_values: list[str]
    ) -> str:
        """Update a specific row in a table."""
        lines = content.split("\n")
        table_start_idx = -1
        row_idx = -1

        # Find the table and row
        for i, line in enumerate(lines):
            if table_start in line:
                table_start_idx = i
            elif table_start_idx != -1 and row_identifier in line:
                row_idx = i
                break

        if row_idx != -1:
            lines[row_idx] = "|" + "|".join(new_values) + "|"

        return "\n".join(lines)


class TemplateHandler:
    """Handles template operations for Confluence and Jira."""

    @staticmethod
    def get_confluence_templates(confluence_client) -> List[dict]:
        """Get available Confluence templates.

        Args:
            confluence_client: Authenticated Confluence client

        Returns:
            List of template information dictionaries
        """
        try:
            # Get blueprint templates
            blueprint_templates = confluence_client.get_blueprint_templates()

            # Get custom templates
            custom_templates = confluence_client.get_content(
                type="template", expand="body.storage,version,space"
            )

            templates = []

            # Process blueprint templates
            for template in blueprint_templates.get("blueprints", []):
                templates.append(
                    {
                        "id": template.get("templateId"),
                        "name": template.get("name"),
                        "description": template.get("description"),
                        "type": "blueprint",
                        "space_key": template.get("spaceKey"),
                        "content": None,  # Content is loaded when template is used
                    }
                )

            # Process custom templates
            for template in custom_templates.get("results", []):
                templates.append(
                    {
                        "id": template.get("id"),
                        "name": template.get("title"),
                        "description": template.get("description", ""),
                        "type": "custom",
                        "space_key": template.get("space", {}).get("key"),
                        "content": template.get("body", {})
                        .get("storage", {})
                        .get("value"),
                    }
                )

            return templates
        except Exception as e:
            logger.error(f"Error fetching Confluence templates: {e}")
            return []

    @staticmethod
    def get_jira_templates(jira_client) -> List[dict]:
        """Get available Jira issue templates.

        Args:
            jira_client: Authenticated Jira client

        Returns:
            List of template information dictionaries
        """
        try:
            # Get project templates
            templates = []

            # Get issue type schemes to find templates
            schemes = jira_client.issue_type_schemes()

            for scheme in schemes:
                project_templates = jira_client.issue_templates(scheme.get("id"))
                for template in project_templates:
                    templates.append(
                        {
                            "id": template.get("id"),
                            "name": template.get("name"),
                            "description": template.get("description", ""),
                            "project_key": template.get("projectKey"),
                            "issue_type": template.get("issueType", {}).get("name"),
                            "fields": template.get("fields", {}),
                        }
                    )

            return templates
        except Exception as e:
            logger.error(f"Error fetching Jira templates: {e}")
            return []

    @staticmethod
    def apply_confluence_template(
        confluence_client,
        template_id: str,
        space_key: str,
        title: str,
        template_parameters: Optional[dict] = None,
    ) -> Optional[str]:
        """Apply a Confluence template.

        Args:
            confluence_client: Authenticated Confluence client
            template_id: ID of the template to use
            space_key: Key of the space to create page in
            title: Title for the new page
            template_parameters: Optional parameters to fill in template

        Returns:
            Content of the new page based on template
        """
        try:
            # Handle blueprint templates
            if template_id.startswith("blueprint-"):
                content = confluence_client.create_page_from_blueprint(
                    space=space_key,
                    title=title,
                    blueprint_id=template_id,
                    template_parameters=template_parameters or {},
                )
                return content.get("body", {}).get("storage", {}).get("value")

            # Handle custom templates
            else:
                template = confluence_client.get_content_by_id(
                    content_id=template_id, expand="body.storage"
                )
                content = template.get("body", {}).get("storage", {}).get("value", "")

                # Replace template parameters if provided
                if template_parameters:
                    for key, value in template_parameters.items():
                        content = content.replace(f"${{{key}}}", str(value))

                return content

        except Exception as e:
            logger.error(f"Error applying Confluence template: {e}")
            return None

    @staticmethod
    def apply_jira_template(
        jira_client,
        template_id: str,
        project_key: str,
        summary: str,
        template_parameters: Optional[dict] = None,
    ) -> Optional[dict]:
        """Apply a Jira issue template.

        Args:
            jira_client: Authenticated Jira client
            template_id: ID of the template to use
            project_key: Key of the project to create issue in
            summary: Issue summary
            template_parameters: Optional parameters to fill in template

        Returns:
            Dictionary with template-based issue fields
        """
        try:
            # Get template details
            template = jira_client.issue_template(template_id)

            # Start with template fields
            fields = template.get("fields", {}).copy()

            # Update with provided parameters
            if template_parameters:
                fields.update(template_parameters)

            # Ensure required fields
            fields.update(
                {
                    "project": {"key": project_key},
                    "summary": summary,
                }
            )

            return fields

        except Exception as e:
            logger.error(f"Error applying Jira template: {e}")
            return None

    @staticmethod
    def list_template_variables(content: str) -> List[str]:
        """Extract template variables from content.

        Args:
            content: Template content

        Returns:
            List of variable names found in template
        """
        import re

        # Match ${variable_name} pattern
        pattern = r"\$\{([^}]+)\}"
        return list(set(re.findall(pattern, content)))
