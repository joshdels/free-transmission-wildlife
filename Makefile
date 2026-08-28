.PHONEY: dev install 

dev:
	uv run mcp dev app/server/server.py

install:
	pkill -f claude
	uv run mcp install app/server/server.py \
		--with duckdb \
		--with pandas \
		--with pyarrow \
		--with fastapi[standard]

api:
	uv run uvicorn app.api.main:app --reload

data:
	python app/db/load_data.py