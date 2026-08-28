import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

TRANSMISSION_FILE = (
    BASE_DIR / "data" / "transmission_lines" / "TransmissionLine_CEC.shp"
)

WILDLIFE_FILE = (
    BASE_DIR / "data" / "public_lands" / "CDFW_Public_Access_Lands_[ds3077].shp"
)

SOURCE_CRS = "EPSG:3310"
WEB_CRS = "EPSG:4326"


def load_data() -> duckdb.DuckDBPyConnection:
    """Load spatial datasets into DuckDB using EPSG:3310 as the canonical CRS."""

    con = duckdb.connect()

    con.sql("INSTALL spatial")
    con.sql("LOAD spatial")

    con.sql(f"""
        CREATE OR REPLACE VIEW transmission_lines AS
        SELECT
            *,
            ST_Transform(geom, '{SOURCE_CRS}') AS geom_3310
        FROM ST_Read('{TRANSMISSION_FILE}')
    """)

    con.sql(f"""
        CREATE OR REPLACE VIEW wildlife_lands AS
        SELECT
            *,
            ST_Transform(geom, '{SOURCE_CRS}') AS geom_3310
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
    print("\n=== TRANSMISSION GEOMETRY ===")

    con.sql("""
        SELECT typeof(geom)
        FROM transmission_lines
        LIMIT 1
    """).show()

    print("\n=== WILDLIFE GEOMETRY ===")

    con.sql("""
        SELECT typeof(geom)
        FROM wildlife_lands
        LIMIT 1
    """).show()


if __name__ == "__main__":
    con = load_data()
    show_schema(con)
    show_geometry_types(con)
