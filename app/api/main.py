import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.queries import (
    get_transmission_lines_data,
    get_wildlife_data,
    get_wildlife_transmission_intersections,
)
from app.db.load_data import load_data

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

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
