import json
import sys
from pathlib import Path

from mcp.server import MCPServer

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.load_data import load_data
from db.queries import (
    summarize_transmission_lines,
    summarize_wildlife_lands,
    find_wildlife_hit_by_transmission,
    calculate_overlap_km,
)

mcp = MCPServer("TransmissionAssistant")

con = load_data()


def json_safe(value):
    """
    Convert database/Python values into MCP-safe JSON values.
    """
    return json.loads(json.dumps(value, default=str))


# ---------------------------------------------------------------------------
# DATA TOOLS
# ---------------------------------------------------------------------------


@mcp.tool()
def get_summary_transmission_lines():
    """Return a summary of transmission lines."""
    return json_safe(summarize_transmission_lines(con))


@mcp.tool()
def get_summary_wildlife_lands():
    """Return a summary of wildlife lands."""
    return json_safe(summarize_wildlife_lands(con))


@mcp.tool()
def get_list_of_hit_wildlife_from_transmission_lines():
    """Return wildlife lands intersected by transmission lines."""
    return json_safe(find_wildlife_hit_by_transmission(con))


@mcp.tool()
def calculate_transmission_lines_intersection_with_wildlife():
    """Return total transmission-line overlap in kilometers."""
    return json_safe(calculate_overlap_km(con))


@mcp.tool()
def get_summary_chart_instructions():
    """
    Return instructions and live data for a summary chart.
    """

    transmission = json_safe(summarize_transmission_lines(con))

    wildlife = json_safe(summarize_wildlife_lands(con))

    overlap_km = json_safe(calculate_overlap_km(con))

    result = {
        "chart_type": "grouped_bar_with_overlap_badge",
        "title": ("San Joaquin Valley — " "Transmission Lines vs Wildlife Lands"),
        "subtitle": "Summary with intersection overlay",
        "data": {
            "transmission": transmission,
            "wildlife": wildlife,
            "overlap_km": overlap_km,
        },
        "colors": {
            "transmission": "#E07B39",
            "wildlife": "#3A7D44",
            "overlap": "#8B2FC9",
            "background": "#0F1117",
            "surface": "#1C1F2A",
            "text_primary": "#F0F0F0",
            "text_muted": "#7A8099",
            "grid_line": "#2A2D3A",
            "chart_background": "#161926",
        },
        "fonts": {
            "display": "IBM Plex Mono",
            "body": "Inter",
            "source": (
                "https://fonts.googleapis.com/css2?"
                "family=IBM+Plex+Mono:wght@400;600"
                "&family=Inter:wght@400;500;600"
                "&display=swap"
            ),
        },
        "layout": {
            "sections": [
                {
                    "id": "kpi_row",
                    "type": "kpi_cards",
                    "cards": [
                        {
                            "label": "Total Transmission Lines",
                            "unit": "km",
                            "color_token": "transmission",
                        },
                        {
                            "label": "Total Wildlife Lands",
                            "unit": "km²",
                            "color_token": "wildlife",
                        },
                        {
                            "label": "Overlap",
                            "unit": "km",
                            "color_token": "overlap",
                        },
                    ],
                },
                {
                    "id": "bar_chart",
                    "type": "grouped_bar",
                    "description": (
                        "Horizontal grouped bar chart using the "
                        "categories returned by the summary data."
                    ),
                    "x_axis_label": "Length / Area",
                    "legend": [
                        "Transmission Lines (km)",
                        "Wildlife Lands (km²)",
                    ],
                },
                {
                    "id": "overlap_band",
                    "type": "highlighted_stat",
                    "color_token": "overlap",
                },
            ],
        },
        "interactions": {
            "bar_hover": ("Show exact value and percentage of total."),
            "kpi_animation": ("Count from 0 to the final value over 1.2 seconds."),
        },
        "notes": [
            "Return a single self-contained HTML file.",
            "Use inline CSS and JavaScript.",
            "Use the supplied Google Fonts.",
            "Use only the supplied color tokens.",
            "Use a dark background.",
            "Make the chart responsive.",
        ],
    }

    return json_safe(result)


@mcp.tool()
def get_arcgis_map_instructions():
    """
    Return instructions and live data for an ArcGIS Maps SDK
    for JavaScript 4.29 map.
    """

    transmission = json_safe(summarize_transmission_lines(con))

    wildlife = json_safe(summarize_wildlife_lands(con))

    overlap_km = json_safe(calculate_overlap_km(con))

    hit_wildlife = json_safe(find_wildlife_hit_by_transmission(con))

    result = {
        "sdk": {
            "name": "ArcGIS Maps SDK for JavaScript",
            "version": "4.29",
            "cdn_css": ("https://js.arcgis.com/4.29/" "esri/themes/dark/main.css"),
            "cdn_js": ("https://js.arcgis.com/4.29/"),
        },
        "data": {
            "transmission": transmission,
            "wildlife": wildlife,
            "overlap_km": overlap_km,
            "hit_wildlife_count": len(hit_wildlife),
            "hit_wildlife_sample": hit_wildlife[:5],
        },
        "projection": {
            "geojson": "EPSG:4326",
            "coordinates": "longitude, latitude",
        },
        "map": {
            "basemap": "dark-gray-vector",
            "initial_view": {
                "center": [-119.7, 36.8],
                "zoom": 8,
            },
        },
        "endpoints": {
            "transmission_lines": ("http://127.0.0.1:8000/transmission_lines"),
            "wildlife_lands": ("http://127.0.0.1:8000/wildlife_lands"),
            "wildlife_transmission_overlap": (
                "http://127.0.0.1:8000/wildlife_lands_hit"
            ),
        },
        "layers": [
            {
                "id": "wildlife_lands",
                "label": "Wildlife Lands",
                "type": "GeoJSONLayer",
                "url": ("http://127.0.0.1:8000/" "wildlife_lands"),
            },
            {
                "id": "transmission_lines",
                "label": "Transmission Lines",
                "type": "GeoJSONLayer",
                "url": ("http://127.0.0.1:8000/" "transmission_lines"),
            },
            {
                "id": "overlap_highlight",
                "label": "Transmission–Wildlife Overlap",
                "type": "GeoJSONLayer",
                "url": ("http://127.0.0.1:8000/" "wildlife_lands_hit"),
            },
        ],
        "layer_order": [
            "wildlife_lands",
            "transmission_lines",
            "overlap_highlight",
        ],
        "zoom_to_layer": {
            "enabled": True,
            "buttons": [
                {
                    "id": "zoom_wildlife",
                    "label": "Wildlife Lands",
                    "layer_id": "wildlife_lands",
                },
                {
                    "id": "zoom_transmission",
                    "label": "Transmission Lines",
                    "layer_id": "transmission_lines",
                },
                {
                    "id": "zoom_overlap",
                    "label": "Overlap",
                    "layer_id": "overlap_highlight",
                },
            ],
            "behavior": [
                "Wait for layer.when().",
                "Use layer.fullExtent.",
                "Call view.goTo(layer.fullExtent).",
                "Use approximately 800ms animation.",
                "Do not use hard-coded bounds.",
                "Do not change layer visibility.",
                "Handle empty layers gracefully.",
            ],
        },
        "requirements": [
            "Return one self-contained HTML file.",
            "Use ArcGIS Maps SDK for JavaScript 4.29.",
            "Use require() with the AMD loader.",
            "Do not use ES modules.",
            "Use GeoJSONLayer.",
            "Use layer.when().",
            "Use view.when().",
            "Handle loading errors with catch().",
            "Use EPSG:4326 GeoJSON.",
            "Do not add authentication.",
            "Do not add custom headers.",
            "Use the supplied endpoints exactly.",
        ],
    }

    return json_safe(result)



@mcp.tool()
def get_maplibre_map_instructions():
    """
    Return instructions and live data for a MapLibre GL JS map.
    """

    transmission = json_safe(summarize_transmission_lines(con))

    wildlife = json_safe(summarize_wildlife_lands(con))

    overlap_km = json_safe(calculate_overlap_km(con))

    hit_wildlife = json_safe(find_wildlife_hit_by_transmission(con))

    result = {
        "map_library": {
            "name": "MapLibre GL JS",
            "version": "5.14.0",
            "cdn_js": (
                "https://unpkg.com/" "maplibre-gl@5.14.0/" "dist/maplibre-gl.js"
            ),
            "cdn_css": (
                "https://unpkg.com/" "maplibre-gl@5.14.0/" "dist/maplibre-gl.css"
            ),
        },
        "basemap": {
            "provider": "OpenFreeMap",
            "style_url": ("https://tiles.openfreemap.org/" "styles/dark"),
        },
        "projection": {
            "geojson": "EPSG:4326",
            "map": "mercator",
        },
        "data": {
            "transmission": transmission,
            "wildlife": wildlife,
            "overlap_km": overlap_km,
            "hit_wildlife_count": len(hit_wildlife),
            "hit_wildlife_sample": hit_wildlife[:5],
        },
        "map": {
            "initial_view": {
                "center": [-119.7, 36.8],
                "zoom": 8,
            },
            "fit_to_data": {
                "source": "transmission_lines",
                "padding": 50,
                "max_zoom": 12,
                "duration": 800,
            },
        },
        "sources": {
            "wildlife_lands": {
                "type": "geojson",
                "url": ("http://127.0.0.1:8000/" "wildlife_lands"),
            },
            "transmission_lines": {
                "type": "geojson",
                "url": ("http://127.0.0.1:8000/" "transmission_lines"),
            },
            "overlap": {
                "type": "geojson",
                "url": ("http://127.0.0.1:8000/" "wildlife_lands_hit"),
            },
        },
        "layers": {
            "wildlife_lands": {
                "type": "fill",
                "source": "wildlife_lands",
                "paint": {
                    "fill-color": "#3A7D44",
                    "fill-opacity": 0.35,
                    "fill-outline-color": "#3A7D44",
                },
            },
            "transmission_lines": {
                "type": "line",
                "source": "transmission_lines",
                "paint": {
                    "line-color": "#E07B39",
                    "line-width": 2,
                },
            },
            "overlap": {
                "type": "line",
                "source": "overlap",
                "paint": {
                    "line-color": "#8B2FC9",
                    "line-width": 3.5,
                    "line-dasharray": [2, 2],
                },
            },
        },
        "layer_order": [
            "wildlife_lands",
            "transmission_lines",
            "overlap",
        ],
        "zoom_to_layer": {
            "enabled": True,
            "buttons": [
                {
                    "id": "zoom_all",
                    "label": "All Layers",
                    "sources": [
                        "wildlife_lands",
                        "transmission_lines",
                        "overlap",
                    ],
                },
                {
                    "id": "zoom_wildlife",
                    "label": "Wildlife Lands",
                    "source": "wildlife_lands",
                },
                {
                    "id": "zoom_transmission",
                    "label": "Transmission Lines",
                    "source": "transmission_lines",
                },
                {
                    "id": "zoom_overlap",
                    "label": "Overlap",
                    "source": "overlap",
                },
            ],
            "behavior": [
                "Wait for the map to load.",
                "Read bounds from loaded GeoJSON data.",
                "Use map.fitBounds().",
                "Do not use hard-coded bounds.",
                "Use 50px padding.",
                "Use 800ms animation.",
                "Do not change layer visibility.",
                "Handle empty sources gracefully.",
            ],
        },
        "popups": {
            "wildlife_lands": [
                "PROP_NAME",
                "PROP_TYPE",
                "REGION",
                "ACCESS",
                "Shape__Are",
            ],
            "transmission_lines": [
                "Name",
                "kV",
                "Owner",
                "Status",
                "Circuit",
                "Type",
                "Length_Mil",
            ],
            "overlap": [
                "wildlife_property_name",
                "wildlife_property_type",
                "wildlife_region",
                "transmission_name",
                "transmission_kv",
                "transmission_owner",
                "transmission_status",
                "transmission_circuit",
                "transmission_type",
            ],
        },
        "requirements": [
            "Return one self-contained HTML file.",
            "Use MapLibre GL JS 5.14.0.",
            "Use OpenFreeMap dark style.",
            "Do not use Mapbox.",
            "Do not require an API key.",
            "Use the supplied GeoJSON URLs exactly.",
            "Use EPSG:4326 GeoJSON.",
            "Wait for GeoJSON sources before calculating bounds.",
            "Fit initially to transmission lines.",
            "Create the Zoom to Layer control.",
            "Include All Layers, Wildlife Lands, Transmission Lines, and Overlap.",
            "Calculate bounds dynamically.",
            "Use map.fitBounds().",
            "Add popups.",
            "Add legend.",
            "Add navigation, fullscreen, and scale controls.",
            "Handle loading errors.",
            "Log source errors.",
            "Do not use ArcGIS.",
        ],
    }

    return json_safe(result)
