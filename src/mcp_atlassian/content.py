from typing import Dict, List, Any, Tuple, Optional
import logging
from bs4 import BeautifulSoup

from mcp_atlassian.types import Document

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
        self.template_handler = TemplateHandler()

    def _ensure_confluence(self, space_key: str):
        """Ensure we have a Confluence connection."""
        if not self.confluence:
            from .confluence import ConfluenceFetcher

            self.confluence = ConfluenceFetcher()
            self.template_handler.confluence = self.confluence

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
        version_comment: Optional[str] = None,
        full_width: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Update a page with new content."""
        try:
            print(f"\nAttempting to get page with ID: {page_id}")
            # Get current page version
            current_page = self.confluence.confluence.get_page_by_id(
                page_id=page_id, expand="version,body.storage,space"
            )
            print(f"Retrieved page: {current_page}")

            if not current_page:
                logger.error(f"Page {page_id} not found")
                return None

            # Get the current version number
            version = current_page["version"]["number"]
            print(f"Current version: {version}")

            # Always use the original title when updating
            original_title = current_page["title"]

            try:
                # Use the SDK's update_page method
                updated_page = self.confluence.confluence.update_page(
                    page_id=page_id,
                    title=original_title,  # Use original title to avoid conflicts
                    body=body,
                    type="page",
                    representation=representation,
                    minor_edit=minor_edit,
                    version_comment=version_comment,
                    full_width=full_width,
                )
                print(f"Update response: {updated_page}")

                if updated_page:
                    # Get the updated page to ensure we have the latest version
                    latest_page = self.confluence.confluence.get_page_by_id(
                        page_id=page_id, expand="version,space"
                    )
                    print(f"Retrieved updated page: {latest_page}")

                    if latest_page:
                        return {
                            "page_id": latest_page["id"],
                            "title": latest_page["title"],
                            "space_key": latest_page.get("space", {}).get("key"),
                            "version": latest_page.get("version", {}).get("number"),
                            "url": f"{self.confluence.confluence.url}/spaces/{latest_page.get('space', {}).get('key')}/pages/{latest_page['id']}",
                        }

                return None
            except Exception as e:
                error_msg = f"Error updating page: {str(e)}"
                logger.error(error_msg)
                print(f"Exception during update: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error updating page: {e}")
            print(f"Exception during update: {str(e)}")
            return None

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
        self,
        space_key: str,
        title: str,
        editor: RichTextEditor,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new page using the rich text editor content with improved validation.

        Args:
            space_key: The space key where to create the page
            title: The title of the new page
            editor: RichTextEditor instance with the page content
            parent_id: Optional parent page ID

        Returns:
            Dict containing the created page information
        """
        # Validate inputs
        if not space_key or not isinstance(space_key, str):
            raise ValueError("Invalid space key")

        title = self.validate_page_title(title)

        # Format content
        formatted_content = self.create_rich_content(editor.get_content())
        if not formatted_content:
            raise ValueError("Page content cannot be empty")

        self._ensure_confluence(space_key)

        try:
            # Create the page
            result = self.confluence.confluence.create_page(
                space=space_key,
                title=title,
                body=formatted_content,
                parent_id=parent_id,
                representation="storage",
                editor="v2",
            )

            if not result:
                logger.error("Failed to create page - no result returned")
                return None

            # Return page information
            return {
                "page_id": result.get("id"),
                "title": result.get("title"),
                "space_key": space_key,
                "url": result.get("_links", {}).get("base", "")
                + result.get("_links", {}).get("webui", ""),
                "version": result.get("version", {}).get("number"),
                "parent_id": parent_id if parent_id else None,
            }
        except Exception as e:
            logger.error(f"Error creating page: {str(e)}")
            return None

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

        # Input validation
        if not isinstance(content_blocks, list):
            logger.warning("Invalid content blocks format: not a list")
            return ""

        for block in content_blocks:
            if not isinstance(block, dict) or "type" not in block:
                logger.warning("Invalid content block format: missing type")
                continue

            block_type = block.get("type", "")
            content = block.get("content", "")
            props = block.get("properties", {})

            try:
                if block_type == "status":
                    # Validate color
                    valid_colors = ["grey", "red", "yellow", "green", "blue"]
                    color = props.get("color", "grey")
                    if color not in valid_colors:
                        logger.warning(
                            f"Invalid status color: {color}, defaulting to grey"
                        )
                        color = "grey"
                    formatted_content.append(
                        f'<ac:structured-macro ac:name="status">\n'
                        f'<ac:parameter ac:name="colour">{color}</ac:parameter>\n'
                        f'<ac:parameter ac:name="title">{content}</ac:parameter>\n'
                        "</ac:structured-macro>\n"
                    )
                elif block_type == "heading":
                    # Validate heading level
                    level = props.get("level", 1)
                    if not isinstance(level, int) or level < 1 or level > 6:
                        logger.warning(
                            f"Invalid heading level: {level}, defaulting to 1"
                        )
                        level = 1
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
                            valid_alignments = ["left", "center", "right", "justify"]
                            alignment = props["alignment"]
                            if alignment in valid_alignments:
                                style_attrs.append(f"text-align: {alignment}")
                        if "indent" in props:
                            indent = props["indent"]
                            if isinstance(indent, (int, float)) and indent >= 0:
                                style_attrs.append(f"margin-left: {indent}em")

                        style_attr = (
                            f' style="{"; ".join(style_attrs)}"' if style_attrs else ""
                        )
                        formatted_content.append(f"<p{style_attr}>{content}</p>\n")
                    else:
                        formatted_content.append(f"<p>{content}</p>\n")
                elif block_type == "list":
                    items = block.get("items", [])
                    if not isinstance(items, list):
                        logger.warning("Invalid list items format")
                        continue

                    # Filter out non-string items
                    items = [str(item) for item in items if item is not None]

                    if not items:
                        continue

                    list_type = "ol" if block.get("style") == "numbered" else "ul"
                    formatted_content.append(f"<{list_type}>\n")
                    for item in items:
                        formatted_content.append(f"<li>{item}</li>\n")
                    formatted_content.append(f"</{list_type}>\n")
                elif block_type == "table":
                    headers = block.get("headers", [])
                    rows = block.get("rows", [])

                    if not isinstance(headers, list) or not isinstance(rows, list):
                        logger.warning("Invalid table format")
                        continue

                    # Validate and sanitize table data
                    headers = [str(h) for h in headers if h is not None]
                    sanitized_rows = []
                    for row in rows:
                        if isinstance(row, list):
                            sanitized_rows.append(
                                [str(cell) for cell in row if cell is not None]
                            )

                    if not headers or not sanitized_rows:
                        continue

                    formatted_content.append("<table><tbody>\n")
                    if headers:
                        formatted_content.append("<tr>\n")
                        for header in headers:
                            formatted_content.append(f"<th>{header}</th>\n")
                        formatted_content.append("</tr>\n")

                    for row in sanitized_rows:
                        formatted_content.append("<tr>\n")
                        for cell in row:
                            formatted_content.append(f"<td>{cell}</td>\n")
                        formatted_content.append("</tr>\n")
                    formatted_content.append("</tbody></table>\n")
                elif block_type == "code":
                    language = props.get("language", "")
                    formatted_content.append(
                        f'<ac:structured-macro ac:name="code">\n'
                        f'<ac:parameter ac:name="language">{language}</ac:parameter>\n'
                        f"<ac:plain-text-body><![CDATA[{content}]]></ac:plain-text-body>\n"
                        "</ac:structured-macro>\n"
                    )
                elif (
                    block_type == "note"
                    or block_type == "info"
                    or block_type == "warning"
                ):
                    macro_type = (
                        "note"
                        if block_type == "note"
                        else ("info" if block_type == "info" else "warning")
                    )
                    formatted_content.append(
                        f'<ac:structured-macro ac:name="{macro_type}">\n'
                        f"<ac:rich-text-body><p>{content}</p></ac:rich-text-body>\n"
                        "</ac:structured-macro>\n"
                    )
            except Exception as e:
                logger.error(f"Error formatting block type {block_type}: {str(e)}")
                continue

        return "".join(formatted_content)

    def validate_page_title(self, title: str) -> str:
        """Validate and sanitize page title."""
        if not title or not isinstance(title, str):
            raise ValueError("Page title cannot be empty")

        # Remove invalid characters
        invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "[", "]"]
        for char in invalid_chars:
            title = title.replace(char, "-")

        # Trim whitespace and limit length
        title = title.strip()
        if len(title) > 255:
            title = title[:255].strip()

        return title

    def create_from_template(
        self,
        space_key: str,
        template_id: str,
        title: str,
        template_parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a page from a template with improved validation and processing."""
        self._ensure_confluence(space_key)

        try:
            # Get template details with structure analysis
            template_details = self.get_template_details(template_id, space_key)
            if not template_details:
                return {"success": False, "error": "Failed to get template details"}

            # Validate parameters against template structure
            is_valid, error_msg = self.validate_template_parameters(
                template_details["variables"], template_parameters
            )
            if not is_valid:
                return {"success": False, "error": error_msg}

            # Process template content with validated parameters
            processed_content = self._process_template_content(
                template_details["content"], template_parameters
            )

            try:
                # Create the page with processed content
                response = self.confluence.confluence.create_page(
                    space=space_key,
                    title=title,
                    body=processed_content,
                    representation="storage",
                )

                if not response:
                    logger.error("Failed to create page - no response from API")
                    return {
                        "success": False,
                        "error": "Failed to create page - no response from API",
                    }

                # Return success response with page details
                return {
                    "success": True,
                    "page_id": response.get("id"),
                    "title": response.get("title"),
                    "space_key": space_key,
                    "url": f"{self.confluence.confluence.url}/spaces/{space_key}/pages/{response.get('id')}",
                    "version": response.get("version", {}).get("number"),
                    "content": processed_content,
                }

            except Exception as e:
                error_msg = f"Error creating page: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Error in template processing: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}


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

    def analyze_template_structure(self, template_content: str) -> Dict[str, str]:
        """Analyze template content to identify available variables."""
        if not template_content:
            return {}

        import re

        variable_patterns = [
            (r"\${([^}]+)}", "dollar_brace"),  # ${variable}
            (r"@([^@]+)@", "at_symbol"),  # @variable@
            (r"\{([^}]+)\}", "brace"),  # {variable}
        ]

        variables = {}
        for pattern, format_type in variable_patterns:
            matches = re.findall(pattern, template_content)
            for match in matches:
                variables[match] = format_type

        return variables

    def get_template_details(
        self, template_id: str, space_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed template information including its structure."""
        try:
            # Get the template content
            template_content = self.confluence.get_content_template(template_id)
            if not template_content:
                logger.error(f"Template {template_id} not found")
                return None

            content = (
                template_content.get("body", {}).get("storage", {}).get("value", "")
            )
            if not content:
                logger.error("Template content is empty")
                return None

            # Analyze template structure
            variables = self.analyze_template_structure(content)

            return {
                "template_id": template_id,
                "content": content,
                "variables": variables,
                "type": template_content.get("type", "custom"),
                "name": template_content.get("name", ""),
                "space_key": space_key,
            }
        except Exception as e:
            logger.error(f"Error getting template details: {str(e)}")
            return None

    def validate_template_parameters(
        self,
        template_variables: Dict[str, str],
        provided_parameters: Optional[Dict[str, Any]],
    ) -> Tuple[bool, str]:
        """Validate that provided parameters match template requirements.
        Now more flexible - will use default/empty values for missing parameters."""
        if not provided_parameters:
            # Always return True - we'll handle missing parameters with empty strings
            return True, ""

        # Log missing variables but don't treat them as errors
        missing_vars = [
            var for var in template_variables if var not in provided_parameters
        ]
        if missing_vars:
            logger.info(
                f"Note: The following template variables will be empty: {', '.join(missing_vars)}"
            )

        # Only validate the type of provided parameters
        for key, value in provided_parameters.items():
            if not isinstance(value, (str, int, float, bool, list, dict)):
                return (
                    False,
                    f"Invalid type for parameter '{key}'. Must be a string, number, boolean, list, or dictionary.",
                )

        return True, ""

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

    def _process_template_content(
        self, content: str, template_parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process template content by replacing variables with provided values.
        Uses empty strings for missing variables to maintain template structure."""
        if not template_parameters:
            template_parameters = {}

        # Parse HTML content
        soup = BeautifulSoup(content, "html.parser")

        # Function to process text nodes
        def process_text(text: str) -> str:
            processed = text
            # Handle provided parameters
            for key, value in template_parameters.items():
                patterns = [
                    f"${{{key}}}",  # ${variable}
                    f"@{key}@",  # @variable@
                    f"{{{key}}}",  # {variable}
                    key,  # Direct match for HTML content
                ]
                for pattern in patterns:
                    processed = processed.replace(pattern, str(value))
            return processed

        # Process all text nodes in the HTML
        for text in soup.find_all(text=True):
            if text.parent.name not in [
                "script",
                "style",
            ]:  # Skip script and style tags
                new_text = process_text(text.string)
                text.replace_with(new_text)

        # Convert back to string
        processed_content = str(soup)

        # Handle any remaining template variables with empty strings
        variables = self.analyze_template_structure(processed_content)
        for var in variables:
            if var not in template_parameters:
                patterns = [
                    f"${{{var}}}",  # ${variable}
                    f"@{var}@",  # @variable@
                    f"{{{var}}}",  # {variable}
                    var,  # Direct match
                ]
                for pattern in patterns:
                    processed_content = processed_content.replace(pattern, "")

        return processed_content

    def create_from_template(
        self,
        space_key: str,
        template_id: str,
        title: str,
        template_parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a page from a template with improved validation and processing."""
        self._ensure_confluence(space_key)

        try:
            # Get template details with structure analysis
            template_details = self.get_template_details(template_id, space_key)
            if not template_details:
                return {"success": False, "error": "Failed to get template details"}

            # Validate parameters against template structure
            is_valid, error_msg = self.validate_template_parameters(
                template_details["variables"], template_parameters
            )
            if not is_valid:
                return {"success": False, "error": error_msg}

            # Process template content with validated parameters
            processed_content = self._process_template_content(
                template_details["content"], template_parameters
            )

            try:
                # Create the page with processed content
                response = self.confluence.confluence.create_page(
                    space=space_key,
                    title=title,
                    body=processed_content,
                    representation="storage",
                )

                if not response:
                    logger.error("Failed to create page - no response from API")
                    return {
                        "success": False,
                        "error": "Failed to create page - no response from API",
                    }

                # Return success response with page details
                return {
                    "success": True,
                    "page_id": response.get("id"),
                    "title": response.get("title"),
                    "space_key": space_key,
                    "url": f"{self.confluence.confluence.url}/spaces/{space_key}/pages/{response.get('id')}",
                    "version": response.get("version", {}).get("number"),
                    "content": processed_content,
                }

            except Exception as e:
                error_msg = f"Error creating page: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Error in template processing: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    @staticmethod
    def apply_jira_template(
        jira,
        template_id: str,
        project_key: str,
        summary: str,
        template_parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Apply a Jira template to create issue fields."""
        try:
            # Get the template
            template = jira.issue_templates(project_key, template_id)
            if not template:
                return {}

            # Extract fields from template
            fields = template.get("fields", {})

            # Apply template parameters if provided
            if template_parameters:
                for key, value in template_parameters.items():
                    if key in fields:
                        fields[key] = value

            return fields
        except Exception as e:
            logger.error(f"Error applying Jira template: {str(e)}")
            return {}
