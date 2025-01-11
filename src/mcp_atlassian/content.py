from typing import Dict, List, Any, Tuple, Optional
import logging
from bs4 import BeautifulSoup

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
        """Create a panel (info, note, warning, success, error)."""
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
        """Create a status macro."""
        valid_colors = {"grey", "red", "yellow", "green", "blue"}
        if color not in valid_colors:
            raise ValueError(f"Color must be one of: {', '.join(valid_colors)}")

        return f"{{status:colour={color}|title={text}}}\n\n"


class ContentEditor:
    """High-level interface for AI to edit Confluence content."""

    def __init__(self):
        """Initialize the content editor."""
        self.confluence = None

    def _ensure_confluence(self, space_key: str):
        """Ensure we have a Confluence connection."""
        if not self.confluence:
            from .confluence import ConfluenceFetcher

            self.confluence = ConfluenceFetcher()

    def _get_page(self, page_title: str, space_key: str) -> Dict[str, Any]:
        """Get a page by title and space key."""
        self._ensure_confluence(space_key)
        page = self.confluence.get_page_by_title(space_key, page_title)
        if not page:
            raise ValueError(f"Page '{page_title}' not found in space '{space_key}'")
        return page

    def _get_section_content(self, content: str, section: str) -> Tuple[str, int]:
        """Find a section in the content and return its content and position."""
        soup = BeautifulSoup(content, "html.parser")
        headers = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

        for i, header in enumerate(headers):
            if header.get_text().strip() == section:
                next_header = headers[i + 1] if i + 1 < len(headers) else None
                section_content = ""
                current = header

                while current and (not next_header or current != next_header):
                    section_content += str(current)
                    current = current.next_sibling

                return section_content, i

        # If section not found, create it
        last_header = headers[-1] if headers else None
        if last_header:
            return str(last_header), len(headers)

        # If no headers exist, return empty content
        return "", 0

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        representation: str = "storage",
        minor_edit: bool = False,
    ) -> None:
        """Update a page with new content."""
        self.confluence.confluence.update_page(
            page_id=page_id,
            title=title,
            body=body,
            type="page",
            representation=representation,
            minor_edit=minor_edit,
            full_width=False,
        )

    def add_list_item(
        self,
        page_title: str,
        space_key: str,
        section: str,
        item: str,
        item_type: str = "bullet",
    ) -> None:
        """Add an item to a list in a specific section."""
        page = self._get_page(page_title, space_key)
        content = page.metadata["content"]

        section_content, pos = self._get_section_content(content, section)

        # Create new list item in appropriate format
        new_item = f"<li>{item}</li>"

        # Find existing list or create new one
        if "<ul>" in section_content:
            new_content = section_content.replace("</ul>", f"{new_item}</ul>")
        else:
            new_content = f"{section_content}<ul>{new_item}</ul>"

        # Update the page
        self.confluence.update_page(
            page_id=page.metadata["page_id"],
            title=page_title,
            body=content.replace(section_content, new_content),
            representation="storage",
        )

    def update_status(
        self, page_title: str, space_key: str, status: str, color: str = "green"
    ) -> None:
        """Update the status macro on the page."""
        page = self._get_page(page_title, space_key)
        current_page = self.confluence.confluence.get_page_by_id(
            page_id=page.metadata["page_id"], expand="body.storage,version"
        )
        content = current_page["body"]["storage"]["value"]

        # Create new status macro
        new_status = f"""
<ac:structured-macro ac:name="status">
    <ac:parameter ac:name="colour">{color}</ac:parameter>
    <ac:parameter ac:name="title">{status}</ac:parameter>
</ac:structured-macro>
"""

        # Find and replace existing status or add new one
        soup = BeautifulSoup(content, "html.parser")
        existing_status = soup.find("ac:structured-macro", {"ac:name": "status"})

        if existing_status:
            existing_status.replace_with(BeautifulSoup(new_status, "html.parser"))
        else:
            # Add after first heading
            first_heading = soup.find(["h1", "h2", "h3", "h4", "h5", "h6"])
            if first_heading:
                first_heading.insert_after(BeautifulSoup(new_status, "html.parser"))

        # Update the page
        self.update_page(
            page_id=page.metadata["page_id"],
            title=page_title,
            body=str(soup),
            representation="storage",
            minor_edit=True,
        )

    def add_section(
        self,
        page_title: str,
        space_key: str,
        section_title: str,
        content: List[Dict[str, Any]],
    ) -> None:
        """Add a new section to the page."""
        page = self._get_page(page_title, space_key)
        current_page = self.confluence.confluence.get_page_by_id(
            page_id=page.metadata["page_id"], expand="body.storage,version"
        )
        page_content = current_page["body"]["storage"]["value"]

        # Create the new section in storage format
        new_section = f"<h2>{section_title}</h2>\n\n"

        for item in content:
            if item["type"] == "text":
                new_section += f"<p>{item['content']}</p>\n\n"
            elif item["type"] == "list":
                list_tag = "ol" if item["style"] == "numbered" else "ul"
                new_section += f"<{list_tag}>\n"
                for list_item in item["items"]:
                    new_section += f"<li>{list_item}</li>\n"
                new_section += f"</{list_tag}>\n\n"
            elif item["type"] == "note":
                new_section += f"""
<ac:structured-macro ac:name="note">
    <ac:rich-text-body>
        <p>{item['content']}</p>
    </ac:rich-text-body>
</ac:structured-macro>\n\n"""
            elif item["type"] == "table":
                new_section += "<table><tbody>\n"
                # Add headers
                new_section += "<tr>\n"
                for header in item["headers"]:
                    new_section += f"<th>{header}</th>\n"
                new_section += "</tr>\n"
                # Add rows
                for row in item["rows"]:
                    new_section += "<tr>\n"
                    for cell in row:
                        new_section += f"<td>{cell}</td>\n"
                    new_section += "</tr>\n"
                new_section += "</tbody></table>\n\n"
            elif item["type"] == "panel":
                new_section += f"""
<ac:structured-macro ac:name="panel">
    <ac:parameter ac:name="title">{item.get("title", "")}</ac:parameter>
    <ac:parameter ac:name="type">{item.get("panel_type", "info")}</ac:parameter>
    <ac:rich-text-body>
        <p>{item['content']}</p>
    </ac:rich-text-body>
</ac:structured-macro>\n\n"""

        # Append the new section
        new_content = page_content + new_section

        # Update the page
        self.update_page(
            page_id=page.metadata["page_id"],
            title=page_title,
            body=new_content,
            representation="storage",
            minor_edit=True,
        )

    def add_code_block(
        self,
        page_title: str,
        space_key: str,
        section: str,
        code: str,
        language: str,
        title: Optional[str] = None,
    ) -> None:
        """Add a code block to a specific section."""
        page = self._get_page(page_title, space_key)
        current_page = self.confluence.confluence.get_page_by_id(
            page_id=page.metadata["page_id"], expand="body.storage,version"
        )
        content = current_page["body"]["storage"]["value"]

        section_content, pos = self._get_section_content(content, section)

        # Create code macro
        code_macro = f"""
<ac:structured-macro ac:name="code">
    <ac:parameter ac:name="language">{language}</ac:parameter>
    {f'<ac:parameter ac:name="title">{title}</ac:parameter>' if title else ''}
    <ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body>
</ac:structured-macro>
"""

        # Add to section
        new_content = content.replace(section_content, section_content + code_macro)

        # Update the page
        self.update_page(
            page_id=page.metadata["page_id"],
            title=page_title,
            body=new_content,
            representation="storage",
            minor_edit=True,
        )

    def update_table(
        self,
        page_title: str,
        space_key: str,
        section: str,
        row_identifier: str,
        new_values: Dict[str, str],
    ) -> None:
        """Update a specific row in a table."""
        page = self._get_page(page_title, space_key)
        content = page.metadata["content"]

        section_content, pos = self._get_section_content(content, section)

        # Parse the table
        soup = BeautifulSoup(section_content, "html.parser")
        table = soup.find("table")
        if not table:
            raise ValueError(f"No table found in section '{section}'")

        # Get headers
        headers = []
        header_row = table.find("tr")
        if header_row:
            headers = [
                th.get_text().strip() for th in header_row.find_all(["th", "td"])
            ]

        # Find and update the target row
        for row in table.find_all("tr")[1:]:  # Skip header row
            cells = row.find_all("td")
            if cells and cells[0].get_text().strip() == row_identifier:
                for header, new_value in new_values.items():
                    if header in headers:
                        idx = headers.index(header)
                        if idx < len(cells):
                            cells[idx].string = new_value

        # Update the page
        self.confluence.update_page(
            page_id=page.metadata["page_id"],
            title=page_title,
            body=content.replace(section_content, str(soup)),
            representation="storage",
        )

    def add_panel(
        self,
        page_title: str,
        space_key: str,
        section: str,
        content: str,
        panel_type: str = "info",
        title: Optional[str] = None,
    ) -> None:
        """Add a panel to a specific section."""
        page = self._get_page(page_title, space_key)
        current_page = self.confluence.confluence.get_page_by_id(
            page_id=page.metadata["page_id"], expand="body.storage,version"
        )
        page_content = current_page["body"]["storage"]["value"]

        section_content, pos = self._get_section_content(page_content, section)

        # Create panel macro
        panel_macro = f"""
<ac:structured-macro ac:name="panel">
    <ac:parameter ac:name="type">{panel_type}</ac:parameter>
    {f'<ac:parameter ac:name="title">{title}</ac:parameter>' if title else ''}
    <ac:rich-text-body>
        <p>{content}</p>
    </ac:rich-text-body>
</ac:structured-macro>
"""

        # Add to section
        new_content = page_content.replace(
            section_content, section_content + panel_macro
        )

        # Update the page
        self.update_page(
            page_id=page.metadata["page_id"],
            title=page_title,
            body=new_content,
            representation="storage",
            minor_edit=True,
        )

    def create_page(
        self, space_key: str, title: str, content: List[Dict[str, Any]]
    ) -> None:
        """Create a new page with structured content.

        Args:
            space_key: The space key where to create the page
            title: The title of the new page
            content: List of content blocks to add to the page
        """
        self._ensure_confluence(space_key)

        # Build the page content in storage format
        page_content = ""

        for item in content:
            if item["type"] == "status":
                page_content += f"""
<ac:structured-macro ac:name="status">
    <ac:parameter ac:name="colour">{item["color"]}</ac:parameter>
    <ac:parameter ac:name="title">{item["text"]}</ac:parameter>
</ac:structured-macro>\n"""

            elif item["type"] == "panel":
                page_content += f"""
<ac:structured-macro ac:name="panel">
    <ac:parameter ac:name="title">{item.get("title", "")}</ac:parameter>
    <ac:parameter ac:name="type">{item.get("panel_type", "info")}</ac:parameter>
    <ac:rich-text-body>
        <p>{item["content"]}</p>
    </ac:rich-text-body>
</ac:structured-macro>\n"""

            elif item["type"] == "text":
                page_content += f"<p>{item['content']}</p>\n\n"

            elif item["type"] == "toc":
                page_content += f"""
<ac:structured-macro ac:name="toc">
    <ac:parameter ac:name="minLevel">{item.get("min_level", 1)}</ac:parameter>
    <ac:parameter ac:name="maxLevel">{item.get("max_level", 7)}</ac:parameter>
</ac:structured-macro>\n"""

        # Create the page using the correct parameters
        return self.confluence.confluence.create_page(
            space=space_key,
            title=title,
            body=page_content,
            representation="storage",
            editor="v2",
        )

    def format_text(self, text: str, formatting: List[str]) -> str:
        """Apply formatting to text.

        Args:
            text: The text to format
            formatting: List of formats to apply ('bold', 'italic', 'underline', 'strike', 'superscript', 'subscript')
        """
        formatted = text
        for fmt in formatting:
            if fmt == "bold":
                formatted = f"<strong>{formatted}</strong>"
            elif fmt == "italic":
                formatted = f"<em>{formatted}</em>"
            elif fmt == "underline":
                formatted = f"<u>{formatted}</u>"
            elif fmt == "strike":
                formatted = f"<strike>{formatted}</strike>"
            elif fmt == "superscript":
                formatted = f"<sup>{formatted}</sup>"
            elif fmt == "subscript":
                formatted = f"<sub>{formatted}</sub>"
        return formatted

    def add_link(
        self,
        page_title: str,
        space_key: str,
        section: str,
        link_text: str,
        url: str,
        link_type: str = "external",
    ) -> None:
        """Add a link to a specific section.

        Args:
            link_type: Type of link ('external', 'page', 'anchor')
        """
        page = self._get_page(page_title, space_key)
        current_page = self.confluence.confluence.get_page_by_id(
            page_id=page.metadata["page_id"], expand="body.storage,version"
        )
        content = current_page["body"]["storage"]["value"]
        section_content, pos = self._get_section_content(content, section)

        if link_type == "external":
            link = f'<a href="{url}">{link_text}</a>'
        elif link_type == "page":
            link = f'<ac:link><ri:page ri:content-title="{url}"/><ac:plain-text-link-body><![CDATA[{link_text}]]></ac:plain-text-link-body></ac:link>'
        elif link_type == "anchor":
            link = f'<ac:link ac:anchor="{url}"><ac:plain-text-link-body><![CDATA[{link_text}]]></ac:plain-text-link-body></ac:link>'

        new_content = content.replace(section_content, section_content + link)

        self.update_page(
            page_id=page.metadata["page_id"],
            title=page_title,
            body=new_content,
            representation="storage",
            minor_edit=True,
        )

    def add_expandable_section(
        self, page_title: str, space_key: str, section: str, title: str, content: str
    ) -> None:
        """Add an expandable section."""
        page = self._get_page(page_title, space_key)
        current_page = self.confluence.confluence.get_page_by_id(
            page_id=page.metadata["page_id"], expand="body.storage,version"
        )
        page_content = current_page["body"]["storage"]["value"]
        section_content, pos = self._get_section_content(page_content, section)

        expand_macro = f"""
<ac:structured-macro ac:name="expand">
    <ac:parameter ac:name="title">{title}</ac:parameter>
    <ac:rich-text-body>
        <p>{content}</p>
    </ac:rich-text-body>
</ac:structured-macro>
"""

        new_content = page_content.replace(
            section_content, section_content + expand_macro
        )

        self.update_page(
            page_id=page.metadata["page_id"],
            title=page_title,
            body=new_content,
            representation="storage",
            minor_edit=True,
        )

    def move_section(
        self,
        page_title: str,
        space_key: str,
        section: str,
        target_section: str,
        position: str = "after",
    ) -> None:
        """Move a section relative to another section."""
        page = self._get_page(page_title, space_key)
        current_page = self.confluence.confluence.get_page_by_id(
            page_id=page.metadata["page_id"], expand="body.storage,version"
        )
        content = current_page["body"]["storage"]["value"]

        # Get source and target sections
        source_content, source_pos = self._get_section_content(content, section)
        target_content, target_pos = self._get_section_content(content, target_section)

        # Remove source section
        content_without_source = content.replace(source_content, "")

        # Insert at target position
        if position == "after":
            new_content = content_without_source.replace(
                target_content, target_content + source_content
            )
        else:  # before
            new_content = content_without_source.replace(
                target_content, source_content + target_content
            )

        self.update_page(
            page_id=page.metadata["page_id"],
            title=page_title,
            body=new_content,
            representation="storage",
            minor_edit=True,
        )

    def add_table_of_contents(
        self,
        page_title: str,
        space_key: str,
        min_level: int = 1,
        max_level: int = 7,
        position: str = "top",
    ) -> None:
        """Add a table of contents to the page."""
        page = self._get_page(page_title, space_key)
        current_page = self.confluence.confluence.get_page_by_id(
            page_id=page.metadata["page_id"], expand="body.storage,version"
        )
        content = current_page["body"]["storage"]["value"]

        toc_macro = f"""
<ac:structured-macro ac:name="toc">
    <ac:parameter ac:name="minLevel">{min_level}</ac:parameter>
    <ac:parameter ac:name="maxLevel">{max_level}</ac:parameter>
</ac:structured-macro>
"""

        if position == "top":
            new_content = toc_macro + content
        else:
            new_content = content + toc_macro

        self.update_page(
            page_id=page.metadata["page_id"],
            title=page_title,
            body=new_content,
            representation="storage",
            minor_edit=True,
        )


class TemplateHandler:
    """Handles Confluence templates and blueprints."""

    def __init__(self):
        """Initialize the template handler."""
        self.confluence = None

    def _ensure_confluence(self, space_key: str):
        """Ensure we have a Confluence connection."""
        if not self.confluence:
            from .confluence import ConfluenceFetcher

            self.confluence = ConfluenceFetcher()

    def get_content_templates(
        self, space_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get content templates for a space or global templates."""
        self._ensure_confluence(space_key or "")
        return self.confluence.confluence.get_content_templates(space_key)

    def get_blueprint_templates(
        self, space_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get blueprint templates for a space or global blueprints."""
        self._ensure_confluence(space_key or "")
        return self.confluence.confluence.get_blueprint_templates(space_key)

    def create_from_template(
        self,
        space_key: str,
        template_id: str,
        title: str,
        template_parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a page from a template."""
        self._ensure_confluence(space_key)

        # Get the template
        template = self.confluence.confluence.get_content_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Prepare the content
        content = template["body"]["storage"]["value"]
        if template_parameters:
            # Replace template parameters in content
            for key, value in template_parameters.items():
                content = content.replace(f"${key}$", str(value))

        # Create the page
        return self.confluence.confluence.create_page(
            space=space_key,
            title=title,
            body=content,
            representation="storage",
            editor="v2",
        )

    def create_or_update_template(
        self,
        name: str,
        body: Dict[str, str],
        template_type: str = "page",
        template_id: Optional[str] = None,
        description: Optional[str] = None,
        labels: Optional[List[Dict[str, str]]] = None,
        space: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create or update a content template."""
        self._ensure_confluence(space or "")
        return self.confluence.confluence.create_or_update_template(
            name=name,
            body=body,
            template_type=template_type,
            template_id=template_id,
            description=description,
            labels=labels,
            space=space,
        )

    def remove_template(self, template_id: str) -> None:
        """Remove a template."""
        self._ensure_confluence("")
        self.confluence.confluence.remove_template(template_id)
