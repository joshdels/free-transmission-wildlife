import duckdb


def summarize_transmission_lines(con: duckdb.DuckDBPyConnection) -> dict:
    """Summarize transmission lines."""

    result = con.sql("""
        SELECT
            COUNT(*)               AS total_lines,
            COUNT(DISTINCT Owner)  AS unique_owners,
            COUNT(DISTINCT kV)     AS unique_voltages,
            COUNT(DISTINCT Status) AS unique_statuses,
            COUNT(DISTINCT Type)   AS unique_types,
            SUM(Length_Mil)        AS total_length_miles,
            SUM(Length_Mil) * 1.60934 AS total_length_km
        FROM transmission_lines
    """).fetchone()

    return {
        "total_lines": result[0],
        "unique_owners": result[1],
        "unique_voltages": result[2],
        "unique_statuses": result[3],
        "unique_types": result[4],
        "total_length_miles": round(result[5], 3),
        "total_length_km": round(result[6], 3),
    }


def summarize_wildlife_lands(con: duckdb.DuckDBPyConnection) -> dict:
    """Summarize wildlife lands."""

    result = con.sql("""
        SELECT
            COUNT(*)                    AS total_parcels,
            COUNT(DISTINCT PROP_TYPE)   AS unique_property_types,
            COUNT(DISTINCT REGION)      AS unique_regions,
            SUM(Shape__Are)             AS total_area_m2,
            SUM(Shape__Are) / 1_000_000 AS total_area_km2,
            SUM(Shape__Are) / 4046.856  AS total_area_acres,
            AVG(Shape__Are)             AS avg_area_m2,
            MIN(Shape__Are)             AS min_area_m2,
            MAX(Shape__Are)             AS max_area_m2
        FROM wildlife_lands
    """).fetchone()

    return {
        "total_parcels": result[0],
        "unique_property_types": result[1],
        "unique_regions": result[2],
        "total_area_m2": round(result[3], 3),
        "total_area_km2": round(result[4], 3),
        "total_area_acres": round(result[5], 3),
        "avg_area_m2": round(result[6], 3),
        "min_area_m2": round(result[7], 3),
        "max_area_m2": round(result[8], 3),
    }


def find_wildlife_hit_by_transmission(con: duckdb.DuckDBPyConnection) -> list[dict]:
    """Find wildlife lands intersected by transmission lines."""

    cols = [
        c
        for c in con.sql("SELECT * FROM wildlife_lands LIMIT 0").columns
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
