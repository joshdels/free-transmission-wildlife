.PHONEY: dev install 

dev:
	uv run mcp dev app/server/server.py

install:
	uv run mcp install app/server/server.py \
		--with duckdb \
		--with pandas \
		--with pyarrow