import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.ai.mcp_client import MCPClient

# ============================================================
# ENVIRONMENT
# ============================================================

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY is not set!")


# ============================================================
# OPENROUTER / OPENAI CLIENT
# ============================================================

client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
)


# ============================================================
# MCP CLIENT
# ============================================================

mcp = MCPClient()


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "openrouter/free"

MAX_TOOL_ROUNDS = 10


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a GIS AI assistant.

You can answer normal questions and you also have access
to GIS analysis and visualization tools through MCP.

Your job is to understand the user's intent and use the
appropriate MCP tool when GIS data or GIS visualization
is required.


============================================================
GENERAL TOOL RULE
============================================================

Use MCP tools whenever the user's request requires:

- GIS data
- transmission line information
- wildlife land information
- intersections
- spatial analysis
- GIS statistics
- charts based on GIS data
- maps
- interactive GIS visualizations
- generated HTML GIS visualizations


============================================================
MAP TOOL ROUTING
============================================================

IMPORTANT:

There are TWO different map-generation systems:

1. ArcGIS Maps SDK for JavaScript
2. MapLibre GL JS

You MUST select the correct MCP tool based on what the
user explicitly requests.


------------------------------------------------------------
ARCGIS
------------------------------------------------------------

If the user asks for:

- an ArcGIS map
- ArcGIS HTML
- an ArcGIS visualization
- an interactive ArcGIS map
- a downloadable ArcGIS map
- ArcGIS Maps SDK
- ESRI map
- ESRI visualization

you MUST call:

get_arcgis_map_instructions


After receiving the MCP result, generate the requested
complete HTML using ArcGIS Maps SDK for JavaScript.

DO NOT use MapLibre.


------------------------------------------------------------
MAPLIBRE
------------------------------------------------------------

If the user asks for:

- a MapLibre map
- MapLibre HTML
- a MapLibre visualization
- an interactive MapLibre map
- a downloadable MapLibre map
- a map using MapLibre
- visualize the GIS data using MapLibre

you MUST call:

get_maplibre_map_instructions


After receiving the MCP result, generate the requested
complete HTML using MapLibre GL JS.

DO NOT use ArcGIS.


============================================================
IMPORTANT DISTINCTION
============================================================

If the user asks:

"What is MapLibre?"

Answer the question normally.

If the user asks:

"Make a MapLibre map"

or:

"Give me MapLibre HTML"

or:

"How about MapLibre?"

when the conversation is already about generating a map,

interpret this as a MapLibre map-generation request and
call:

get_maplibre_map_instructions


Likewise, if the conversation is already about generating
an ArcGIS map and the user says:

"How about ArcGIS?"

interpret this as an ArcGIS map-generation request.


============================================================
ARCGIS IMPLEMENTATION RULES
============================================================

When generating ArcGIS HTML:

- Use ArcGIS Maps SDK for JavaScript.
- Use the SDK version specified by the MCP tool.
- Use the ArcGIS AMD require() loader.
- Use Map.
- Use MapView.
- Use GeoJSONLayer for GeoJSON data.
- Use the supplied GeoJSONLayer URLs.
- Use native ArcGIS widgets when specified.
- Do not use MapLibre.
- Do not use maplibre.
- Do not use map.addSource().
- Do not use MapLibre source objects.
- Do not use MapLibre layers.


============================================================
MAPLIBRE IMPLEMENTATION RULES
============================================================

When generating MapLibre HTML:

- Use the MapLibre version specified by the MCP tool.
- Use maplibre.Map.
- Use map.addSource().
- Use map.addLayer().
- Use GeoJSON sources.
- For MapLibre GeoJSON sources, use:

    {
        "type": "geojson",
        "data": "URL"
    }

- NEVER use "url" for a MapLibre GeoJSON source.
- Do not use GeoJSONLayer.
- Do not use ArcGIS Maps SDK.
- Do not use ArcGIS AMD require().


============================================================
HTML GENERATION
============================================================

When the user explicitly requests HTML for a chart or map:

1. Call the appropriate MCP instruction tool.
2. Read the MCP result carefully.
3. Generate ONE complete self-contained HTML document.
4. Include <!DOCTYPE html>.
5. Include all required CSS.
6. Include all required JavaScript.
7. Use the exact endpoints supplied by the MCP tool.
8. Follow the requested library exactly.
9. Do not substitute another mapping library.
10. Do not merely explain how to build the map.
11. Return the actual HTML.


============================================================
CHARTS
============================================================

If the user requests:

- a chart
- a summary chart
- an HTML chart
- a visualization of the summary statistics

call:

get_summary_chart_instructions


Then generate the requested HTML.


============================================================
GIS ANALYSIS
============================================================

For questions about actual GIS data, use the appropriate
MCP data-analysis tools.

Do not invent GIS values.

Use the values returned by MCP.


============================================================
NORMAL CONVERSATION
============================================================

If the user asks a general question that does not require
GIS data or a GIS operation, answer normally.

Do not call MCP tools unnecessarily.


============================================================
MCP RESULTS
============================================================

Treat MCP results as authoritative for:

- GIS values
- endpoints
- map configuration
- library versions
- visualization instructions
- layer definitions
- styling instructions


============================================================
FINAL RESPONSE
============================================================

For normal questions:
Return a concise human-readable answer.

For GIS analysis:
Return the relevant analysis.

For HTML generation:
Return the complete HTML document and nothing else
unless the application requires a short explanation.
"""


# ============================================================
# GET MCP TOOLS
# ============================================================


async def get_mcp_tools():
    """
    Connect to the MCP server if necessary and convert
    MCP tools into OpenAI/OpenRouter-compatible definitions.
    """

    # Connect only once
    if mcp.session is None:
        await mcp.connect()

    mcp_tools = await mcp.list_tools()

    tools = []

    for tool in mcp_tools:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
        )

    print()
    print("========================================")
    print("AVAILABLE MCP TOOLS")
    print("========================================")

    for tool in tools:
        print("-", tool["function"]["name"])

    print("========================================")
    print()

    return tools


# ============================================================
# ASK AI
# ============================================================


async def ask_ai(
    message: str,
    on_tool_result=None,
    conversation_history=None,
) -> str:
    """
    Send a user message to the AI.

    The AI can:

    1. Answer normally.
    2. Call one or more MCP tools.
    3. Receive MCP results.
    4. Generate a final response or HTML document.

    conversation_history:
        Optional list of previous OpenAI-compatible messages.

    on_tool_result:
        Optional async callback used by the WebSocket layer.
    """

    # --------------------------------------------------------
    # GET MCP TOOLS
    # --------------------------------------------------------

    tools = await get_mcp_tools()

    # --------------------------------------------------------
    # BUILD CONVERSATION
    # --------------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    # Add previous conversation if supplied
    if conversation_history:
        messages.extend(conversation_history)

    # Add current user message
    messages.append(
        {
            "role": "user",
            "content": message,
        }
    )

    # --------------------------------------------------------
    # MCP / AI LOOP
    # --------------------------------------------------------

    for round_number in range(MAX_TOOL_ROUNDS):

        print()
        print("========================================")
        print(f"AI ROUND {round_number + 1}")
        print("========================================")

        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        # ----------------------------------------------------
        # CASE 1:
        # AI DOES NOT REQUEST A TOOL
        # ----------------------------------------------------

        if not assistant_message.tool_calls:

            content = assistant_message.content or ""

            print()
            print("AI FINAL RESPONSE:")
            print(content)
            print()

            return content

        # ----------------------------------------------------
        # CASE 2:
        # AI REQUESTED TOOL(S)
        # ----------------------------------------------------

        print()
        print(f"AI requested " f"{len(assistant_message.tool_calls)} MCP tool(s)")

        # ----------------------------------------------------
        # PRESERVE ASSISTANT TOOL-CALL MESSAGE
        # ----------------------------------------------------

        assistant_tool_message = {
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [],
        }

        for tool_call in assistant_message.tool_calls:

            assistant_tool_message["tool_calls"].append(
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
            )

        messages.append(assistant_tool_message)

        # ----------------------------------------------------
        # EXECUTE MCP TOOLS
        # ----------------------------------------------------

        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            # -----------------------------------------------
            # PARSE ARGUMENTS
            # -----------------------------------------------

            raw_arguments = tool_call.function.arguments or "{}"

            try:
                arguments = json.loads(raw_arguments)

            except json.JSONDecodeError as e:

                print()
                print("ERROR: Invalid tool arguments")
                print("Tool:", tool_name)
                print("Arguments:", raw_arguments)
                print()

                raise ValueError(
                    f"Invalid arguments for MCP tool " f"{tool_name}: {e}"
                ) from e

            # -----------------------------------------------
            # LOG TOOL REQUEST
            # -----------------------------------------------

            print()
            print("----------------------------------------")
            print("MCP TOOL REQUEST")
            print("----------------------------------------")
            print("Tool:", tool_name)
            print("Arguments:", arguments)
            print("----------------------------------------")

            # -----------------------------------------------
            # CALL MCP
            # -----------------------------------------------

            try:

                result = await mcp.call_tool(
                    tool_name,
                    arguments,
                )

            except Exception as e:

                print()
                print("----------------------------------------")
                print("MCP TOOL ERROR")
                print("----------------------------------------")
                print("Tool:", tool_name)
                print("Error:", repr(e))
                print("----------------------------------------")
                print()

                # Give the error back to the AI
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            {
                                "error": str(e),
                                "tool": tool_name,
                            }
                        ),
                    }
                )

                continue

            # -----------------------------------------------
            # LOG MCP RESULT
            # -----------------------------------------------

            print()
            print("----------------------------------------")
            print("MCP RESULT")
            print("----------------------------------------")
            print("Tool:", tool_name)
            print(result)
            print("----------------------------------------")

            # -----------------------------------------------
            # SEND TOOL RESULT TO FRONTEND
            # -----------------------------------------------

            if on_tool_result:

                await on_tool_result(
                    tool_name,
                    arguments,
                    result,
                )

            # -----------------------------------------------
            # GIVE RESULT BACK TO AI
            # -----------------------------------------------

            if isinstance(result, str):
                tool_content = result
            else:
                try:
                    tool_content = json.dumps(
                        result,
                        default=str,
                    )
                except Exception:
                    tool_content = str(result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_content,
                }
            )

        # ----------------------------------------------------
        # LOOP
        # ----------------------------------------------------

        print()
        print("Sending MCP results back to AI...")
        print()

    # --------------------------------------------------------
    # MAX TOOL ROUNDS REACHED
    # --------------------------------------------------------

    raise RuntimeError(
        f"AI exceeded the maximum number of MCP tool rounds " f"({MAX_TOOL_ROUNDS})."
    )
