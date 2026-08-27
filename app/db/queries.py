import duckdb


def summarize_transmission_lines(con: duckdb.DuckDBPyConnection) -> dict:
    """Summarize transmission lines."""

    result = con.sql("""
        SELECT
            COUNT(*)              AS total_lines,
            COUNT(DISTINCT Owner) AS unique_owners,
            COUNT(DISTINCT kV)    AS unique_voltages,
            SUM(Length_Mil)       AS total_length_miles,
            SUM(Length_Mil) * 1.60934 AS total_length_km
        FROM transmission_lines
    """).fetchone()

    return {
        "total_lines":       result[0],
        "unique_owners":     result[1],
        "unique_voltages":   result[2],
        "total_length_miles": round(result[3], 3),
        "total_length_km":   round(result[4], 3),
    }


def find_wildlife_hit_by_transmission(con: duckdb.DuckDBPyConnection) -> list[dict]:
    """Find wildlife lands intersected by transmission lines."""

    cols = [
        c for c in con.sql("SELECT * FROM wildlife_lands LIMIT 0").columns
        if c != "geom"
    ]

    return con.sql(f"""
        SELECT DISTINCT {", ".join(f"w.{c}" for c in cols)}
        FROM wildlife_lands w
        JOIN transmission_lines t
            ON ST_Intersects(w.geom, t.geom)
    """).df().to_dict(orient="records")


def calculate_overlap_km(con: duckdb.DuckDBPyConnection) -> float:
    """Calculate total km of transmission lines overlapping wildlife lands."""
    result = con.sql("""
        SELECT
            SUM(
                ST_Length(
                    ST_Transform(
                        ST_Intersection(t.geom, w.geom),
                        'EPSG:3857',
                        'EPSG:3310'
                    )
                )
            ) / 1000.0
        FROM transmission_lines t
        JOIN wildlife_lands w
            ON ST_Intersects(t.geom, w.geom)
    """).fetchone()

    return round(result[0], 3)
