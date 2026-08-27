import sys

from mcp.server import MCPServer
from pathlib import Path

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


@mcp.tool()
def get_summary_transmission_lines():
    """Gives a summary of transmission lines in California San Joaquin Valley"""
    return summarize_transmission_lines(con)


@mcp.tool()
def get_summary_wildlife_lands():
    """Gives a summary of wildlife lands in California San Joaquin Valley"""
    return summarize_wildlife_lands(con)


@mcp.tool()
def get_list_of_hit_wildlife_from_transmission_lines():
    """Gives a list of details of the wildlife from hit transmission lines"""
    return find_wildlife_hit_by_transmission(con)


@mcp.tool()
def calculate_transmission_lines_intersection_with_wildlife():
    """Total transmission lines in km of overlap with wildlife"""
    return calculate_overlap_km(con)
