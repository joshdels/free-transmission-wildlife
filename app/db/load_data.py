import duckdb

from pathlib import Path

TRANSMISSION_FILE = Path("data/transmission_lines/TransmissionLine_CEC.shp")
WILDLIFE_FILE = Path("data/public_lands/CDFW_Public_Access_Lands_[ds3077].shp")


def load_data() -> duckdb.DuckDBPyConnection:
    """Load both Shapefiles into DuckDB."""

    con = duckdb.connect()

    con.sql("INSTALL spatial")
    con.sql("LOAD spatial")

    con.sql(f"""
        CREATE VIEW transmission_lines AS
        SELECT *
        FROM ST_Read('{TRANSMISSION_FILE}')
    """)

    con.sql(f"""
        CREATE VIEW wildlife_lands AS
        SELECT *
        FROM ST_Read('{WILDLIFE_FILE}')
    """)

    return con


def show_schema(con: duckdb.DuckDBPyConnection) -> None:

    print("\n=== TRANSMISSION SCHEMA ===")

    con.sql("""
        DESCRIBE
        SELECT *
        FROM transmission_lines
    """).show()

    print("\n=== WILDLIFE SCHEMA ===")

    con.sql("""
        DESCRIBE
        SELECT *
        FROM wildlife_lands
    """).show()


def show_geometry_types(con: duckdb.DuckDBPyConnection) -> None:
    con.sql("""
        SELECT
            typeof(geom)
        FROM transmission_lines
        LIMIT 1
    """).show()

    print("\n=== WILDLIFE GEOMETRY ===")

    con.sql("""
        SELECT
            typeof(geom)
        FROM wildlife_lands
        LIMIT 1
    """).show()


if __name__ == "__main__":
    con = load_data()
    show_schema(con)
    show_geometry_types(con)
