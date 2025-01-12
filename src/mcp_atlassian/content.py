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


class RichTextEditor:
    """Abstracts Confluence's rich text editing capabilities."""

    def __init__(self):
        self._content = []

    def get_content(self) -> list:
        """Get the current content."""
        return self._content

    def text_with_properties(
        self,
        content: str,
        color: str = None,
        background: str = None,
        alignment: str = None,
        indent: int = None,
    ) -> "RichTextEditor":
        """Add text with advanced properties."""
        properties = {}
        if color:
            properties["color"] = color
        if background:
            properties["background"] = background
        if alignment:
            properties["alignment"] = alignment
        if indent:
            properties["indent"] = indent

        self._content.append(
            {"type": "text", "content": content, "properties": properties}
        )
        return self

    def task_list(self, items: List[Dict]) -> "RichTextEditor":
        """Add a task list with status and assignees."""
        self._content.append({"type": "task_list", "items": items})
        return self

    def image(
        self, source: str, alt: str = "", caption: str = "", alignment: str = "left"
    ) -> "RichTextEditor":
        """Add an image with caption and alignment."""
        self._content.append(
            {
                "type": "image",
                "properties": {
                    "source": source,
                    "alt": alt,
                    "caption": caption,
                    "alignment": alignment,
                },
            }
        )
        return self

    def video(self, source: str, thumbnail: str = "") -> "RichTextEditor":
        """Add a video with optional thumbnail."""
        self._content.append(
            {"type": "video", "properties": {"source": source, "thumbnail": thumbnail}}
        )
        return self

    def file(self, path: str, name: str = "", size: str = "") -> "RichTextEditor":
        """Add a file attachment."""
        self._content.append(
            {"type": "file", "properties": {"path": path, "name": name, "size": size}}
        )
        return self

    def mention(self, user: str) -> "RichTextEditor":
        """Add a user mention."""
        self._content.append({"type": "mention", "properties": {"user": user}})
        return self

    def emoji(self, name: str) -> "RichTextEditor":
        """Add an emoji."""
        self._content.append({"type": "emoji", "properties": {"name": name}})
        return self

    def expand(self, content: str, title: str) -> "RichTextEditor":
        """Add an expandable section."""
        self._content.append(
            {"type": "expand", "properties": {"title": title}, "content": content}
        )
        return self

    def divider(
        self, style: str = "single", width: str = "100%", alignment: str = "left"
    ) -> "RichTextEditor":
        """Add a divider line."""
        self._content.append(
            {
                "type": "divider",
                "properties": {"style": style, "width": width, "alignment": alignment},
            }
        )
        return self

    def format_cell(
        self, content: str, background: str = None, alignment: str = None
    ) -> str:
        """Format a table cell with advanced properties."""
        if background or alignment:
            properties = {}
            if background:
                properties["background"] = background
            if alignment:
                properties["alignment"] = alignment
            return {"content": content, "properties": properties}
        return content

    def status(self, text: str, color: str = "grey") -> "RichTextEditor":
        """Add a status macro."""
        self._content.append(
            {"type": "status", "content": text, "properties": {"color": color}}
        )
        return self

    def text(self, content: str) -> "RichTextEditor":
        """Add normal text."""
        self._content.append({"type": "text", "content": content})
        return self

    def bold(self, text: str) -> "RichTextEditor":
        """Make text bold."""
        self._content.append({"type": "text", "content": text, "style": ["bold"]})
        return self

    def italic(self, text: str) -> "RichTextEditor":
        """Make text italic."""
        self._content.append({"type": "text", "content": text, "style": ["italic"]})
        return self

    def bullet_list(self, items: list[str]) -> "RichTextEditor":
        """Create a bullet list."""
        self._content.append({"type": "list", "style": "bullet", "items": items})
        return self

    def numbered_list(self, items: list[str]) -> "RichTextEditor":
        """Create a numbered list."""
        self._content.append({"type": "list", "style": "numbered", "items": items})
        return self

    def table(
        self, headers: list[str], rows: list[list[str]], properties: Dict = None
    ) -> "RichTextEditor":
        """Create a table with advanced formatting."""
        table_data = {"type": "table", "headers": headers, "rows": rows}
        if properties:
            table_data["properties"] = properties
        self._content.append(table_data)
        return self

    def heading(self, text: str, level: int = 1) -> "RichTextEditor":
        """Add a heading."""
        self._content.append(
            {"type": "heading", "content": text, "properties": {"level": level}}
        )
        return self

    def quote(self, text: str) -> "RichTextEditor":
        """Add a quote."""
        self._content.append({"type": "quote", "content": text})
        return self

    def code(self, code: str, language: str = "") -> "RichTextEditor":
        """Add a code block."""
        self._content.append(
            {"type": "code", "content": code, "properties": {"language": language}}
        )
        return self

    def link(self, text: str, url: str) -> "RichTextEditor":
        """Add a link."""
        self._content.append(
            {"type": "link", "content": text, "properties": {"url": url}}
        )
        return self

    def panel(
        self,
        content: str,
        panel_type: str = "info",
        title: str = "",
        collapsible: bool = False,
    ) -> "RichTextEditor":
        """Add a panel with advanced options."""
        self._content.append(
            {
                "type": "panel",
                "content": content,
                "properties": {
                    "type": panel_type,
                    "title": title,
                    "collapsible": collapsible,
                },
            }
        )
        return self

    def table_of_contents(
        self, min_level: int = 1, max_level: int = 7
    ) -> "RichTextEditor":
        """Add a table of contents."""
        self._content.append(
            {
                "type": "toc",
                "properties": {"min_level": min_level, "max_level": max_level},
            }
        )
        return self


class ContentEditor:
    """High-level interface for editing Confluence content."""

    def __init__(self):
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

    def create_editor(self) -> RichTextEditor:
        """Create a new rich text editor instance."""
        return RichTextEditor()

    def create_page(
        self, space_key: str, title: str, editor: RichTextEditor
    ) -> Dict[str, Any]:
        """Create a new page using the rich text editor content.

        Args:
            space_key: The space key where to create the page
            title: The title of the new page
            editor: RichTextEditor instance with the page content

        Returns:
            Dict containing the created page information
        """
        formatted_content = self.create_rich_content(editor.get_content())
        self._ensure_confluence(space_key)

        # Create the page
        result = self.confluence.confluence.create_page(
            space=space_key,
            title=title,
            body=formatted_content,
            representation="storage",
            editor="v2",
        )

        # Return page information
        return {
            "page_id": result.get("id"),
            "title": result.get("title"),
            "space_key": space_key,
            "url": result.get("_links", {}).get("base")
            + result.get("_links", {}).get("webui", ""),
            "version": result.get("version", {}).get("number"),
        }

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

    def create_rich_content(self, content_blocks: List[Dict[str, Any]]) -> str:
        """Convert content blocks to Confluence storage format."""
        formatted_content = []

        for block in content_blocks:
            if not isinstance(block, dict) or "type" not in block:
                logger.warning("Invalid content block format: missing type")
                continue

            block_type = block.get("type", "")
            content = block.get("content", "")
            props = block.get("properties", {})

            try:
                if block_type == "status":
                    color = props.get("color", "grey")
                    formatted_content.append(
                        f'<ac:structured-macro ac:name="status">\n'
                        f'<ac:parameter ac:name="colour">{color}</ac:parameter>\n'
                        f'<ac:parameter ac:name="title">{content}</ac:parameter>\n'
                        "</ac:structured-macro>\n"
                    )
                elif block_type == "heading":
                    level = props.get("level", 1)
                    formatted_content.append(f"<h{level}>{content}</h{level}>\n")
                elif block_type == "text":
                    # Handle text with advanced properties
                    if "properties" in block:
                        style_attrs = []
                        if "color" in props:
                            style_attrs.append(f"color: {props['color']}")
                        if "background" in props:
                            style_attrs.append(
                                f"background-color: {props['background']}"
                            )
                        if "alignment" in props:
                            style_attrs.append(f"text-align: {props['alignment']}")
                        if "indent" in props:
                            style_attrs.append(f"margin-left: {props['indent']}em")

                        style_attr = (
                            f' style="{"; ".join(style_attrs)}"' if style_attrs else ""
                        )
                        formatted_content.append(f"<p{style_attr}>{content}</p>\n")
                    else:
                        style = block.get("style", [])
                        if isinstance(style, list):
                            if "bold" in style:
                                content = f"<strong>{content}</strong>"
                            if "italic" in style:
                                content = f"<em>{content}</em>"
                        elif isinstance(style, dict):
                            if style.get("bold"):
                                content = f"<strong>{content}</strong>"
                            if style.get("italic"):
                                content = f"<em>{content}</em>"
                        formatted_content.append(f"<p>{content}</p>\n")
                elif block_type == "list":
                    tag = "ol" if block.get("style") == "numbered" else "ul"
                    items = block.get("items", [])
                    if not isinstance(items, list):
                        logger.warning(f"Invalid list items format for block: {block}")
                        continue
                    formatted_items = "\n".join(f"<li>{item}</li>" for item in items)
                    formatted_content.append(f"<{tag}>\n{formatted_items}\n</{tag}>\n")
                elif block_type == "task_list":
                    formatted_content.append(
                        '<ac:structured-macro ac:name="tasklist">\n<ac:task-list>'
                    )
                    for item in block.get("items", []):
                        status = (
                            "complete"
                            if item.get("status") == "complete"
                            else "incomplete"
                        )
                        assignee = item.get("assignee", "")
                        due_date = item.get("due", "")
                        formatted_content.append(
                            f"<ac:task>\n"
                            f"<ac:task-status>{status}</ac:task-status>\n"
                            f'<ac:task-body>{item["text"]}</ac:task-body>\n'
                            + (
                                f"<ac:task-assignee>{assignee}</ac:task-assignee>\n"
                                if assignee
                                else ""
                            )
                            + (
                                f"<ac:task-due-date>{due_date}</ac:task-due-date>\n"
                                if due_date
                                else ""
                            )
                            + "</ac:task>\n"
                        )
                    formatted_content.append(
                        "</ac:task-list>\n</ac:structured-macro>\n"
                    )
                elif block_type == "image":
                    source = props.get("source", "")
                    alt = props.get("alt", "")
                    caption = props.get("caption", "")
                    alignment = props.get("alignment", "left")
                    formatted_content.append(
                        f'<ac:image ac:align="{alignment}">\n'
                        f'<ri:attachment ri:filename="{source}"/>\n'
                        + (f"<ac:alt-text>{alt}</ac:alt-text>\n" if alt else "")
                        + (f"<ac:caption>{caption}</ac:caption>\n" if caption else "")
                        + "</ac:image>\n"
                    )
                elif block_type == "video":
                    source = props.get("source", "")
                    thumbnail = props.get("thumbnail", "")
                    formatted_content.append(
                        f'<ac:structured-macro ac:name="video">\n'
                        f'<ac:parameter ac:name="url">{source}</ac:parameter>\n'
                        + (
                            f'<ac:parameter ac:name="thumbnail">{thumbnail}</ac:parameter>\n'
                            if thumbnail
                            else ""
                        )
                        + "</ac:structured-macro>\n"
                    )
                elif block_type == "file":
                    path = props.get("path", "")
                    name = props.get("name", "")
                    formatted_content.append(
                        f'<ac:structured-macro ac:name="attachments">\n'
                        f'<ac:parameter ac:name="upload">{path}</ac:parameter>\n'
                        + (
                            f'<ac:parameter ac:name="name">{name}</ac:parameter>\n'
                            if name
                            else ""
                        )
                        + "</ac:structured-macro>\n"
                    )
                elif block_type == "mention":
                    user = props.get("user", "")
                    formatted_content.append(
                        f'<ac:link>\n<ri:user ri:username="{user}"/>\n</ac:link>\n'
                    )
                elif block_type == "emoji":
                    name = props.get("name", "")
                    formatted_content.append(f'<ac:emoticon ac:name="{name}"/>\n')
                elif block_type == "expand":
                    title = props.get("title", "")
                    formatted_content.append(
                        f'<ac:structured-macro ac:name="expand">\n'
                        f'<ac:parameter ac:name="title">{title}</ac:parameter>\n'
                        "<ac:rich-text-body>\n"
                        f"<p>{content}</p>\n"
                        "</ac:rich-text-body>\n"
                        "</ac:structured-macro>\n"
                    )
                elif block_type == "divider":
                    style = props.get("style", "single")
                    width = props.get("width", "100%")
                    alignment = props.get("alignment", "left")
                    formatted_content.append(
                        f'<hr style="border-style: {style}; width: {width}; text-align: {alignment};"/>\n'
                    )
                elif block_type == "code":
                    language = props.get("language", "")
                    formatted_content.append(
                        f'<ac:structured-macro ac:name="code">\n'
                        f'<ac:parameter ac:name="language">{language}</ac:parameter>\n'
                        "<ac:plain-text-body><![CDATA[\n"
                        f"{content}\n"
                        "]]></ac:plain-text-body>\n"
                        "</ac:structured-macro>\n"
                    )
                elif block_type == "table":
                    table_props = props or {}
                    column_widths = table_props.get("column_widths", [])

                    table_start = "<table"
                    if column_widths:
                        table_start += ' style="'
                        table_start += "; ".join(
                            f"width: {width}" for width in column_widths
                        )
                        table_start += '"'
                    table_start += "><tbody>\n"

                    formatted_content.append(table_start)

                    # Handle headers
                    headers = block.get("headers", [])
                    if headers:
                        header_row = "<tr>"
                        for header in headers:
                            if isinstance(header, dict):
                                header_content = header["content"]
                                header_props = header.get("properties", {})
                                style_attrs = []
                                if "background" in header_props:
                                    style_attrs.append(
                                        f"background-color: {header_props['background']}"
                                    )
                                if "alignment" in header_props:
                                    style_attrs.append(
                                        f"text-align: {header_props['alignment']}"
                                    )
                                style_attr = (
                                    f' style="{"; ".join(style_attrs)}"'
                                    if style_attrs
                                    else ""
                                )
                                header_row += f"<th{style_attr}>{header_content}</th>"
                            else:
                                header_row += f"<th>{header}</th>"
                        header_row += "</tr>\n"
                        formatted_content.append(header_row)

                    # Handle rows
                    for row in block.get("rows", []):
                        row_content = "<tr>"
                        for cell in row:
                            if isinstance(cell, dict):
                                cell_content = cell["content"]
                                cell_props = cell.get("properties", {})
                                style_attrs = []
                                if "background" in cell_props:
                                    style_attrs.append(
                                        f"background-color: {cell_props['background']}"
                                    )
                                if "alignment" in cell_props:
                                    style_attrs.append(
                                        f"text-align: {cell_props['alignment']}"
                                    )
                                style_attr = (
                                    f' style="{"; ".join(style_attrs)}"'
                                    if style_attrs
                                    else ""
                                )
                                row_content += f"<td{style_attr}>{cell_content}</td>"
                            else:
                                row_content += f"<td>{cell}</td>"
                        row_content += "</tr>\n"
                        formatted_content.append(row_content)

                    formatted_content.append("</tbody></table>\n")
                elif block_type == "panel":
                    panel_type = props.get("type", "info")
                    title = props.get("title", "")
                    collapsible = props.get("collapsible", False)
                    icon = props.get("icon", "")

                    macro_params = [
                        f'<ac:parameter ac:name="type">{panel_type}</ac:parameter>'
                    ]
                    if title:
                        macro_params.append(
                            f'<ac:parameter ac:name="title">{title}</ac:parameter>'
                        )
                    if collapsible:
                        macro_params.append(
                            '<ac:parameter ac:name="collapsible">true</ac:parameter>'
                        )
                    if icon:
                        macro_params.append(
                            f'<ac:parameter ac:name="icon">{icon}</ac:parameter>'
                        )

                    formatted_content.append(
                        '<ac:structured-macro ac:name="panel">\n'
                        + "\n".join(macro_params)
                        + "\n<ac:rich-text-body>\n"
                        f"<p>{content}</p>\n"
                        "</ac:rich-text-body>\n"
                        "</ac:structured-macro>\n"
                    )
            except Exception as e:
                logger.error(f"Error formatting block type {block_type}: {e}")
                continue

        return "\n".join(formatted_content)


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
