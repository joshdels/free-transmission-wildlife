import json
import duckdb

from .helper import swap_geojson_coordinates


def summarize_transmission_lines(
    con: duckdb.DuckDBPyConnection,
) -> dict:
    """Summarize transmission lines."""

    result = con.sql("""
        SELECT
            COUNT(*) AS total_lines,
            COUNT(DISTINCT Owner) AS unique_owners,
            COUNT(DISTINCT kV) AS unique_voltages,
            COUNT(DISTINCT Status) AS unique_statuses,
            COUNT(DISTINCT Type) AS unique_types,
            SUM(Length_Mil) AS total_length_miles,
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


def summarize_wildlife_lands(
    con: duckdb.DuckDBPyConnection,
) -> dict:
    """Summarize wildlife lands."""

    result = con.sql("""
        SELECT
            COUNT(*) AS total_parcels,
            COUNT(DISTINCT PROP_TYPE) AS unique_property_types,
            COUNT(DISTINCT REGION) AS unique_regions,
            SUM(Shape__Are) AS total_area_m2,
            SUM(Shape__Are) / 1_000_000 AS total_area_km2,
            SUM(Shape__Are) / 4046.856 AS total_area_acres,
            AVG(Shape__Are) AS avg_area_m2,
            MIN(Shape__Are) AS min_area_m2,
            MAX(Shape__Are) AS max_area_m2
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


def find_wildlife_hit_by_transmission(
    con: duckdb.DuckDBPyConnection,
) -> list[dict]:
    """Find wildlife lands intersected by transmission lines."""

    cols = [
        column
        for column in con.sql("SELECT * FROM wildlife_lands LIMIT 0").columns
        if column != "geom"
    ]

    query = f"""
        SELECT DISTINCT
            {", ".join(f"w.{column}" for column in cols)}
        FROM wildlife_lands AS w
        JOIN transmission_lines AS t
            ON ST_Intersects(w.geom, t.geom)
    """

    return con.sql(query).df().to_dict(orient="records")


def calculate_overlap_km(
    con: duckdb.DuckDBPyConnection,
) -> float:
    """Calculate total transmission-line length overlapping wildlife lands."""

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
        FROM transmission_lines AS t
        JOIN wildlife_lands AS w
            ON ST_Intersects(t.geom, w.geom)
    """).fetchone()

    return round(result[0], 3)


def get_transmission_lines_data(
    con: duckdb.DuckDBPyConnection,
) -> dict:
    rows = con.sql("""
        SELECT
            Owner,
            kV,
            Status,
            Type,
            Length_Mil,
            ST_AsGeoJSON(geom) AS geometry,
        FROM transmission_lines
    """).fetchall()

    features = [
        {
            "type": "Feature",
            "geometry": swap_geojson_coordinates(json.loads(geometry)),
            "properties": {
                "Owner": owner,
                "kV": kv,
                "Status": status,
                "Type": line_type,
                "Length_Mil": length_mil,
            },
        }
        for (
            owner,
            kv,
            status,
            line_type,
            length_mil,
            geometry,
        ) in rows
    ]

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def get_wildlife_data(
    con: duckdb.DuckDBPyConnection,
) -> dict:
    cols = [
        column
        for column in con.sql("SELECT * FROM wildlife_lands LIMIT 0").columns
        if column != "geom"
    ]

    select_columns = ", ".join(f"w.{column}" for column in cols)

    query = f"""
        SELECT
            {select_columns},
            ST_AsGeoJSON(ST_Force2D(geom)) AS geometry,
        FROM wildlife_lands AS w
    """

    rows = con.sql(query).fetchall()

    features = []

    for row in rows:
        attributes = dict(zip(cols, row[:-1]))

        features.append(
            {
                "type": "Feature",
                "geometry": swap_geojson_coordinates(json.loads(row[-1])),
                "properties": attributes,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def get_wildlife_transmission_intersections(
    con: duckdb.DuckDBPyConnection,
) -> dict:
    """Return transmission/wildlife intersections as GeoJSON."""

    rows = con.sql("""
        SELECT
            w.OBJECTID AS wildlife_id,
            w.PROP_TYPE AS wildlife_property_type,
            w.PROP_NAME AS wildlife_property_name,
            w.LINK AS wildlife_link,
            w.ACCESS AS wildlife_access,
            w.REGION AS wildlife_region,
            w.Shape__Are AS wildlife_area_m2,

            t.OGC_FID AS transmission_id,
            t.Name AS transmission_name,
            t.kV AS transmission_kv,
            t.Owner AS transmission_owner,
            t.Status AS transmission_status,
            t.Circuit AS transmission_circuit,
            t.Type AS transmission_type,
            t.Length_Mil AS transmission_length_miles,

            ST_AsGeoJSON(t.geom) AS geometry,

        FROM transmission_lines AS t
        JOIN wildlife_lands AS w
            ON ST_Intersects(
                t.geom,
                w.geom
            )
    """).fetchall()

    features = []

    for row in rows:
        (
            wildlife_id,
            wildlife_property_type,
            wildlife_property_name,
            wildlife_link,
            wildlife_access,
            wildlife_region,
            wildlife_area_m2,
            transmission_id,
            transmission_name,
            transmission_kv,
            transmission_owner,
            transmission_status,
            transmission_circuit,
            transmission_type,
            transmission_length_miles,
            geometry,
        ) = row

        features.append(
            {
                "type": "Feature",
                "geometry": swap_geojson_coordinates(json.loads(geometry)),
                "properties": {
                    "wildlife_id": wildlife_id,
                    "wildlife_property_type": wildlife_property_type,
                    "wildlife_property_name": wildlife_property_name,
                    "wildlife_access": wildlife_access,
                    "wildlife_link": wildlife_link,
                    "wildlife_region": wildlife_region,
                    "wildlife_area_m2": wildlife_area_m2,
                    "transmission_id": transmission_id,
                    "transmission_name": transmission_name,
                    "transmission_kv": transmission_kv,
                    "transmission_owner": transmission_owner,
                    "transmission_status": transmission_status,
                    "transmission_circuit": transmission_circuit,
                    "transmission_type": transmission_type,
                    "transmission_length_miles": transmission_length_miles,
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }
