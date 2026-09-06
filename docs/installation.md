# Installation

This document describes how to install, configure, run, and deploy the project locally and with Docker.

---

# Requirements

The project currently uses:

* Python 3.14+
* `uv`
* DuckDB
* DuckDB Spatial
* MCP Python
* FastAPI
* Uvicorn
* Pandas
* PyArrow
* Docker
* Docker Compose

For the local MCP workflow, you will also need:

* Claude Desktop

For the cloud workflow:

* An OpenRouter API key
* A server capable of running Docker

---

# 1. Clone the Repository

```bash
git clone https://github.com/joshdels/free-transmission-wildlife.git

cd free-transmission-wildlife
```

---

# 2. Install uv

This project uses `uv` for Python environment and dependency management.

Install `uv` using the official installation instructions for your operating system.

Verify the installation:

```bash
uv --version
```

---

# 3. Install Project Dependencies

Synchronize the project environment:

```bash
uv sync
```

This installs the dependencies defined by the project.

---

# 4. Environment Variables

The cloud application uses OpenRouter for LLM access.

Create a local environment file:

```bash
touch .env
```

Add:

```env
OPENROUTER_API_KEY=your-openrouter-api-key
```

If the application exposes a configurable frontend/backend URL, it can also be configured using:

```env
API_BASE_URL=http://127.0.0.1:8000
```

For production:

```env
API_BASE_URL=https://your-domain.com
```

## Security

Never commit your real API key.

Make sure `.env` is included in `.gitignore`:

```text
.env
.env.*
```

Use `.env.example` when sharing the required configuration structure:

```env
OPENROUTER_API_KEY=
API_BASE_URL=
```

---

# 5. Prepare the GIS Data

The project expects the GIS datasets to be available under:

```text
data/
```

Example:

```text
data/
├── transmission_lines/
│   └── TransmissionLine_CEC.shp
│
└── public_lands/
    └── CDFW_Public_Access_Lands_[ds3077].shp
```

Make sure all required files belonging to a Shapefile dataset are present.

For example:

```text
dataset.shp
dataset.shx
dataset.dbf
dataset.prj
```

---

# 6. Load the Data

Use the data-loading script to prepare the GIS data for DuckDB:

```bash
make datas
```

Or run it directly:

```bash
uv run python app/db/load_data.py
```

The loading process prepares the GIS datasets for spatial analysis.

---

# 7. Local MCP Development

The project can be run locally through the MCP development environment.

Start the MCP server:

```bash
make dev
```

Equivalent command:

```bash
uv run mcp dev app/server/server.py
```

This starts the MCP development workflow for the project.

The local architecture is:

```text
User
  ↓
Claude Desktop
  ↓
Local MCP
  ↓
DuckDB Spatial
  ↓
GIS Data
```

---

# 8. Install the MCP Server into Claude

To install the MCP server into your Claude Desktop environment:

```bash
make install
```

This runs:

```bash
uv run mcp install app/server/server.py \
    --with duckdb \
    --with pandas \
    --with pyarrow \
    --with "fastapi[standard]"
```

After installation, the MCP server can be used by the configured Claude Desktop environment.

---

# 9. Run the Backend API

Start the FastAPI application:

```bash
make api
```

Equivalent command:

```bash
uv run uvicorn app.api.main:app --reload
```

The development server will normally be available at:

```text
http://127.0.0.1:8000
```

The API documentation is typically available at:

```text
http://127.0.0.1:8000/docs
```

if the FastAPI application exposes the default documentation route.

---

# 10. Custom Web UI

The cloud architecture uses a custom web interface rather than Claude Desktop.

The frontend communicates with the backend:

```text
Custom Web UI
      ↓
Backend API
      ↓
OpenRouter
      ↓
AI Model
      ↓
Spatial Analysis
```

The frontend should use the configured API base URL.

For local development:

```env
API_BASE_URL=http://127.0.0.1:8000
```

For production:

```env
API_BASE_URL=https://your-domain.com
```

The OpenRouter API key should remain exclusively on the backend.

The browser should never receive:

```text
OPENROUTER_API_KEY
```

---

# 11. Make Commands

The project provides a Makefile for common development operations.

| Command        | Purpose                              |
| -------------- | ------------------------------------ |
| `make dev`     | Start the MCP development server     |
| `make install` | Install the MCP server into Claude   |
| `make api`     | Start the FastAPI development server |
| `make datas`   | Load / prepare GIS datasets          |
| `make docker`  | Build and start Docker Compose       |
| `make kill`    | Stop local Claude processes          |

---

# 12. Docker

The application can be deployed using Docker.

Build and start the services:

```bash
make docker
```

Equivalent:

```bash
docker compose up -d --build
```

Check running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

Stop the application:

```bash
docker compose down
```

---

# 13. Docker Environment Variables

When deploying with Docker, provide the required environment variables to the application.

Example:

```env
OPENROUTER_API_KEY=your-openrouter-api-key
API_BASE_URL=https://your-domain.com
```

Do not bake secrets directly into the Dockerfile.

Prefer environment variables or your deployment platform's secret-management system.

---

# 14. Production Deployment

A typical production deployment looks like:

```text
Internet
   │
   ▼
Domain
   │
   ▼
Reverse Proxy
   │
   ▼
Docker
   │
   ├── Backend / API
   │
   └── Spatial Analysis
          │
          ▼
      DuckDB Spatial
          │
          ▼
       GIS Data
```

The backend communicates with OpenRouter:

```text
Backend
   │
   ▼
OpenRouter
   │
   ▼
LLM
```

The browser communicates only with the application's backend.

---

# 15. Recommended Production Configuration

For production:

* Disable development reload mode.
* Do not expose `.env`.
* Keep API keys server-side.
* Use HTTPS.
* Put the application behind a reverse proxy.
* Configure appropriate CORS rules.
* Use production logging.
* Monitor container health.
* Keep GIS datasets backed up.
* Pin dependency versions.
* Avoid exposing internal database or spatial-analysis services directly to the public internet.

---

# 16. Updating the Application

Pull the latest source:

```bash
git pull
```

Synchronize dependencies:

```bash
uv sync
```

For Docker deployments:

```bash
docker compose up -d --build
```

---

# 17. Troubleshooting

## Check Python

```bash
python --version
```

## Check uv

```bash
uv --version
```

## Check Docker

```bash
docker --version
```

## Check Docker Compose

```bash
docker compose version
```

## Check application logs

```bash
docker compose logs -f
```

## Check running containers

```bash
docker compose ps
```

## Check the API

Open:

```text
http://127.0.0.1:8000
```

or the FastAPI documentation route:

```text
http://127.0.0.1:8000/docs
```

---

# 18. Local Development Workflow

A typical local development session is:

```bash
# Install dependencies
uv sync

# Prepare datasets
make datas

# Start MCP development
make dev
```

For API development:

```bash
make api
```

---

# 19. Docker Development Workflow

A typical Docker workflow is:

```bash
# Build and start
make docker

# Check containers
docker compose ps

# Follow logs
docker compose logs -f
```

To stop:

```bash
docker compose down
```

---

# 20. Development Architecture

Local development:

```text
Claude Desktop
      ↓
MCP Server
      ↓
DuckDB Spatial
      ↓
GIS Data
```

Cloud development:

```text
Custom Web UI
      ↓
FastAPI Backend
      ↓
OpenRouter
      ↓
LLM
      ↓
Spatial Tools
      ↓
DuckDB Spatial
      ↓
GIS Data
```

---

# 21. Project Structure

The relevant project structure is:

```text
free-transmission-wildlife/
│
├── app/
│   ├── api/
│   │   └── main.py
│   │
│   ├── db/
│   │   ├── load_data.py
│   │   └── queries.py
│   │
│   └── server/
│       └── server.py
│
├── data/
│   ├── transmission_lines/
│   └── public_lands/
│
├── public/
│   ├── claude.png
│   ├── arcgis.png
│   ├── maplibre.png
│   └── dashboard.png
│
├── docs/
│   ├── architecture/
│   │   └── README.md
│   │
│   └── installation/
│       └── README.md
│
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── uv.lock
└── README.md
```

---

# 22. Quick Start

For local development:

```bash
git clone https://github.com/joshdels/free-transmission-wildlife.git

cd free-transmission-wildlife

uv sync

make datas

make dev
```

For the API:

```bash
make api
```

For Docker:

```bash
make docker
```

---

# 23. Next Steps

After installation:

* Review the project README.
* Review the architecture documentation.
* Load the GIS datasets.
* Test spatial queries.
* Run the MCP server locally.
* Configure Claude Desktop.
* Run the FastAPI backend.
* Configure the custom web UI.
* Configure OpenRouter for cloud inference.
* Deploy with Docker when ready.
