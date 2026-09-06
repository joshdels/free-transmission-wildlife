# Architecture

This document describes the architecture of the AI-assisted GIS system, including the local MCP workflow and the cloud application workflow.

---

## Overview

The project has two primary ways of interacting with the spatial analysis system:

1. **Local MCP workflow** — used for development and experimentation with Claude Desktop.
2. **Cloud application workflow** — used by the custom web interface and deployed backend.

Both workflows use the same core idea:

> Natural-language questions are translated into spatial analysis operations that run against GIS datasets.

The spatial analysis itself is handled by application tools and DuckDB Spatial rather than by the language model directly.

---

# Local Architecture

The local workflow is designed for development, experimentation, and direct interaction with the MCP server.

```text
┌──────────────┐
│     User     │
└──────┬───────┘
       │
       │ Natural-language question
       ▼
┌──────────────────┐
│  Claude Desktop  │
└────────┬─────────┘
         │
         │ MCP
         ▼
┌──────────────────┐
│    MCP Server    │
└────────┬─────────┘
         │
         │ Spatial tools
         ▼
┌──────────────────┐
│  DuckDB Spatial  │
└────────┬─────────┘
         │
         │ SQL / spatial operations
         ▼
┌──────────────────┐
│    GIS Data      │
│                  │
│ Transmission     │
│ Wildlife Lands   │
│ Public Lands     │
└────────┬─────────┘
         │
         │ Spatial result
         ▼
┌──────────────────┐
│  MCP / Claude    │
│     Response     │
└──────────────────┘
```

## Local Request Flow

A typical request follows this sequence:

1. The user asks a spatial question in Claude Desktop.
2. Claude determines that spatial analysis is required.
3. Claude calls an available MCP tool.
4. The MCP server executes the appropriate spatial operation.
5. DuckDB Spatial queries the GIS datasets.
6. The spatial result is returned to the MCP server.
7. The result is returned to Claude.
8. Claude presents the result to the user.

For example:

```text
"Which transmission lines intersect public-access lands?"
```

The system can translate this into a spatial operation based on:

```text
Transmission Lines
        +
Public Access Lands
        ↓
ST_Intersects(...)
        ↓
Matching Features
        ↓
Result
```

---

# Cloud Architecture

The cloud architecture uses a custom web interface rather than exposing Claude Desktop or an MCP development environment to end users.

```text
┌──────────────┐
│     User     │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│   Custom Web UI  │
└────────┬─────────┘
         │
         │ HTTP / API
         ▼
┌──────────────────┐
│   Backend / API  │
└────────┬─────────┘
         │
         │ AI request
         ▼
┌──────────────────┐
│    OpenRouter    │
└────────┬─────────┘
         │
         │ LLM inference
         ▼
┌──────────────────┐
│     AI Model     │
└────────┬─────────┘
         │
         │ Tool / analysis request
         ▼
┌──────────────────────┐
│ Spatial Analysis     │
│ Tools / Application  │
│ Layer                │
└──────────┬───────────┘
           │
           ▼
┌──────────────────┐
│  DuckDB Spatial  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    GIS Data      │
└────────┬─────────┘
         │
         │ Spatial result
         ▼
┌──────────────────┐
│   Backend / API  │
└────────┬─────────┘
         │
         │ JSON / response
         ▼
┌──────────────────┐
│   Custom Web UI  │
└──────────────────┘
```

---

# Cloud Request Flow

A typical cloud request follows this sequence:

### 1. User submits a question

The user interacts with the custom web interface.

Example:

```text
Show transmission lines within 1 km of public-access lands.
```

### 2. Frontend sends the request

The browser sends the question to the backend API.

```text
Browser
   ↓
POST /api/...
```

### 3. Backend communicates with OpenRouter

The backend sends the request to OpenRouter.

The OpenRouter API acts as the gateway between the application and the selected language model.

```text
Backend
   ↓
OpenRouter
   ↓
LLM
```

The API key remains on the server.

It is **never exposed to the browser**.

### 4. AI determines the required operation

The model interprets the user's request and determines the appropriate spatial operation.

For example:

```text
"within 1 km"

        ↓

buffer / distance analysis
```

### 5. Spatial tools execute the operation

The application/tool layer performs the actual GIS operation.

```text
AI decision
    ↓
Spatial tool
    ↓
DuckDB Spatial
```

### 6. DuckDB Spatial queries the data

DuckDB Spatial performs the spatial computation against the loaded GIS datasets.

Possible operations include:

* `ST_Intersects`
* `ST_Within`
* `ST_DWithin`
* `ST_Distance`
* `ST_Buffer`
* Geometry inspection
* Filtering
* Aggregation
* Counting
* Area calculations
* Length calculations

### 7. Result returns to the backend

The spatial result is returned to the backend.

The backend can then format the result for the frontend.

### 8. Custom UI displays the result

The frontend presents the result to the user.

Depending on the application, this could include:

* Text
* Tables
* Counts
* Spatial features
* GeoJSON
* Maps
* Charts
* Analysis summaries

---

# MCP Architecture

MCP provides a standardized interface between an AI client and external tools.

In the local workflow:

```text
Claude Desktop
      │
      │ MCP
      ▼
MCP Server
      │
      ▼
Spatial Tools
      │
      ▼
DuckDB Spatial
```

The MCP server exposes capabilities that allow the AI client to interact with the spatial-analysis environment.

This separates:

```text
AI reasoning
```

from:

```text
actual spatial computation
```

The language model can determine what needs to be done, while the spatial tool performs the operation against real GIS data.

---

# Spatial Data Layer

The project currently uses GIS datasets representing infrastructure and public/environmental land.

Example datasets include:

```text
data/
├── transmission_lines/
│   └── TransmissionLine_CEC.shp
│
└── public_lands/
    └── CDFW_Public_Access_Lands_[ds3077].shp
```

These datasets are loaded into DuckDB for spatial analysis.

The architecture is intentionally designed so additional datasets can be introduced later.

Potential future datasets include:

* Parcels
* Protected areas
* Wildlife habitat
* Environmental constraints
* Renewable-energy sites
* Roads
* Administrative boundaries
* Land-use datasets
* Infrastructure networks

---

# DuckDB Spatial

DuckDB acts as the analytical database for the project.

DuckDB Spatial provides spatial functions that allow GIS operations to be performed directly inside the analytical database.

For example:

```sql
SELECT *
FROM transmission_lines t
JOIN public_lands p
ON ST_Intersects(t.geom, p.geom);
```

This allows spatial analysis to remain close to the data layer without requiring a large database infrastructure for the prototype.

---

# Application Layer

The application layer is responsible for connecting the AI interaction with the spatial-analysis capabilities.

Conceptually:

```text
Natural Language
       ↓
AI Interpretation
       ↓
Spatial Operation
       ↓
Database Query
       ↓
Spatial Result
       ↓
Human-readable Response
```

This separation is important because the AI model should not be responsible for directly performing geometric calculations.

Instead:

```text
AI = interpretation / orchestration

Spatial tools = GIS operations

DuckDB Spatial = spatial computation
```

---

# OpenRouter

OpenRouter is used in the cloud architecture as the AI gateway.

```text
Custom UI
    ↓
Backend
    ↓
OpenRouter
    ↓
Selected LLM
```

This allows the backend to communicate with different supported models through a common API interface.

The `OPENROUTER_API_KEY` must remain server-side.

It should be stored as an environment variable and should never be committed to Git.

---

# Environment Separation

The project separates local development from cloud deployment.

## Local

```text
Claude Desktop
      ↓
Local MCP
      ↓
DuckDB
      ↓
Local GIS Data
```

## Cloud

```text
Custom Web UI
      ↓
Backend API
      ↓
OpenRouter
      ↓
AI Model
      ↓
Spatial Tools
      ↓
DuckDB
      ↓
GIS Data
```

The same spatial-analysis concepts can therefore be used in both environments while changing the user interface and infrastructure around them.

---

# Deployment Architecture

Docker provides the deployment layer for the application.

Conceptually:

```text
┌───────────────────────────────┐
│          Cloud Server         │
│                               │
│  ┌─────────────────────────┐  │
│  │       Docker            │  │
│  │                         │  │
│  │  ┌───────────────────┐  │  │
│  │  │ Backend / API     │  │  │
│  │  └─────────┬─────────┘  │  │
│  │            │            │  │
│  │            ▼            │  │
│  │  ┌───────────────────┐  │  │
│  │  │ DuckDB Spatial    │  │  │
│  │  └─────────┬─────────┘  │  │
│  │            │            │  │
│  │            ▼            │  │
│  │       GIS Data          │  │
│  └─────────────────────────┘  │
│                               │
└───────────────────────────────┘
               │
               ▼
          OpenRouter
```

Docker provides a consistent environment for running the backend and supporting services.

---

# Security

The cloud application should keep secrets on the server.

Sensitive configuration includes:

```text
OPENROUTER_API_KEY
```

The key should be supplied through environment variables.

It should **not** be:

* Hardcoded in Python
* Included in JavaScript
* Sent to the browser
* Stored in Git
* Included in Docker images
* Included in screenshots

A typical configuration is:

```text
.env
```

with:

```text
OPENROUTER_API_KEY=your-key
```

The `.env` file should be excluded through `.gitignore`.

---

# Future Architecture

The current architecture is intentionally lightweight.

Future versions may introduce:

```text
                 ┌──────────────┐
                 │ Custom Web UI│
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ Backend/API  │
                 └──────┬───────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
        ┌──────────┐         ┌──────────┐
        │   LLM    │         │ GIS Tools│
        └──────────┘         └────┬─────┘
                                  │
                                  ▼
                           ┌─────────────┐
                           │ Spatial DB  │
                           └──────┬──────┘
                                  │
                                  ▼
                           ┌─────────────┐
                           │ GIS Datasets│
                           └─────────────┘
```

Potential future improvements include:

* GeoParquet
* Larger datasets
* Cloud object storage
* PostGIS
* More spatial tools
* GeoJSON output
* Interactive mapping
* Automated reports
* Spatial visualization
* Dataset management
* Authentication
* Multi-user applications
* Background processing
* Scalable cloud infrastructure

---

# Design Principle

The central architectural principle is:

> **Use AI to make spatial analysis easier to interact with, while keeping spatial computation inside deterministic GIS-aware systems.**

This creates a separation between:

```text
Human intent
     ↓
AI interpretation
     ↓
Tool orchestration
     ↓
Spatial computation
     ↓
GIS result
     ↓
Human-readable explanation
```
