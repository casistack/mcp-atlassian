"""Draw.io Integration Handler for Confluence Cloud.

This module provides integration with draw.io (Diagrams) app installed in Confluence Cloud.
It handles diagram creation, updating, and retrieval through the Confluence Cloud REST API.
"""

import base64
import json
import logging
from typing import Dict, Optional, Union, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("mcp-atlassian")


class DiagramType(Enum):
    """Supported diagram types."""

    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    ER = "er"
    UML = "uml"
    NETWORK = "network"
    MINDMAP = "mindmap"
    ORG_CHART = "org"
    TIMELINE = "timeline"


class ShapeType(Enum):
    """Available shape types for diagram elements."""

    # Network Diagram Shapes
    SERVER = "mxgraph.networks.server"
    CLOUD = "mxgraph.networks.cloud"
    FIREWALL = "mxgraph.networks.firewall"
    ROUTER = "mxgraph.networks.router"
    SWITCH = "mxgraph.networks.switch"
    WIRELESS_ROUTER = "mxgraph.networks.wireless_router"
    DATABASE = "mxgraph.networks.database"
    USER = "mxgraph.networks.user"
    LAPTOP = "mxgraph.networks.laptop"
    PC = "mxgraph.networks.pc"
    MOBILE = "mxgraph.networks.mobile"
    STORAGE = "mxgraph.networks.storage"
    LOAD_BALANCER = "mxgraph.networks.load_balancer"
    PROXY = "mxgraph.networks.proxy"
    WAN = "mxgraph.networks.wan"
    SATELLITE = "mxgraph.networks.satellite"
    VPN = "mxgraph.networks.vpn"
    IDS = "mxgraph.networks.ids"
    RACK = "mxgraph.networks.rack"
    WIRELESS_ACCESS_POINT = "mxgraph.networks.wireless_access_point"

    # Flowchart Shapes
    PROCESS = "process"
    DECISION = "rhombus"
    START_END = "ellipse"
    INPUT_OUTPUT = "parallelogram"
    DOCUMENT = "document"
    MANUAL_INPUT = "manualInput"
    PREPARATION = "hexagon"
    DATA = "cylinder"
    PREDEFINED_PROCESS = "mxgraph.flowchart.predefined_process"
    STORED_DATA = "mxgraph.flowchart.stored_data"
    INTERNAL_STORAGE = "mxgraph.flowchart.internal_storage"
    MERGE = "mxgraph.flowchart.merge"
    EXTRACT = "mxgraph.flowchart.extract"
    DELAY = "mxgraph.flowchart.delay"
    SUMMING_POINT = "mxgraph.flowchart.summing_point"
    OR = "mxgraph.flowchart.or"
    DISPLAY = "mxgraph.flowchart.display"

    # Container and Cloud Shapes
    CONTAINER = "mxgraph.kubernetes.container"
    POD = "mxgraph.kubernetes.pod"
    SERVICE = "mxgraph.kubernetes.service"
    VOLUME = "mxgraph.kubernetes.volume"
    DEPLOYMENT = "mxgraph.kubernetes.deploy"
    STATEFUL_SET = "mxgraph.kubernetes.sts"
    CONFIG_MAP = "mxgraph.kubernetes.cm"
    SECRET = "mxgraph.kubernetes.secret"
    INGRESS = "mxgraph.kubernetes.ing"

    # AWS Shapes
    AWS_CLOUD = "mxgraph.aws4.cloud"
    AWS_EC2 = "mxgraph.aws4.ec2"
    AWS_S3 = "mxgraph.aws4.s3"
    AWS_RDS = "mxgraph.aws4.rds"
    AWS_LAMBDA = "mxgraph.aws4.lambda"
    AWS_VPC = "mxgraph.aws4.vpc"
    AWS_SUBNET = "mxgraph.aws4.subnet"
    AWS_AUTO_SCALING = "mxgraph.aws4.auto_scaling"
    AWS_ELB = "mxgraph.aws4.elastic_load_balancing"
    AWS_ECS = "mxgraph.aws4.ecs"
    AWS_EKS = "mxgraph.aws4.eks"
    AWS_API_GATEWAY = "mxgraph.aws4.api_gateway"
    AWS_CLOUDFRONT = "mxgraph.aws4.cloudfront"
    AWS_ROUTE53 = "mxgraph.aws4.route_53"
    AWS_SQS = "mxgraph.aws4.sqs"
    AWS_SNS = "mxgraph.aws4.sns"

    # Azure Shapes
    AZURE_VM = "mxgraph.azure.virtual_machine"
    AZURE_APP_SERVICE = "mxgraph.azure.app_service"
    AZURE_SQL = "mxgraph.azure.sql_database"
    AZURE_STORAGE = "mxgraph.azure.storage"
    AZURE_FUNCTIONS = "mxgraph.azure.functions"
    AZURE_COSMOS_DB = "mxgraph.azure.cosmos_db"
    AZURE_KUBERNETES = "mxgraph.azure.aks"

    # GCP Shapes
    GCP_COMPUTE = "mxgraph.gcp.compute_engine"
    GCP_CLOUD_RUN = "mxgraph.gcp.cloud_run"
    GCP_GKE = "mxgraph.gcp.gke"
    GCP_CLOUD_SQL = "mxgraph.gcp.cloud_sql"
    GCP_CLOUD_STORAGE = "mxgraph.gcp.cloud_storage"
    GCP_BIGQUERY = "mxgraph.gcp.bigquery"

    # UML Shapes
    UML_CLASS = "mxgraph.uml.class"
    UML_INTERFACE = "mxgraph.uml.interface"
    UML_PACKAGE = "mxgraph.uml.package"
    UML_ACTOR = "mxgraph.uml.actor"
    UML_USE_CASE = "mxgraph.uml.useCase"
    UML_LIFELINE = "mxgraph.uml.lifeline"
    UML_ACTIVATION = "mxgraph.uml.activation"

    # General Shapes
    RECTANGLE = "rectangle"
    CIRCLE = "ellipse"
    DIAMOND = "rhombus"
    TRIANGLE = "triangle"
    HEXAGON = "hexagon"
    ACTOR = "actor"
    NOTE = "note"
    TEXT = "text"
    CARD = "card"
    STEP = "step"
    CUBE = "cube"
    CYLINDER = "cylinder"
    CLOUD = "cloud"
    DOCUMENT = "document"
    STAR = "star"


class ConnectorType(Enum):
    """Available connector types for linking elements."""

    STRAIGHT = "straight"
    CURVED = "curved"
    ORTHOGONAL = "orthogonal"
    BIDIRECTIONAL = "bidirectional"
    DASHED = "dashed"
    DOTTED = "dotted"
    ARROW = "arrow"
    DOUBLE_ARROW = "double_arrow"
    THICK_ARROW = "thickArrow"
    THIN_ARROW = "thinArrow"
    ASYNC_ARROW = "async"
    SYNC_ARROW = "sync"
    AGGREGATION = "aggregation"
    COMPOSITION = "composition"
    INHERITANCE = "inheritance"
    IMPLEMENTATION = "implementation"
    DEPENDENCY = "dependency"
    CUSTOM = "custom"


@dataclass
class DiagramStyle:
    """Diagram styling options."""

    theme: str = "default"
    background: str = "#ffffff"
    grid: bool = True
    grid_size: int = 10
    grid_color: str = "#d0d0d0"
    connect: bool = True
    guides: bool = True
    page_width: int = 850
    page_height: int = 1100
    default_font_size: int = 12
    default_font_family: str = "Helvetica"
    line_color: str = "#000000"
    fill_color: str = "#ffffff"
    stroke_width: int = 2
    shadow: bool = True
    shadow_color: str = "#808080"
    shadow_opacity: float = 0.25
    shadow_offset_x: int = 2
    shadow_offset_y: int = 2
    zoom: float = 1.0
    math_enabled: bool = False
    sketch_style: bool = False


@dataclass
class ElementStyle:
    """Style options for individual diagram elements."""

    fill_color: str = "#ffffff"
    fill_opacity: float = 1.0
    gradient: bool = False
    gradient_color: str = ""
    gradient_direction: str = "north"
    stroke_color: str = "#000000"
    stroke_width: int = 2
    stroke_opacity: float = 1.0
    opacity: float = 1.0
    font_size: int = 12
    font_family: str = "Helvetica"
    font_color: str = "#000000"
    font_style: str = "normal"  # normal, italic, bold, bolditalic
    text_align: str = "center"  # left, center, right
    text_opacity: float = 1.0
    shadow: bool = True
    shadow_color: str = "#808080"
    shadow_opacity: float = 0.25
    shadow_offset_x: int = 2
    shadow_offset_y: int = 2
    dashed: bool = False
    dash_pattern: str = "3 3"
    rounded: bool = False
    rounded_radius: int = 10
    glass: bool = False
    rotation: int = 0
    flip_horizontal: bool = False
    flip_vertical: bool = False
    aspect_ratio: bool = True
    auto_size: bool = False
    resize: bool = True
    connectable: bool = True
    placeholder: str = ""
    tooltip: str = ""
    link: str = ""
    image_align: str = "center"
    image_vertical_align: str = "middle"
    spacing_top: int = 0
    spacing_right: int = 0
    spacing_bottom: int = 0
    spacing_left: int = 0


class DiagramData:
    """Handles draw.io diagram data encoding and decoding."""

    def __init__(
        self,
        diagram_type: DiagramType,
        content: Dict,
        style: Optional[DiagramStyle] = None,
    ):
        """Initialize diagram data.

        Args:
            diagram_type: Type of diagram to create
            content: Dictionary containing diagram content specification
            style: Optional styling parameters
        """
        self.diagram_type = diagram_type
        self.content = content
        self.style = style or DiagramStyle()
        self._xml_content = None

    def to_base64(self) -> str:
        """Convert diagram content to base64 encoded string."""
        if not self._xml_content:
            self._generate_xml()
        return base64.b64encode(self._xml_content.encode("utf-8")).decode("utf-8")

    @classmethod
    def from_base64(cls, base64_str: str) -> "DiagramData":
        """Create DiagramData instance from base64 encoded string.

        Args:
            base64_str: Base64 encoded diagram data

        Returns:
            DiagramData instance
        """
        xml_content = base64.b64decode(base64_str).decode("utf-8")
        # Parse XML to extract diagram type and content
        # This is a placeholder for actual XML parsing logic
        return cls(
            diagram_type=DiagramType.FLOWCHART,  # Default type
            content={},  # Parsed content would go here
        )

    def _generate_xml(self) -> None:
        """Generate draw.io compatible XML content.

        This is where we'll implement the logic to convert our content
        specification into draw.io's XML format.
        """
        # This is a simplified example - actual implementation would be more complex
        xml_template = f"""
        <mxfile host="Confluence" modified="{self._get_timestamp()}" agent="MCP Atlassian">
            <diagram id="{self._generate_id()}" name="{self.diagram_type.value}">
                <mxGraphModel dx="1186" dy="764" grid="{str(self.style.grid).lower()}" 
                             guides="{str(self.style.guides).lower()}" connect="{str(self.style.connect).lower()}"
                             arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.style.page_width}" 
                             pageHeight="{self.style.page_height}" background="{self.style.background}">
                    <root>
                        <mxCell id="0"/>
                        <mxCell id="1" parent="0"/>
                        {self._content_to_xml()}
                    </root>
                </mxGraphModel>
            </diagram>
        </mxfile>
        """
        self._xml_content = xml_template.strip()

    def _content_to_xml(self) -> str:
        """Convert content dictionary to draw.io XML elements."""
        elements_xml = []

        # Process nodes/elements
        for element in self.content.get("elements", []):
            element_id = self._generate_id()
            diagram_element = DiagramElement(
                element_id=element_id,
                element_type=ShapeType(element["type"]),
                x=element.get("x", 0),
                y=element.get("y", 0),
                width=element.get("width", 120),
                height=element.get("height", 60),
                label=element.get("label", ""),
                style=(
                    ElementStyle(**element.get("style", {}))
                    if element.get("style")
                    else None
                ),
            )
            elements_xml.append(diagram_element.to_xml())

            # Store ID mapping for connectors
            element["_id"] = element_id

        # Process connections
        for connection in self.content.get("connections", []):
            source_element = next(
                e
                for e in self.content["elements"]
                if e.get("id") == connection["source"]
            )
            target_element = next(
                e
                for e in self.content["elements"]
                if e.get("id") == connection["target"]
            )

            connector = DiagramConnector(
                connector_id=self._generate_id(),
                source_id=source_element["_id"],
                target_id=target_element["_id"],
                connector_type=ConnectorType(connection.get("type", "straight")),
                label=connection.get("label", ""),
                style=(
                    ElementStyle(**connection.get("style", {}))
                    if connection.get("style")
                    else None
                ),
                waypoints=connection.get("waypoints"),
            )
            elements_xml.append(connector.to_xml())

        return "\n".join(elements_xml)

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in draw.io format."""
        from datetime import datetime

        return datetime.utcnow().isoformat()

    @staticmethod
    def _generate_id() -> str:
        """Generate unique diagram ID."""
        import uuid

        return str(uuid.uuid4())


class DiagramElement:
    """Represents a single element in the diagram."""

    def __init__(
        self,
        element_id: str,
        element_type: ShapeType,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str = "",
        style: Optional[ElementStyle] = None,
        parent_id: str = "1",
    ):
        self.id = element_id
        self.type = element_type
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.style = style or ElementStyle()
        self.parent_id = parent_id

    def to_xml(self) -> str:
        """Convert element to draw.io XML format."""
        style_str = self._build_style_string()

        return f"""
            <mxCell id="{self.id}" value="{self.label}" style="{style_str}"
                    parent="{self.parent_id}" vertex="1">
                <mxGeometry x="{self.x}" y="{self.y}" width="{self.width}" 
                           height="{self.height}" as="geometry"/>
            </mxCell>
        """.strip()

    def _build_style_string(self) -> str:
        """Build the style string for the element."""
        style_parts = [
            f"shape={self.type.value}",
            f"fillColor={self.style.fill_color}",
            f"strokeColor={self.style.stroke_color}",
            f"strokeWidth={self.style.stroke_width}",
            f"fontSize={self.style.font_size}",
            f"fontFamily={self.style.font_family}",
            f"fontColor={self.style.font_color}",
            f"opacity={self.style.opacity}",
        ]

        if self.style.shadow:
            style_parts.append("shadow=1")
        if self.style.dashed:
            style_parts.append("dashed=1")
        if self.style.rounded:
            style_parts.append("rounded=1")
        if self.style.glass:
            style_parts.append("glass=1")

        return ";".join(style_parts)


class DiagramConnector:
    """Represents a connector between two elements."""

    def __init__(
        self,
        connector_id: str,
        source_id: str,
        target_id: str,
        connector_type: ConnectorType,
        label: str = "",
        style: Optional[ElementStyle] = None,
        waypoints: Optional[List[Tuple[int, int]]] = None,
        parent_id: str = "1",
    ):
        self.id = connector_id
        self.source_id = source_id
        self.target_id = target_id
        self.type = connector_type
        self.label = label
        self.style = style or ElementStyle()
        self.waypoints = waypoints or []
        self.parent_id = parent_id

    def to_xml(self) -> str:
        """Convert connector to draw.io XML format."""
        style_str = self._build_style_string()
        geometry = self._build_geometry() if self.waypoints else ""

        return f"""
            <mxCell id="{self.id}" value="{self.label}" style="{style_str}"
                    parent="{self.parent_id}" source="{self.source_id}" 
                    target="{self.target_id}" edge="1">
                {geometry}
            </mxCell>
        """.strip()

    def _build_style_string(self) -> str:
        """Build the style string for the connector."""
        style_parts = [
            f"edgeStyle={self.type.value}",
            f"strokeColor={self.style.stroke_color}",
            f"strokeWidth={self.style.stroke_width}",
            f"fontSize={self.style.font_size}",
            f"fontFamily={self.style.font_family}",
            f"fontColor={self.style.font_color}",
            f"opacity={self.style.opacity}",
        ]

        if self.type in [ConnectorType.ARROW, ConnectorType.DOUBLE_ARROW]:
            style_parts.append("endArrow=classic")
        if self.type == ConnectorType.DOUBLE_ARROW:
            style_parts.append("startArrow=classic")
        if self.style.dashed:
            style_parts.append("dashed=1")

        return ";".join(style_parts)

    def _build_geometry(self) -> str:
        """Build geometry XML for custom waypoints."""
        if not self.waypoints:
            return ""

        points = "".join(
            f'<mxPoint x="{x}" y="{y}" as="point"/>' for x, y in self.waypoints
        )
        return f'<mxGeometry relative="1" as="geometry">{points}</mxGeometry>'


class DrawIOHandler:
    """Handles draw.io operations in Confluence Cloud."""

    def __init__(self, confluence_client):
        """Initialize draw.io handler.

        Args:
            confluence_client: Initialized Confluence client
        """
        self.confluence = confluence_client
        self.base_url = confluence_client.url

    async def create_diagram(
        self,
        page_id: str,
        diagram_name: str,
        diagram_type: Union[DiagramType, str],
        content: Dict,
        style: Optional[DiagramStyle] = None,
    ) -> Dict:
        """Create a new draw.io diagram in a Confluence page.

        Args:
            page_id: Confluence page ID
            diagram_name: Name of the diagram
            diagram_type: Type of diagram to create
            content: Dictionary containing diagram specification
            style: Optional styling parameters

        Returns:
            Dictionary containing the created diagram information
        """
        # Convert string to enum if necessary
        if isinstance(diagram_type, str):
            diagram_type = DiagramType(diagram_type.lower())

        # Create diagram data
        diagram = DiagramData(diagram_type, content, style)

        # Generate macro content
        macro_content = self._create_drawio_macro(
            diagram_name=diagram_name, diagram_data=diagram.to_base64()
        )

        try:
            # Get current page content
            page_content = await self.confluence.get_page_content(page_id)
            if not page_content:
                raise ValueError(f"Could not get content for page {page_id}")

            # Append diagram macro to page content
            new_content = f"{page_content}\n{macro_content}"

            # Update page
            result = await self.confluence.update_page(
                page_id=page_id, title=None, body=new_content  # Keep existing title
            )

            if not result:
                raise ValueError("Failed to update page with diagram")

            return {
                "success": True,
                "page_id": page_id,
                "diagram_name": diagram_name,
                "diagram_type": diagram_type.value,
                "macro_id": self._generate_macro_id(),
            }

        except Exception as e:
            logger.error(f"Error creating diagram: {str(e)}")
            return {"success": False, "error": str(e)}

    async def update_diagram(
        self,
        page_id: str,
        macro_id: str,
        content: Dict,
        style: Optional[DiagramStyle] = None,
    ) -> Dict:
        """Update an existing draw.io diagram.

        Args:
            page_id: Confluence page ID
            macro_id: ID of the diagram macro to update
            content: New diagram content
            style: Optional new styling parameters

        Returns:
            Dictionary containing the update result
        """
        try:
            # Get current diagram data
            current_data = await self._get_diagram_data(page_id, macro_id)
            if not current_data:
                raise ValueError(f"Could not find diagram with macro ID {macro_id}")

            # Create new diagram data
            diagram = DiagramData(
                diagram_type=current_data.diagram_type,
                content=content,
                style=style or current_data.style,
            )

            # Update macro content
            result = await self._update_macro_content(
                page_id=page_id, macro_id=macro_id, diagram_data=diagram.to_base64()
            )

            if not result:
                raise ValueError("Failed to update diagram")

            return {"success": True, "page_id": page_id, "macro_id": macro_id}

        except Exception as e:
            logger.error(f"Error updating diagram: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_diagram(self, page_id: str, macro_id: str) -> Optional[Dict]:
        """Retrieve diagram data and metadata.

        Args:
            page_id: Confluence page ID
            macro_id: ID of the diagram macro

        Returns:
            Dictionary containing diagram data and metadata, or None if not found
        """
        try:
            diagram_data = await self._get_diagram_data(page_id, macro_id)
            if not diagram_data:
                return None

            return {
                "diagram_type": diagram_data.diagram_type.value,
                "content": diagram_data.content,
                "style": vars(diagram_data.style),
                "macro_id": macro_id,
            }

        except Exception as e:
            logger.error(f"Error retrieving diagram: {str(e)}")
            return None

    def _create_drawio_macro(self, diagram_name: str, diagram_data: str) -> str:
        """Create draw.io macro content.

        Args:
            diagram_name: Name of the diagram
            diagram_data: Base64 encoded diagram data

        Returns:
            Confluence storage format macro string
        """
        macro_id = self._generate_macro_id()
        return f"""
        <ac:structured-macro ac:name="drawio" ac:schema-version="1" ac:macro-id="{macro_id}">
            <ac:parameter ac:name="diagramName">{diagram_name}</ac:parameter>
            <ac:parameter ac:name="simpleViewer">false</ac:parameter>
            <ac:parameter ac:name="diagramData">{diagram_data}</ac:parameter>
            <ac:parameter ac:name="width">auto</ac:parameter>
            <ac:parameter ac:name="height">auto</ac:parameter>
        </ac:structured-macro>
        """.strip()

    async def _get_diagram_data(
        self, page_id: str, macro_id: str
    ) -> Optional[DiagramData]:
        """Retrieve diagram data from a macro.

        Args:
            page_id: Confluence page ID
            macro_id: ID of the diagram macro

        Returns:
            DiagramData instance or None if not found
        """
        try:
            # Get page content
            page_content = await self.confluence.get_page_content(page_id)
            if not page_content:
                return None

            # Find the draw.io macro with matching ID
            import xml.etree.ElementTree as ET

            root = ET.fromstring(page_content)

            # Find draw.io macro with matching ID
            macro = root.find(
                f".//ac:structured-macro[@ac:name='drawio'][@ac:macro-id='{macro_id}']",
                {"ac": "http://www.atlassian.com/schema/confluence/4/ac/"},
            )

            if macro is None:
                return None

            # Extract diagram data
            diagram_data = macro.find(
                ".//ac:parameter[@ac:name='diagramData']",
                {"ac": "http://www.atlassian.com/schema/confluence/4/ac/"},
            )

            if diagram_data is None or not diagram_data.text:
                return None

            # Parse the diagram data
            return DiagramData.from_base64(diagram_data.text)

        except Exception as e:
            logger.error(f"Error retrieving diagram data: {str(e)}")
            return None

    async def _update_macro_content(
        self, page_id: str, macro_id: str, diagram_data: str
    ) -> bool:
        """Update diagram macro content.

        Args:
            page_id: Confluence page ID
            macro_id: ID of the diagram macro
            diagram_data: New base64 encoded diagram data

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Get page content
            page_content = await self.confluence.get_page_content(page_id)
            if not page_content:
                return False

            # Parse the content
            import xml.etree.ElementTree as ET

            root = ET.fromstring(page_content)

            # Find draw.io macro with matching ID
            macro = root.find(
                f".//ac:structured-macro[@ac:name='drawio'][@ac:macro-id='{macro_id}']",
                {"ac": "http://www.atlassian.com/schema/confluence/4/ac/"},
            )

            if macro is None:
                return False

            # Update diagram data
            diagram_param = macro.find(
                ".//ac:parameter[@ac:name='diagramData']",
                {"ac": "http://www.atlassian.com/schema/confluence/4/ac/"},
            )

            if diagram_param is None:
                return False

            diagram_param.text = diagram_data

            # Convert back to string
            new_content = ET.tostring(root, encoding="unicode")

            # Update the page
            result = await self.confluence.update_page(
                page_id=page_id, title=None, body=new_content  # Keep existing title
            )

            return bool(result)

        except Exception as e:
            logger.error(f"Error updating macro content: {str(e)}")
            return False

    @staticmethod
    def _generate_macro_id() -> str:
        """Generate unique macro ID."""
        import uuid

        return f"drawio-{str(uuid.uuid4())}"
