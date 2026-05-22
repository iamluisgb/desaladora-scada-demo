#!/usr/bin/env python3
"""
API REST para exponer datos de la planta desaladora.
Lee los registros Modbus del simulador y los devuelve como JSON.
"""

import json
import os
import struct
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pymodbus.client import ModbusTcpClient

app = FastAPI(title="Desaladora RO - API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MODBUS_HOST = os.getenv("MODBUS_HOST", "localhost")
MODBUS_PORT = int(os.getenv("MODBUS_PORT", "502"))
OVERRIDE_FILE = os.getenv("OVERRIDE_FILE", "/tmp/override.json")

TAG_DEFS = [
    ("FT-101", "Caudal Alimentación",    "m³/h",  1),
    ("FT-201", "Caudal Permeado",        "m³/h",  3),
    ("FT-301", "Caudal Concentrado",     "m³/h",  5),
    ("PT-101", "Presión Alta (HP)",      "bar",   7),
    ("PT-102", "Presión Baja (LP)",      "bar",   9),
    ("PT-201", "Presión Permeado",       "bar",  11),
    ("CT-101", "Conductividad Alim.",    "µS/cm",13),
    ("CT-201", "Conductividad Permeado", "µS/cm",15),
    ("TT-101", "Temperatura Agua",       "°C",   17),
    ("AT-101", "pH Alimentación",        "pH",   19),
    ("AT-201", "pH Permeado",            "pH",   21),
    ("KW-101", "Potencia Bomba HP",      "kW",   23),
    ("VL-101", "Apertura Válvula",       "%",    25),
    ("RECOV",  "Tasa Recuperación",      "%",    27),
    ("REJEC",  "Tasa Rechazo Sal",       "%",    29),
    ("PROD-H", "Producción Hora",        "m³",   31),
    ("PROD-D", "Producción Día",         "m³",   33),
]

COIL_DEFS = [
    ("SP-101", "Bomba HP"),
    ("SP-102", "Bomba Baja Presión"),
    ("ALRM-1", "Alarma Conductividad Alta"),
    ("ALRM-2", "Alarma Presión Alta"),
]

# History buffer (last 300 samples = 5 min at 1s interval)
history: list[dict] = []
MAX_HISTORY = 300


class WriteCommand(BaseModel):
    tag: str
    value: bool | float | None = None


@app.post("/api/write")
def write_tag(cmd: WriteCommand):
    """Write a tag value to the simulator via override file."""
    overrides = {}
    try:
        with open(OVERRIDE_FILE) as f:
            overrides = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    overrides[cmd.tag] = cmd.value
    with open(OVERRIDE_FILE, "w") as f:
        json.dump(overrides, f)

    return {"status": "ok", "tag": cmd.tag, "value": cmd.value}


@app.get("/api/live")
def get_live_data():
    """Return current plant data as JSON."""
    analogs, digitals = read_modbus()
    ts = time.time()

    # Append to history
    snapshot = {k: v["value"] for k, v in analogs.items()}
    snapshot["ts"] = ts
    history.append(snapshot)
    if len(history) > MAX_HISTORY:
        history.pop(0)

    return {
        "timestamp": ts,
        "analogs": analogs,
        "digitals": digitals,
    }


@app.get("/api/history")
def get_history():
    """Return recent history for trend charts."""
    return history


@app.get("/")
def index():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")
