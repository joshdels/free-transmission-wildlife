from mcp.server import MCPServer
from db.load_data import load_data
from db.queries import get_transmission_lines, find_intersections, calculate_overlap_km

mcp = MCPServer("TransmissionAssistant")


@mcp.tool()
def get_transmission():
    pass
