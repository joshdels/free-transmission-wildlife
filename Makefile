.PHONEY: dev install 

dev:
	uv run mcp dev app/server/server.py

install:
	uv run mcp install app/server/server.py \
		--with duckdb \
		--with pandas \
		--with pyarrow \
		--with fastapi[standard]

api:
	uv run uvicorn app.api.main:app --reload

datas:
	python app/db/load_data.py

kill:
	pkill -f claude

docker:
	docker compose up -d --build