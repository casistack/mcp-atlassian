"""Draw.io tool definitions and handlers for the MCP Atlassian server."""

import logging
from typing import Sequence
from mcp.types import TextContent, Tool

from ..draw_io_handler import (
    DiagramType,
    ShapeType,
    ConnectorType,
    DiagramStyle,
    ElementStyle,
)

logger = logging.getLogger("mcp-atlassian")

TOOL_CATEGORY = "📊 Diagrams"


def get_draw_io_tools() -> list[Tool]:
    """Get the list of draw.io related tools."""
    return [
        Tool(
            name="create_diagram",
            description="Create a new draw.io diagram in a Confluence page with support for network diagrams, flowcharts, cloud architecture, and more.",
            category=TOOL_CATEGORY,
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Confluence page ID where the diagram will be created",
                    },
                    "diagram_name": {
                        "type": "string",
                        "description": "Name of the diagram",
                    },
                    "diagram_type": {
                        "type": "string",
                        "description": "Type of diagram to create",
                        "enum": [t.value for t in DiagramType],
                    },
                    "elements": {
                        "type": "array",
                        "description": "Array of diagram elements/shapes",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Unique identifier for the element",
                                },
                                "type": {
                                    "type": "string",
                                    "description": "Type of shape/element",
                                    "enum": [t.value for t in ShapeType],
                                },
                                "x": {
                                    "type": "integer",
                                    "description": "X coordinate",
                                },
                                "y": {
                                    "type": "integer",
                                    "description": "Y coordinate",
                                },
                                "width": {
                                    "type": "integer",
                                    "description": "Width of the element",
                                    "default": 120,
                                },
                                "height": {
                                    "type": "integer",
                                    "description": "Height of the element",
                                    "default": 60,
                                },
                                "label": {
                                    "type": "string",
                                    "description": "Label/text for the element",
                                },
                                "style": {
                                    "type": "object",
                                    "description": "Style options for the element",
                                    "properties": {
                                        "fill_color": {"type": "string"},
                                        "stroke_color": {"type": "string"},
                                        "font_size": {"type": "integer"},
                                        "font_color": {"type": "string"},
                                        "shadow": {"type": "boolean"},
                                    },
                                },
                            },
                            "required": ["id", "type", "x", "y"],
                        },
                    },
                    "connections": {
                        "type": "array",
                        "description": "Array of connections between elements",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {
                                    "type": "string",
                                    "description": "ID of the source element",
                                },
                                "target": {
                                    "type": "string",
                                    "description": "ID of the target element",
                                },
                                "type": {
                                    "type": "string",
                                    "description": "Type of connector",
                                    "enum": [t.value for t in ConnectorType],
                                    "default": "straight",
                                },
                                "label": {
                                    "type": "string",
                                    "description": "Label for the connection",
                                },
                                "style": {
                                    "type": "object",
                                    "description": "Style options for the connector",
                                },
                                "waypoints": {
                                    "type": "array",
                                    "description": "Optional custom routing points",
                                    "items": {
                                        "type": "array",
                                        "minItems": 2,
                                        "maxItems": 2,
                                        "items": {"type": "integer"},
                                    },
                                },
                            },
                            "required": ["source", "target"],
                        },
                    },
                    "style": {
                        "type": "object",
                        "description": "Global diagram styling options",
                        "properties": {
                            "theme": {"type": "string"},
                            "background": {"type": "string"},
                            "grid": {"type": "boolean"},
                            "shadow": {"type": "boolean"},
                        },
                    },
                },
                "required": ["page_id", "diagram_name", "diagram_type", "elements"],
            },
            metadata={
                "icon": "📊",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="update_diagram",
            description="Update an existing draw.io diagram in a Confluence page.",
            category=TOOL_CATEGORY,
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Confluence page ID containing the diagram",
                    },
                    "macro_id": {
                        "type": "string",
                        "description": "ID of the diagram macro to update",
                    },
                    "elements": {
                        "type": "array",
                        "description": "Updated array of diagram elements",
                    },
                    "connections": {
                        "type": "array",
                        "description": "Updated array of connections",
                    },
                    "style": {
                        "type": "object",
                        "description": "Updated diagram styling",
                    },
                },
                "required": ["page_id", "macro_id", "elements"],
            },
            metadata={
                "icon": "✏️",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
        Tool(
            name="get_diagram",
            description="Retrieve an existing draw.io diagram's data and metadata.",
            category=TOOL_CATEGORY,
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Confluence page ID containing the diagram",
                    },
                    "macro_id": {
                        "type": "string",
                        "description": "ID of the diagram macro",
                    },
                },
                "required": ["page_id", "macro_id"],
            },
            metadata={
                "icon": "🔍",
                "status": "stable",
                "version": "1.0",
                "author": "MCP Atlassian Team",
            },
        ),
    ]


async def handle_draw_io_tools(
    name: str, arguments: dict, draw_io_handler
) -> Sequence[TextContent]:
    """Handle draw.io tool invocations.

    Args:
        name: Name of the tool being invoked
        arguments: Tool arguments
        draw_io_handler: Initialized DrawIOHandler instance

    Returns:
        Sequence of TextContent responses
    """
    try:
        if name == "create_diagram":
            result = await draw_io_handler.create_diagram(
                page_id=arguments["page_id"],
                diagram_name=arguments["diagram_name"],
                diagram_type=arguments["diagram_type"],
                content={
                    "elements": arguments["elements"],
                    "connections": arguments.get("connections", []),
                },
                style=(
                    DiagramStyle(**arguments.get("style", {}))
                    if arguments.get("style")
                    else None
                ),
            )

            if result.get("success"):
                return [
                    TextContent(
                        f"Successfully created diagram '{arguments['diagram_name']}' "
                        f"with macro ID {result['macro_id']}"
                    )
                ]
            else:
                return [
                    TextContent(
                        f"Failed to create diagram: {result.get('error', 'Unknown error')}"
                    )
                ]

        elif name == "update_diagram":
            result = await draw_io_handler.update_diagram(
                page_id=arguments["page_id"],
                macro_id=arguments["macro_id"],
                content={
                    "elements": arguments["elements"],
                    "connections": arguments.get("connections", []),
                },
                style=(
                    DiagramStyle(**arguments.get("style", {}))
                    if arguments.get("style")
                    else None
                ),
            )

            if result.get("success"):
                return [TextContent("Successfully updated diagram")]
            else:
                return [
                    TextContent(
                        f"Failed to update diagram: {result.get('error', 'Unknown error')}"
                    )
                ]

        elif name == "get_diagram":
            result = await draw_io_handler.get_diagram(
                page_id=arguments["page_id"],
                macro_id=arguments["macro_id"],
            )

            if result:
                return [
                    TextContent(
                        f"Retrieved diagram data:\n"
                        f"Type: {result['diagram_type']}\n"
                        f"Elements: {len(result['content'].get('elements', []))}\n"
                        f"Connections: {len(result['content'].get('connections', []))}"
                    )
                ]
            else:
                return [TextContent("Failed to retrieve diagram data")]

        else:
            return [TextContent(f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error handling draw.io tool {name}: {str(e)}")
        return [TextContent(f"Error processing request: {str(e)}")]
