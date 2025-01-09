from typing import List, Optional, Tuple


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
