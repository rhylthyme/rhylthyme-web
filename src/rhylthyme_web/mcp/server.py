#!/usr/bin/env python3
"""
Rhylthyme MCP Server - Exposes schedule visualization as MCP tools.

Usage:
    python -m rhylthyme_web.mcp.server

Or add to Claude Desktop config:
    {
        "mcpServers": {
            "rhylthyme": {
                "command": "python",
                "args": ["-m", "rhylthyme_web.mcp.server"]
            }
        }
    }
"""

import json
import tempfile
import os
import sys
from typing import Any

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Rhylthyme imports
try:
    from rhylthyme_web.web.web_visualizer import generate_dag_visualization
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False

# Importer imports
try:
    from rhylthyme_importers import ImporterRegistry, TheMealDBImporter
    IMPORTERS_AVAILABLE = True
except ImportError:
    IMPORTERS_AVAILABLE = False


# Tool schema for visualize_program
VISUALIZE_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "program": {
            "type": "object",
            "description": "Complete Rhylthyme program JSON for schedule visualization",
            "properties": {
                "programId": {
                    "type": "string",
                    "description": "Unique identifier for the program (e.g., 'thanksgiving-dinner')"
                },
                "name": {
                    "type": "string",
                    "description": "Human-readable name for the program"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of what the program does"
                },
                "version": {
                    "type": "string",
                    "description": "Program version (e.g., '1.0.0')"
                },
                "environmentType": {
                    "type": "string",
                    "description": "Type of environment (e.g., 'kitchen', 'laboratory', 'manufacturing')"
                },
                "actors": {
                    "type": "integer",
                    "description": "Number of available workers/operators"
                },
                "startTrigger": {
                    "type": "object",
                    "description": "How the program starts",
                    "properties": {
                        "type": {"type": "string", "enum": ["manual", "offset", "scheduled"]},
                        "offsetSeconds": {"type": "integer"}
                    }
                },
                "tracks": {
                    "type": "array",
                    "description": "Array of parallel execution tracks",
                    "items": {
                        "type": "object",
                        "properties": {
                            "trackId": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "steps": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "stepId": {"type": "string"},
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "startTrigger": {"type": "object"},
                                        "duration": {"type": "object"},
                                        "task": {"type": "string"}
                                    },
                                    "required": ["stepId", "name", "duration", "task"]
                                }
                            }
                        },
                        "required": ["trackId", "name", "steps"]
                    }
                },
                "resourceConstraints": {
                    "type": "array",
                    "description": "Resource usage limits",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string"},
                            "maxConcurrent": {"type": "integer"},
                            "description": {"type": "string"}
                        },
                        "required": ["task", "maxConcurrent"]
                    }
                }
            },
            "required": ["programId", "name", "tracks"]
        }
    },
    "required": ["program"]
}

# Tool schema for importing from TheMealDB
IMPORT_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["search", "import", "random"],
            "description": "Action: 'search' to find recipes, 'import' to import by ID, 'random' for a random recipe"
        },
        "query": {
            "type": "string",
            "description": "Search query (for search) or meal ID (for import)"
        }
    },
    "required": ["action"]
}


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("rhylthyme")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        tools = [
            Tool(
                name="visualize_program",
                description="""Creates an interactive schedule visualization from a Rhylthyme program.

Rhylthyme is a JSON-based format for describing real-time coordinated workflows with:
- Multiple parallel tracks of work
- Resource constraints (e.g., max 2 stove burners at once)
- Timing dependencies between steps
- Variable and fixed duration steps

Use this tool when you've designed a complete scheduling program and want to visualize it.

Example use cases:
- Coordinating a multi-course dinner so everything is hot at serving time
- Laboratory experiment workflows with equipment constraints
- Manufacturing processes with resource limits
- Event coordination with multiple parallel activities

Duration values are in seconds:
- 1 minute = 60 seconds
- 5 minutes = 300 seconds
- 30 minutes = 1800 seconds
- 1 hour = 3600 seconds""",
                inputSchema=VISUALIZE_TOOL_SCHEMA
            )
        ]

        if IMPORTERS_AVAILABLE:
            tools.append(Tool(
                name="themealdb_import",
                description="""Import cooking recipes from TheMealDB to create Rhylthyme cooking schedules.

IMPORTANT: Use this tool whenever a user asks about cooking, recipes, or meal preparation.

Actions:
- "search": Search for recipes by name (e.g., "chicken curry", "lasagna")
- "import": Import a specific recipe by meal ID to get a full cooking schedule
- "random": Get a random recipe for inspiration

Workflow:
1. First use action="search" with query="dish name" to find recipes
2. Tell the user what you found from TheMealDB
3. Use action="import" with the meal ID to get the full cooking schedule
4. Use visualize_program to display the schedule

Always tell the user you are using TheMealDB as the source.""",
                inputSchema=IMPORT_TOOL_SCHEMA
            ))

        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""

        # Handle TheMealDB import tool
        if name == "themealdb_import":
            if not IMPORTERS_AVAILABLE:
                return [TextContent(type="text", text="Error: Importers not available. Install rhylthyme-importers.")]

            action = arguments.get("action")
            query = arguments.get("query", "")

            try:
                importer = TheMealDBImporter()

                if action == "search":
                    if not query:
                        return [TextContent(type="text", text="Error: Search query required")]
                    results = importer.search(query)
                    if not results:
                        return [TextContent(type="text", text=f"No recipes found on TheMealDB for '{query}'")]

                    response = f"Found {len(results)} recipe(s) on TheMealDB for '{query}':\n\n"
                    for r in results[:5]:
                        response += f"- **{r['name']}** (ID: {r['id']})\n"
                        if r.get('description'):
                            response += f"  {r['description']}\n"
                    response += "\nUse action='import' with the meal ID to get the full cooking schedule."
                    return [TextContent(type="text", text=response)]

                elif action == "import":
                    if not query:
                        return [TextContent(type="text", text="Error: Meal ID required for import")]
                    result = importer.import_from_url(query)
                    if not result.success:
                        return [TextContent(type="text", text=f"Error importing from TheMealDB: {result.error}")]

                    program = result.program
                    track_count = len(program.get("tracks", []))
                    step_count = sum(len(t.get("steps", [])) for t in program.get("tracks", []))
                    ingredients = program.get("metadata", {}).get("ingredients", [])

                    response = f"Successfully imported **{program['name']}** from TheMealDB!\n\n"
                    response += f"**Cooking Schedule:**\n"
                    response += f"- {track_count} track(s), {step_count} step(s)\n"
                    if ingredients:
                        response += f"- {len(ingredients)} ingredients\n"
                    response += f"\n**Tracks:**\n"
                    for t in program.get("tracks", []):
                        response += f"- {t['name']}: {len(t['steps'])} steps\n"
                    response += "\nUse visualize_program with this program to display the interactive schedule."
                    response += f"\n\n```json\n{json.dumps(program, indent=2)}\n```"
                    return [TextContent(type="text", text=response)]

                elif action == "random":
                    meal = importer.get_random_meal()
                    if not meal:
                        return [TextContent(type="text", text="Error: Failed to get random meal from TheMealDB")]

                    result = importer.import_from_url(meal.get("idMeal"))
                    if not result.success:
                        return [TextContent(type="text", text=f"Error importing: {result.error}")]

                    program = result.program
                    response = f"Random recipe from TheMealDB: **{program['name']}**!\n\n"
                    response += f"Category: {program.get('metadata', {}).get('category', 'Unknown')}\n"
                    response += f"Cuisine: {program.get('metadata', {}).get('area', 'Unknown')}\n\n"
                    response += "Use visualize_program with this program to display the cooking schedule."
                    response += f"\n\n```json\n{json.dumps(program, indent=2)}\n```"
                    return [TextContent(type="text", text=response)]

                else:
                    return [TextContent(type="text", text=f"Unknown action: {action}. Use 'search', 'import', or 'random'.")]

            except Exception as e:
                return [TextContent(type="text", text=f"Error with TheMealDB: {str(e)}")]

        if name != "visualize_program":
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        if not VISUALIZER_AVAILABLE:
            return [TextContent(
                type="text",
                text="Error: Rhylthyme visualizer not available. Install rhylthyme-web package."
            )]

        program = arguments.get("program")
        if not program:
            return [TextContent(type="text", text="Error: No program provided")]

        try:
            # Validate required fields
            if not program.get("programId"):
                return [TextContent(type="text", text="Error: program must have 'programId'")]
            if not program.get("name"):
                return [TextContent(type="text", text="Error: program must have 'name'")]
            if not program.get("tracks"):
                return [TextContent(type="text", text="Error: program must have 'tracks'")]

            # Save program to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                json.dump(program, tmp)
                tmp_path = tmp.name

            # Generate visualization
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as out:
                output_path = out.name

            generate_dag_visualization(tmp_path, output_path, open_browser=False)

            # Read the generated HTML
            with open(output_path, 'r') as f:
                html_content = f.read()

            # Clean up temp files
            os.unlink(tmp_path)
            os.unlink(output_path)

            # Calculate some stats for the response
            track_count = len(program.get("tracks", []))
            step_count = sum(len(t.get("steps", [])) for t in program.get("tracks", []))

            return [TextContent(
                type="text",
                text=f"""Successfully created visualization for "{program.get('name')}"!

Program stats:
- {track_count} parallel track(s)
- {step_count} total step(s)
- Environment: {program.get('environmentType', 'general')}

The interactive schedule visualization has been generated. Users can:
- See the timeline with all parallel tracks
- View step dependencies and resource constraints
- Start/pause the schedule simulation
- Download the program JSON

Visualization HTML length: {len(html_content)} characters"""
            )]

        except Exception as e:
            return [TextContent(type="text", text=f"Error generating visualization: {str(e)}")]

    return server


async def main():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("Error: MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
        sys.exit(1)

    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
