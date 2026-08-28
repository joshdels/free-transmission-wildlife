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
        "title": "San Joaquin Valley — Transmission Lines vs Wildlife Lands",
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
            "bar_hover": "Show exact value and percentage of total.",
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

    The map should use the standard ArcGIS dark theme and native
    ArcGIS UI components, including the standard dark legend.
    """

    transmission = json_safe(summarize_transmission_lines(con))
    wildlife = json_safe(summarize_wildlife_lands(con))
    overlap_km = json_safe(calculate_overlap_km(con))
    hit_wildlife = json_safe(find_wildlife_hit_by_transmission(con))

    result = {
        "sdk": {
            "name": "ArcGIS Maps SDK for JavaScript",
            "version": "4.29",
            "cdn_css": "https://js.arcgis.com/4.29/esri/themes/dark/main.css",
            "cdn_js": "https://js.arcgis.com/4.29/",
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
            "ui": {
                "theme": "arcgis-dark",
                "use_standard_arcgis_theme": True,
                "use_native_arcgis_widgets": True,
            },
            "widgets": [
                "zoom",
                "compass",
                "home",
                "fullscreen",
                "scale_bar",
                "legend",
            ],
            "legend": {
                "type": "ArcGIS Legend widget",
                "use_native_widget": True,
                "theme": "dark",
                "position": "bottom-right",
            },
        },
        "layers": {
            "transmission_lines": {
                "type": "GeoJSONLayer",
                "title": "Transmission Lines",
                "url": ("http://127.0.0.1:8000/transmission_lines"),
                "renderer": {
                    "type": "simple",
                    "symbol": {
                        "type": "simple-line",
                        "color": "#E07B39",
                        "width": 2,
                    },
                },
            },
            "wildlife_lands": {
                "type": "GeoJSONLayer",
                "title": "Wildlife Lands",
                "url": ("http://127.0.0.1:8000/wildlife_lands"),
                "renderer": {
                    "type": "simple",
                    "symbol": {
                        "type": "simple-fill",
                        "color": [
                            58,
                            125,
                            68,
                            0.35,
                        ],
                        "outline": {
                            "color": "#3A7D44",
                            "width": 1,
                        },
                    },
                },
            },
            "overlap": {
                "type": "GeoJSONLayer",
                "title": "Transmission / Wildlife Overlap",
                "url": ("http://127.0.0.1:8000/wildlife_lands_hit"),
                "renderer": {
                    "type": "simple",
                    "symbol": {
                        "type": "simple-line",
                        "color": "#8B2FC9",
                        "width": 3.5,
                        "style": "dash",
                    },
                },
            },
        },
        "layer_order": [
            "wildlife_lands",
            "transmission_lines",
            "overlap",
        ],
        "endpoints": {
            "transmission_lines": ("http://127.0.0.1:8000/transmission_lines"),
            "wildlife_lands": ("http://127.0.0.1:8000/wildlife_lands"),
            "wildlife_transmission_overlap": (
                "http://127.0.0.1:8000/wildlife_lands_hit"
            ),
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
            # ArcGIS UI
            "Use the ArcGIS dark theme CSS.",
            "Use the standard ArcGIS dark UI styling.",
            "Use the native ArcGIS Legend widget.",
            "Place the Legend widget in the bottom-right.",
            "Do not create a custom HTML legend.",
            "Do not override the ArcGIS Legend widget styling.",
            "Do not create custom ArcGIS-style controls.",
            # Map behavior
            "Use the supplied initial center and zoom.",
            "Do not automatically fit the map to any layer.",
            "Do not calculate layer bounds for the initial view.",
            "Do not create Zoom to Layer buttons.",
            "Do not create a Zoom to All Layers button.",
            "Do not add custom layer zoom controls.",
            # Standard ArcGIS controls
            "Use the standard ArcGIS zoom control.",
            "Use the standard ArcGIS compass control.",
            "Use the standard ArcGIS home control.",
            "Use the standard ArcGIS fullscreen control.",
            "Use the standard ArcGIS scale bar.",
            "Use the standard ArcGIS Legend widget.",
            "Use the standard ArcGIS Popups",
            "Keep the ArcGIS interface visually native.",
            "Do not replace the standard ArcGIS widget design.",
            "Do not use MapLibre in the ArcGIS map.",
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
            "behavior": {
                "fit_to_data": False,
                "automatic_layer_zoom": False,
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
        "controls": {
            "navigation": True,
            "fullscreen": True,
            "scale": True,
            "legend": True,
        },
        "legend": {
            "type": "custom",
            "items": [
                {
                    "label": "Wildlife Lands",
                    "color": "#3A7D44",
                    "opacity": 0.35,
                    "type": "fill",
                },
                {
                    "label": "Transmission Lines",
                    "color": "#E07B39",
                    "type": "line",
                },
                {
                    "label": "Transmission / Wildlife Overlap",
                    "color": "#8B2FC9",
                    "type": "line",
                    "dashed": True,
                },
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
            "Use the supplied initial center and zoom.",
            "Do not automatically fit the map to any layer.",
            "Do not calculate bounds for the initial view.",
            "Do not create Zoom to Layer buttons.",
            "Do not create Zoom to All Layers buttons.",
            "Do not add custom layer zoom controls.",
            "Wait for GeoJSON sources to load before interacting with them.",
            "Add popups for feature information.",
            "Add the supplied legend.",
            "Add navigation controls.",
            "Add fullscreen control.",
            "Add scale control.",
            "Handle loading errors.",
            "Log source errors.",
            "Do not use ArcGIS.",
        ],
    }

    return json_safe(result)
