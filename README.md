# AI-Assisted Transmission Line & Wildlife Analysis

An AI-assisted GIS application for analyzing the relationship between **electrical transmission infrastructure** and **wildlife / public-access lands** in California's San Joaquin Valley.

The project combines **GIS spatial analysis, DuckDB Spatial, MCP, LLMs, and custom web interfaces** to make spatial questions easier to ask and analyze.

## Use Case

Wildlife and environmental organizations may need to answer questions such as:

* Which transmission lines intersect wildlife lands?
* Which public-access lands are within 1 km of transmission infrastructure?
* How many transmission segments affect a particular area?
* Which areas may require further environmental review?
* What transmission infrastructure is closest to a protected or public-access area?

Instead of manually loading multiple datasets into a GIS application and constructing spatial queries, the system allows these questions to be expressed in natural language and translated into spatial analysis workflows.

## Screenshots

### Claude + MCP

![Claude MCP](public/claude.png)

### ArcGIS

![ArcGIS](public/arcgis.png)

### MapLibre

![MapLibre](public/maplibre.png)

### Web Dashboard

![Dashboard](public/dashboard.png)

## Why This Exists

Traditional GIS workflows are powerful, but spatial analysis often requires users to:

1. Find the appropriate datasets.
2. Load and inspect the data.
3. Understand coordinate systems.
4. Construct spatial queries.
5. Run geoprocessing operations.
6. Interpret the results.

This project explores a different interaction model:

> **Ask a spatial question → perform GIS analysis → receive an interpretable result.**

The goal is not to replace GIS software.

It is to explore how **AI can become an interface for spatial analysis**, while the underlying spatial operations remain deterministic and are executed by GIS-aware tools and databases.

## The Bigger Idea

This project explores the intersection of:

**GIS + Spatial Databases + AI + MCP + Custom Interfaces**

with the goal of building more accessible and automatable spatial-analysis workflows.

---

For installation instructions, see [`docs/installation`](docs/installation.md).

For the system architecture, see [`docs/architecture`](docs/architecture.md).
