from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
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

# =========================================================
# APP
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# STATIC FILES
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


templates = Jinja2Templates(directory=BASE_DIR / "templates")


# =========================================================
# DATABASE
# =========================================================

con = load_data()

con.execute("INSTALL spatial;")
con.execute("LOAD spatial;")


# =========================================================
# GIS API
# =========================================================


@app.get("/transmission_lines")
def get_transmission_lines():

    return get_transmission_lines_data(con.cursor())


@app.get("/wildlife_lands")
def get_wildlife_lands():

    return get_wildlife_data(con.cursor())


@app.get("/wildlife_lands_hit")
def get_wildlife_hit():

    return get_wildlife_transmission_intersections(con.cursor())


# =========================================================
# CHAT PAGE
# =========================================================


@app.get("/chat", response_class=HTMLResponse)
async def read_item(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="ui.html",
    )


# =========================================================
# EXTRACT HTML FROM AI RESPONSE
# =========================================================


def extract_html(content: str) -> str | None:

    if not content:
        return None

    content = content.strip()

    # -----------------------------------------------------
    # CASE 1
    # AI returned markdown code block
    #
    # ```html
    # <!DOCTYPE html>
    # ...
    # ```
    # -----------------------------------------------------

    if "```html" in content.lower():

        lower_content = content.lower()

        start_marker = lower_content.find("```html")

        start = start_marker + len("```html")

        end = content.find("```", start)

        if end != -1:

            html = content[start:end].strip()

            if "<html" in html.lower():

                return html

    # -----------------------------------------------------
    # CASE 2
    # AI returned generic code block
    #
    # ```
    # <!DOCTYPE html>
    # ...
    # ```
    # -----------------------------------------------------

    if "```" in content:

        first = content.find("```")

        start = content.find("\n", first)

        if start != -1:

            start += 1

            end = content.find("```", start)

            if end != -1:

                html = content[start:end].strip()

                if "<html" in html.lower():

                    return html

    # -----------------------------------------------------
    # CASE 3
    # AI added explanation before HTML
    #
    # Here's your map:
    #
    # <!DOCTYPE html>
    # ...
    # -----------------------------------------------------

    html_start = content.lower().find("<!doctype html>")

    if html_start != -1:

        html = content[html_start:].strip()

        return html

    # -----------------------------------------------------
    # CASE 4
    # AI starts directly with <html>
    # -----------------------------------------------------

    html_start = content.lower().find("<html")

    if html_start != -1:

        html = content[html_start:].strip()

        return html

    # -----------------------------------------------------
    # Not HTML
    # -----------------------------------------------------

    return None


# =========================================================
# SEND AI RESPONSE
# =========================================================


async def send_ai_response(
    websocket: WebSocket,
    content: str,
):

    if not content:

        return

    # -----------------------------------------------------
    # Try to extract HTML
    # -----------------------------------------------------

    html = extract_html(content)

    # -----------------------------------------------------
    # HTML FOUND
    # -----------------------------------------------------

    if html:

        print("AI generated HTML file")

        await websocket.send_json(
            {
                "type": "html_file",
                "filename": "file.html",
                "content": html,
            }
        )

        return

    # -----------------------------------------------------
    # NORMAL TEXT
    # -----------------------------------------------------

    await websocket.send_json(
        {
            "type": "message",
            "content": content,
        }
    )


# =========================================================
# AI WEBSOCKET
# =========================================================


@app.websocket("/ws/ai")
async def ai_websocket(
    websocket: WebSocket,
):

    await websocket.accept()

    print("AI WebSocket connected")

    while True:

        try:

            # =================================================
            # RECEIVE USER MESSAGE
            # =================================================

            message = await websocket.receive_text()

            print("USER:", message)

            # =================================================
            # MCP CALLBACK
            # =================================================

            async def send_tool_result(
                tool_name,
                arguments,
                result,
            ):

                # ------------------------------------------------
                # DO NOT DISPLAY MCP RESULTS IN CHAT
                # ------------------------------------------------

                print(f"MCP TOOL: {tool_name}")

                return

            # =================================================
            # ASK AI
            # =================================================

            response = await ask_ai(
                message,
                on_tool_result=send_tool_result,
            )

            print("AI RESPONSE:", response[:200])

            # =================================================
            # SEND FINAL RESPONSE
            # =================================================

            await send_ai_response(
                websocket,
                response,
            )

        except WebSocketDisconnect:

            print("AI WebSocket disconnected")

            break

        except Exception as e:

            print("AI ERROR:", repr(e))

            try:

                await websocket.send_json(
                    {
                        "type": "error",
                        "message": str(e),
                    }
                )

            except Exception:

                break
