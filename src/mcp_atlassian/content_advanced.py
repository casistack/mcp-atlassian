from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger("mcp-atlassian")


class AdvancedFormatting:
    """Advanced formatting capabilities for Confluence content."""

    @staticmethod
    def two_column_layout(left_content: str, right_content: str) -> str:
        """Create a two-column layout section.

        Args:
            left_content: Content for the left column
            right_content: Content for the right column
        """
        return (
            '<ac:layout><ac:layout-section ac:type="two_equal">'
            f"<ac:layout-cell>{left_content}</ac:layout-cell>"
            f"<ac:layout-cell>{right_content}</ac:layout-cell>"
            "</ac:layout-section></ac:layout>"
        )

    @staticmethod
    def three_column_layout(contents: List[str]) -> str:
        """Create a three-column layout section.

        Args:
            contents: List of three content strings for each column
        """
        if len(contents) != 3:
            raise ValueError(
                "Three-column layout requires exactly three content blocks"
            )

        return (
            '<ac:layout><ac:layout-section ac:type="three_equal">'
            + "".join(
                f"<ac:layout-cell>{content}</ac:layout-cell>" for content in contents
            )
            + "</ac:layout-section></ac:layout>"
        )

    @staticmethod
    def collapsible_section(
        title: str, content: str, initial_state: str = "collapsed"
    ) -> str:
        """Create a collapsible section.

        Args:
            title: Title of the collapsible section
            content: Content inside the section
            initial_state: 'collapsed' or 'expanded'
        """
        return (
            '<ac:structured-macro ac:name="expand">'
            f'<ac:parameter ac:name="title">{title}</ac:parameter>'
            f'<ac:parameter ac:name="default-state">{initial_state}</ac:parameter>'
            f"<ac:rich-text-body>{content}</ac:rich-text-body>"
            "</ac:structured-macro>"
        )

    @staticmethod
    def info_card(
        title: str, content: str, icon: str = "info", color: str = "#0052CC"
    ) -> str:
        """Create an info card with custom styling.

        Args:
            title: Card title
            content: Card content
            icon: Icon name (info, warning, check, etc.)
            color: Background color in hex
        """
        return (
            '<ac:structured-macro ac:name="info-card">'
            f'<ac:parameter ac:name="title">{title}</ac:parameter>'
            f'<ac:parameter ac:name="icon">{icon}</ac:parameter>'
            f'<ac:parameter ac:name="color">{color}</ac:parameter>'
            f"<ac:rich-text-body>{content}</ac:rich-text-body>"
            "</ac:structured-macro>"
        )

    @staticmethod
    def tabbed_content(tabs: List[Dict[str, str]]) -> str:
        """Create tabbed content section.

        Args:
            tabs: List of dictionaries with 'title' and 'content' keys
        """
        return (
            '<ac:structured-macro ac:name="tabbed-content">'
            + "".join(
                '<ac:structured-macro ac:name="tab">'
                f'<ac:parameter ac:name="title">{tab["title"]}</ac:parameter>'
                f'<ac:rich-text-body>{tab["content"]}</ac:rich-text-body>'
                "</ac:structured-macro>"
                for tab in tabs
            )
            + "</ac:structured-macro>"
        )

    @staticmethod
    def roadmap(items: List[Dict[str, Union[str, Dict]]]) -> str:
        """Create a roadmap/timeline visualization.

        Args:
            items: List of dictionaries with 'title', 'date', 'status', and 'description'
        """
        return (
            '<ac:structured-macro ac:name="roadmap">'
            + "".join(
                '<ac:structured-macro ac:name="roadmap-item">'
                f'<ac:parameter ac:name="title">{item["title"]}</ac:parameter>'
                f'<ac:parameter ac:name="date">{item["date"]}</ac:parameter>'
                f'<ac:parameter ac:name="status">{item.get("status", "on-track")}</ac:parameter>'
                f'<ac:rich-text-body>{item["description"]}</ac:rich-text-body>'
                "</ac:structured-macro>"
                for item in items
            )
            + "</ac:structured-macro>"
        )

    @staticmethod
    def chart(
        chart_type: str,
        data: Dict[str, Union[List, Dict]],
        title: str = "",
        width: int = 600,
        height: int = 400,
    ) -> str:
        """Create various types of charts.

        Args:
            chart_type: Type of chart (pie, bar, line, etc.)
            data: Chart data structure
            title: Chart title
            width: Chart width in pixels
            height: Chart height in pixels
        """
        return (
            '<ac:structured-macro ac:name="chart">'
            f'<ac:parameter ac:name="type">{chart_type}</ac:parameter>'
            f'<ac:parameter ac:name="title">{title}</ac:parameter>'
            f'<ac:parameter ac:name="width">{width}</ac:parameter>'
            f'<ac:parameter ac:name="height">{height}</ac:parameter>'
            f'<ac:parameter ac:name="data">{str(data)}</ac:parameter>'
            "</ac:structured-macro>"
        )

    @staticmethod
    def table_with_styling(
        headers: List[str],
        rows: List[List[str]],
        styles: Dict[str, Dict[str, str]] = None,
    ) -> str:
        """Create a table with advanced styling options.

        Args:
            headers: List of header texts
            rows: List of row data
            styles: Dictionary of cell styles (e.g., {"1-1": {"background": "#f0f0f0"}})
        """
        styles = styles or {}

        def apply_style(row_idx: int, col_idx: int, content: str) -> str:
            cell_style = styles.get(f"{row_idx}-{col_idx}", {})
            style_str = " ".join(f'{k}="{v}"' for k, v in cell_style.items())
            return (
                f"<td {style_str}>{content}</td>"
                if style_str
                else f"<td>{content}</td>"
            )

        table = "<table><tbody>"
        # Headers
        table += "<tr>" + "".join(f"<th>{header}</th>" for header in headers) + "</tr>"
        # Rows
        for row_idx, row in enumerate(rows, 1):
            table += (
                "<tr>"
                + "".join(
                    apply_style(row_idx, col_idx, cell)
                    for col_idx, cell in enumerate(row, 1)
                )
                + "</tr>"
            )
        table += "</tbody></table>"
        return table

    @staticmethod
    def decision_table(
        headers: List[str], rows: List[List[str]], decision_column: int
    ) -> str:
        """Create a decision table with highlighting.

        Args:
            headers: List of header texts
            rows: List of row data
            decision_column: Index of the decision column (0-based)
        """
        table = '<table class="decision-table"><tbody>'
        # Headers
        table += "<tr>" + "".join(f"<th>{header}</th>" for header in headers) + "</tr>"
        # Rows
        for row in rows:
            cells = []
            for idx, cell in enumerate(row):
                cell_class = ' class="decision-cell"' if idx == decision_column else ""
                cells.append(f"<td{cell_class}>{cell}</td>")
            table += "<tr>" + "".join(cells) + "</tr>"
        table += "</tbody></table>"
        return table

    @staticmethod
    def content_by_label(
        labels: List[str],
        max_results: int = 10,
        sort: str = "modified",
        excerpt: bool = True,
    ) -> str:
        """Display content tagged with specific labels.

        Args:
            labels: List of labels to filter by
            max_results: Maximum number of results to show
            sort: Sort order ('modified', 'created', 'title')
            excerpt: Whether to show content excerpts
        """
        return (
            '<ac:structured-macro ac:name="content-by-label">'
            f'<ac:parameter ac:name="labels">{",".join(labels)}</ac:parameter>'
            f'<ac:parameter ac:name="max">{max_results}</ac:parameter>'
            f'<ac:parameter ac:name="sort">{sort}</ac:parameter>'
            f'<ac:parameter ac:name="excerpt">{str(excerpt).lower()}</ac:parameter>'
            "</ac:structured-macro>"
        )

    @staticmethod
    def jira_issues(
        jql: str,
        columns: List[str] = None,
        max_results: int = 20,
        server_id: str = None,
    ) -> str:
        """Display Jira issues using JQL.

        Args:
            jql: JQL query string
            columns: List of columns to display
            max_results: Maximum number of issues to show
            server_id: Optional Jira server ID for multi-instance setups
        """
        macro = (
            '<ac:structured-macro ac:name="jira">'
            f'<ac:parameter ac:name="jqlQuery">{jql}</ac:parameter>'
            f'<ac:parameter ac:name="maxResults">{max_results}</ac:parameter>'
        )
        if columns:
            macro += (
                f'<ac:parameter ac:name="columns">{",".join(columns)}</ac:parameter>'
            )
        if server_id:
            macro += f'<ac:parameter ac:name="server">{server_id}</ac:parameter>'
        macro += "</ac:structured-macro>"
        return macro


class AdvancedContentBuilder:
    """Builder class for creating complex content structures."""

    def __init__(self):
        self._content = []
        self._formatting = AdvancedFormatting()

    def add_section(
        self, title: str, content: str, level: int = 2, collapsible: bool = False
    ) -> "AdvancedContentBuilder":
        """Add a section with optional collapsible behavior."""
        self._content.append(f"<h{level}>{title}</h{level}>")
        if collapsible:
            self._content.append(
                self._formatting.collapsible_section("Details", content)
            )
        else:
            self._content.append(content)
        return self

    def add_columns(self, contents: List[str]) -> "AdvancedContentBuilder":
        """Add a multi-column layout."""
        if len(contents) == 2:
            self._content.append(
                self._formatting.two_column_layout(contents[0], contents[1])
            )
        elif len(contents) == 3:
            self._content.append(self._formatting.three_column_layout(contents))
        else:
            raise ValueError("Only 2 or 3 column layouts are supported")
        return self

    def add_info_cards(self, cards: List[Dict[str, str]]) -> "AdvancedContentBuilder":
        """Add multiple info cards in a grid layout."""
        for card in cards:
            self._content.append(
                self._formatting.info_card(
                    card["title"],
                    card["content"],
                    card.get("icon", "info"),
                    card.get("color", "#0052CC"),
                )
            )
        return self

    def add_tabbed_section(
        self, tabs: List[Dict[str, str]]
    ) -> "AdvancedContentBuilder":
        """Add a tabbed content section."""
        self._content.append(self._formatting.tabbed_content(tabs))
        return self

    def add_chart_section(
        self, title: str, charts: List[Dict[str, Union[str, Dict]]]
    ) -> "AdvancedContentBuilder":
        """Add a section with multiple charts."""
        self._content.append(f"<h3>{title}</h3>")
        for chart in charts:
            self._content.append(
                self._formatting.chart(
                    chart["type"],
                    chart["data"],
                    chart.get("title", ""),
                    chart.get("width", 600),
                    chart.get("height", 400),
                )
            )
        return self

    def build(self) -> str:
        """Build the final content string."""
        return "\n".join(self._content)
