def swap_geojson_coordinates(geometry):
    """
    Convert GeoJSON coordinates from [latitude, longitude]
    to [longitude, latitude].

    Use only when the source data is known to have its
    X/Y coordinates reversed.
    """

    if geometry is None:
        return None

    def swap(coords):
        # Coordinate pair: [x, y] / [lat, lon]
        if isinstance(coords[0], (int, float)):
            return [coords[1], coords[0], *coords[2:]]

        return [swap(item) for item in coords]

    geometry["coordinates"] = swap(geometry["coordinates"])
    return geometry
