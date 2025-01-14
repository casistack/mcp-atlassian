"""Draw.io Integration Handler for Confluence Cloud.

This module provides integration with draw.io (Diagrams) app installed in Confluence Cloud.
It handles diagram creation, updating, and retrieval through the Confluence Cloud REST API.
"""

import base64
import json
import logging
from typing import Dict, Optional, Union, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import xml.etree.ElementTree as ElementTree

# Configure logging
logger = logging.getLogger("mcp-atlassian")
logger.setLevel(logging.DEBUG)


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
    SIMPLE_CLOUD = "cloud"
    BASIC_DOCUMENT = "document2"
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
        try:
            xml_content = base64.b64decode(base64_str).decode("utf-8")
            logger.debug(f"Decoded XML content: {xml_content}")

            # Parse XML
            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml_content)

            # Get diagram type from the diagram name
            diagram = root.find("diagram")
            if diagram is None:
                raise ValueError("No diagram element found in XML")

            diagram_name = diagram.get("name", "flowchart")
            try:
                diagram_type = DiagramType(diagram_name)
            except ValueError:
                diagram_type = DiagramType.FLOWCHART  # Default to flowchart

            # Get model and root
            model = diagram.find("mxGraphModel")
            if model is None:
                raise ValueError("No mxGraphModel element found in XML")

            root_elem = model.find("root")
            if root_elem is None:
                raise ValueError("No root element found in XML")

            # Extract style from model attributes
            style = DiagramStyle(
                grid=model.get("grid", "1").lower() == "true",
                guides=model.get("guides", "1").lower() == "true",
                connect=model.get("connect", "1").lower() == "true",
                page_width=int(model.get("pageWidth", "850")),
                page_height=int(model.get("pageHeight", "1100")),
                background=model.get("background", "#ffffff"),
            )

            # Extract elements and connections
            elements = []
            connections = []
            id_map = {}  # Map internal IDs to user-provided IDs

            for cell in root_elem.findall("mxCell"):
                cell_id = cell.get("id")
                if cell_id in ("0", "1"):  # Skip root cells
                    continue

                geometry = cell.find("mxGeometry")
                if geometry is None:
                    continue

                style_str = cell.get("style", "")
                style_dict = dict(
                    s.split("=") for s in style_str.split(";") if "=" in s
                )

                if cell.get("edge") == "1":  # It's a connection
                    connections.append(
                        {
                            "source": id_map.get(cell.get("source")),
                            "target": id_map.get(cell.get("target")),
                            "type": style_dict.get("edgeStyle", "straight"),
                            "label": cell.get("value", ""),
                            "style": {
                                "stroke_color": style_dict.get(
                                    "strokeColor", "#000000"
                                ),
                                "stroke_width": int(style_dict.get("strokeWidth", "2")),
                                "font_size": int(style_dict.get("fontSize", "12")),
                                "font_color": style_dict.get("fontColor", "#000000"),
                            },
                        }
                    )
                else:  # It's an element
                    shape_type = style_dict.get("shape", "rectangle")
                    try:
                        shape_type = next(t for t in ShapeType if t.value == shape_type)
                    except StopIteration:
                        shape_type = ShapeType.RECTANGLE

                    element = {
                        "id": f"element_{cell_id}",
                        "type": shape_type.value,
                        "x": int(geometry.get("x", "0")),
                        "y": int(geometry.get("y", "0")),
                        "width": int(geometry.get("width", "120")),
                        "height": int(geometry.get("height", "60")),
                        "label": cell.get("value", ""),
                        "style": {
                            "fill_color": style_dict.get("fillColor", "#ffffff"),
                            "stroke_color": style_dict.get("strokeColor", "#000000"),
                            "font_size": int(style_dict.get("fontSize", "12")),
                            "font_color": style_dict.get("fontColor", "#000000"),
                            "shadow": style_dict.get("shadow", "0") == "1",
                        },
                    }
                    elements.append(element)
                    id_map[cell_id] = element["id"]

            return cls(
                diagram_type=diagram_type,
                content={"elements": elements, "connections": connections},
                style=style,
            )

        except Exception as e:
            logger.error(f"Error parsing diagram data: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return cls(
                diagram_type=DiagramType.FLOWCHART,
                content={"elements": [], "connections": []},
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
        diagram_data: str,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new draw.io diagram in a Confluence page.

        Args:
            page_id: The ID of the page where the diagram will be created
            diagram_name: The name of the diagram
            diagram_data: Base64 encoded diagram data
            location: Optional location in the page to insert the diagram

        Returns:
            Dictionary containing success status and macro ID
        """
        try:
            # Get current page content
            page = self.confluence.get_page_by_id(
                page_id=page_id, expand="body.storage,version,space"
            )
            if not page:
                return {"success": False, "error": f"Page {page_id} not found"}

            content = page["body"]["storage"]["value"]

            # Create the draw.io macro
            macro_id = self._generate_macro_id()
            macro = self._create_drawio_macro(macro_id, diagram_name, diagram_data)

            # Insert the macro at the specified location or append to the end
            if location:
                # TODO: Implement location-based insertion
                new_content = content + "\n" + macro
            else:
                new_content = content + "\n" + macro

            # Update the page
            result = self.confluence.update_page(
                page_id=page_id,
                title=page["title"],
                body=new_content,
                type="page",
                representation="storage",
                minor_edit=False,
            )

            if result:
                return {"success": True, "macro_id": macro_id}
            return {"success": False, "error": "Failed to update page"}

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
            current_data = self._get_diagram_data(page_id, macro_id)
            if not current_data:
                raise ValueError(f"Could not find diagram with macro ID {macro_id}")

            # Create new diagram data
            diagram = DiagramData(
                diagram_type=current_data.diagram_type,
                content=content,
                style=style or current_data.style,
            )

            # Update macro content
            result = self._update_macro_content(
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
            diagram_data = self._get_diagram_data(page_id, macro_id)
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

    def _create_drawio_macro(
        self, macro_id: str, diagram_name: str, diagram_data: str
    ) -> str:
        """Create a draw.io macro with the given diagram data.

        Args:
            macro_id: Unique identifier for the macro
            diagram_name: Name of the diagram
            diagram_data: Base64 encoded diagram data

        Returns:
            String containing the draw.io macro XML
        """
        return (
            f'<ac:structured-macro ac:name="drawio" ac:schema-version="1" ac:macro-id="{macro_id}">'
            f'<ac:parameter ac:name="diagramName">{diagram_name}</ac:parameter>'
            f'<ac:parameter ac:name="contentType">application/vnd.jgraph.mxfile</ac:parameter>'
            f'<ac:parameter ac:name="width">100%</ac:parameter>'
            f'<ac:parameter ac:name="height">auto</ac:parameter>'
            f'<ac:parameter ac:name="simple">false</ac:parameter>'
            f'<ac:parameter ac:name="zoom">1.0</ac:parameter>'
            f'<ac:parameter ac:name="border">1</ac:parameter>'
            f'<ac:parameter ac:name="diagramData">{diagram_data}</ac:parameter>'
            "</ac:structured-macro>"
        )

    def _get_diagram_data(self, page_id: str, macro_id: str) -> Optional[DiagramData]:
        """Get diagram data from a macro."""
        try:
            # Get page content with macro rendered output
            page = self.confluence.get_page_by_id(
                page_id=page_id,
                expand="body.storage,version,space,body.view,macroRenderedOutput",
            )
            if not page:
                logger.error(f"Page {page_id} not found")
                return None

            page_content = page["body"]["storage"]["value"]
            logger.debug(f"Raw page content: {page_content}")

            # Define all possible namespaces
            namespaces = {
                "ac": "http://www.atlassian.com/schema/confluence/4/ac/",
                "ri": "http://www.atlassian.com/schema/confluence/4/ri/",
                "at": "http://www.atlassian.com/schema/confluence/4/at/",
                "default": "http://www.atlassian.com/schema/confluence/4/default/",
            }

            # Register namespaces for output
            for prefix, uri in namespaces.items():
                ElementTree.register_namespace(prefix, uri)

            # Clean up XML content to handle namespace issues
            # Replace default namespace with ac namespace
            page_content = page_content.replace(
                'xmlns="http://www.atlassian.com/schema/confluence/4/ac/"',
                'xmlns:ac="http://www.atlassian.com/schema/confluence/4/ac/"',
            )
            page_content = page_content.replace(
                'xmlns="http://www.atlassian.com/schema/confluence/4/ri/"',
                'xmlns:ri="http://www.atlassian.com/schema/confluence/4/ri/"',
            )
            page_content = page_content.replace(
                'xmlns="http://www.atlassian.com/schema/confluence/4/at/"',
                'xmlns:at="http://www.atlassian.com/schema/confluence/4/at/"',
            )

            logger.debug(f"Cleaned page content: {page_content}")

            try:
                root = ElementTree.fromstring(f"<root>{page_content}</root>")
                logger.debug(f"Successfully parsed XML root")
                logger.debug(
                    f"Root element: {ElementTree.tostring(root, encoding='unicode', method='xml')}"
                )
            except ElementTree.ParseError as e:
                logger.error(f"Failed to parse XML: {str(e)}")
                return None

            # Find all structured macros first
            all_macros = root.findall(".//ac:structured-macro", namespaces)
            logger.debug(f"Found {len(all_macros)} total macros")

            # Log details of each macro
            for i, m in enumerate(all_macros):
                logger.debug(f"Macro {i + 1}:")
                logger.debug(f"  Name: {m.get('{{{}}}name'.format(namespaces['ac']))}")
                logger.debug(
                    f"  ID: {m.get('{{{}}}macro-id'.format(namespaces['ac']))}"
                )
                logger.debug(
                    f"  Full XML: {ElementTree.tostring(m, encoding='unicode', method='xml')}"
                )

            # Try multiple XPath patterns to find the macro
            xpath_patterns = [
                f".//ac:structured-macro[@ac:macro-id='{macro_id}' and @ac:name='drawio']",
                f".//structured-macro[@macro-id='{macro_id}' and @name='drawio']",
                f".//*[local-name()='structured-macro'][@*[local-name()='macro-id']='{macro_id}' and @*[local-name()='name']='drawio']",
            ]

            macro = None
            for xpath in xpath_patterns:
                logger.debug(f"Trying XPath pattern: {xpath}")
                macro = root.find(xpath, namespaces)
                if macro is not None:
                    logger.debug(f"Found macro using pattern: {xpath}")
                    break

            if macro is not None:
                logger.debug(
                    f"Found target macro: {ElementTree.tostring(macro, encoding='unicode', method='xml')}"
                )

                # Try multiple patterns to find diagram data
                diagram_data = None
                param_patterns = [
                    ".//ac:parameter[@ac:name='diagramData']",
                    ".//parameter[@name='diagramData']",
                    ".//*[local-name()='parameter'][@*[local-name()='name']='diagramData']",
                ]

                for pattern in param_patterns:
                    logger.debug(f"Trying parameter pattern: {pattern}")
                    diagram_data = macro.find(pattern, namespaces)
                    if diagram_data is not None and diagram_data.text:
                        logger.debug(f"Found diagram data using pattern: {pattern}")
                        break

                if diagram_data is not None and diagram_data.text:
                    logger.debug(
                        f"Found diagram data: {diagram_data.text[:100]}..."
                    )  # Log first 100 chars
                    return DiagramData.from_base64(diagram_data.text)
                else:
                    logger.error("Diagram data parameter not found or empty in macro")
                    # Log all parameters in the macro
                    params = macro.findall(".//ac:parameter", namespaces)
                    logger.debug(f"Found {len(params)} parameters in macro:")
                    for p in params:
                        logger.debug(
                            f"  Parameter name: {p.get('{{{}}}name'.format(namespaces['ac']))}"
                        )
                        logger.debug(
                            f"  Parameter value: {p.text[:100] if p.text else 'None'}"
                        )
            else:
                logger.error(f"Macro with ID {macro_id} not found")
                # Log available macros for debugging
                macros = root.findall(
                    ".//ac:structured-macro[@ac:name='drawio']", namespaces
                )
                logger.debug(f"Available drawio macros: {len(macros)}")
                for m in macros:
                    logger.debug(
                        f"  Macro ID: {m.get('{{{}}}macro-id'.format(namespaces['ac']))}"
                    )

            return None

        except Exception as e:
            logger.error(f"Error getting diagram data: {str(e)}")
            logger.debug("Full error details:", exc_info=True)
            return None

    def _update_macro_content(
        self,
        page_id: str,
        macro_id: str,
        diagram_data: str,
    ) -> bool:
        """Update the content of a draw.io macro."""
        try:
            # Get page content with macro rendered output
            page = self.confluence.get_page_by_id(
                page_id=page_id,
                expand="body.storage,version,space,body.view,macroRenderedOutput",
            )
            if not page:
                logger.error(f"Page {page_id} not found")
                return False

            page_content = page["body"]["storage"]["value"]
            logger.debug(f"Page content: {page_content}")

            # Define all possible namespaces
            namespaces = {
                "ac": "http://www.atlassian.com/schema/confluence/4/ac/",
                "ri": "http://www.atlassian.com/schema/confluence/4/ri/",
                "at": "http://www.atlassian.com/schema/confluence/4/at/",
                "default": "http://www.atlassian.com/schema/confluence/4/default/",
            }

            # Register namespaces for output
            for prefix, uri in namespaces.items():
                ElementTree.register_namespace(prefix, uri)

            # Clean up XML content to handle namespace issues
            # Replace default namespace with ac namespace
            page_content = page_content.replace(
                'xmlns="http://www.atlassian.com/schema/confluence/4/ac/"',
                'xmlns:ac="http://www.atlassian.com/schema/confluence/4/ac/"',
            )
            page_content = page_content.replace(
                'xmlns="http://www.atlassian.com/schema/confluence/4/ri/"',
                'xmlns:ri="http://www.atlassian.com/schema/confluence/4/ri/"',
            )
            page_content = page_content.replace(
                'xmlns="http://www.atlassian.com/schema/confluence/4/at/"',
                'xmlns:at="http://www.atlassian.com/schema/confluence/4/at/"',
            )

            try:
                root = ElementTree.fromstring(f"<root>{page_content}</root>")
                logger.debug(f"Successfully parsed XML root")
            except ElementTree.ParseError as e:
                logger.error(f"Failed to parse XML: {str(e)}")
                return False

            # Try multiple XPath patterns to find the macro
            xpath_patterns = [
                f".//ac:structured-macro[@ac:macro-id='{macro_id}' and @ac:name='drawio']",
                f".//structured-macro[@macro-id='{macro_id}' and @name='drawio']",
                f".//*[local-name()='structured-macro'][@*[local-name()='macro-id']='{macro_id}' and @*[local-name()='name']='drawio']",
            ]

            macro = None
            for xpath in xpath_patterns:
                logger.debug(f"Trying XPath pattern: {xpath}")
                macro = root.find(xpath, namespaces)
                if macro is not None:
                    logger.debug(f"Found macro using pattern: {xpath}")
                    break

            if macro is not None:
                logger.debug(
                    f"Found target macro: {ElementTree.tostring(macro, encoding='unicode', method='xml')}"
                )

                # Try multiple patterns to find diagram data parameter
                diagram_data_param = None
                param_patterns = [
                    ".//ac:parameter[@ac:name='diagramData']",
                    ".//parameter[@name='diagramData']",
                    ".//*[local-name()='parameter'][@*[local-name()='name']='diagramData']",
                ]

                for pattern in param_patterns:
                    logger.debug(f"Trying parameter pattern: {pattern}")
                    diagram_data_param = macro.find(pattern, namespaces)
                    if diagram_data_param is not None:
                        logger.debug(
                            f"Found diagram data parameter using pattern: {pattern}"
                        )
                        break

                if diagram_data_param is not None:
                    diagram_data_param.text = diagram_data
                    logger.debug(
                        f"Updated diagram data: {diagram_data_param.text[:100]}..."
                    )  # Log first 100 chars

                    # Convert back to string, excluding the root element
                    updated_content = "".join(
                        ElementTree.tostring(child, encoding="unicode", method="xml")
                        for child in root
                    )
                    logger.debug(
                        f"Updated content: {updated_content[:500]}..."
                    )  # Log first 500 chars

                    # Update the page
                    result = self.confluence.update_page(
                        page_id=page_id,
                        title=page["title"],
                        body=updated_content,
                        minor_edit=False,
                    )

                    return result is not None
                else:
                    logger.error("Diagram data parameter not found in macro")
            else:
                logger.error(f"Macro with ID {macro_id} not found")
                # Log available macros for debugging
                macros = root.findall(
                    ".//ac:structured-macro[@ac:name='drawio']", namespaces
                )
                logger.debug(f"Available drawio macros: {len(macros)}")
                for m in macros:
                    logger.debug(
                        f"  Macro ID: {m.get('{{{}}}macro-id'.format(namespaces['ac']))}"
                    )

            return False

        except Exception as e:
            logger.error(f"Error updating macro content: {str(e)}")
            logger.debug("Full error details:", exc_info=True)
            return False

    @staticmethod
    def _generate_macro_id() -> str:
        """Generate unique macro ID."""
        import uuid

        return f"drawio-{str(uuid.uuid4())}"
