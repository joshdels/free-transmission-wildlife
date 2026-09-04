from pathlib import Path

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.db.queries import (
    get_transmission_lines_data,
    get_wildlife_data,
    get_wildlife_transmission_intersections,
)
from app.ai.service import ask_ai
from app.db.load_data import load_data

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

con = load_data()
con.execute("INSTALL spatial; LOAD spatial;")


@app.get("/transmission_lines")
def get_transmission_lines():
    data = get_transmission_lines_data(con.cursor())
    return data


@app.get("/wildlife_lands")
def get_wildlife_lands():
    data = get_wildlife_data(con.cursor())
    return data


@app.get("/wildlife_lands_hit")
def get_wildlife_hit():
    data = get_wildlife_transmission_intersections(con.cursor())
    return data


@app.get("/chat", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request, name="ui.html"
    )


@app.websocket("/ws/ai")
async def ai_chat(websocket: WebSocket):
    await websocket.accept()

    while True:
        message = await websocket.receive_text()

        response = await ask_ai(message)

        await websocket.send_text(response)
