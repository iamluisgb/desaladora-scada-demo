#!/usr/bin/env python3
"""
API REST para exponer datos de la planta desaladora.
Lee los registros Modbus del simulador y los devuelve como JSON.
"""

import struct
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pymodbus.client import ModbusTcpClient

app = FastAPI(title="Desaladora RO - API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MODBUS_HOST = "localhost"
MODBUS_PORT = 502

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

# History buffer (last 120 samples = 2 min at 1s interval)
history: list[dict] = []
MAX_HISTORY = 300


def read_modbus():
    """Read all tags from the Modbus simulator."""
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    client.connect()

    # Analog tags (holding registers, float32 big-endian)
    result = client.read_holding_registers(address=1, count=34)
    analogs = {}
    if not result.isError():
        for tag, desc, unit, addr in TAG_DEFS:
            idx = addr - 1
            raw = struct.pack('>HH', result.registers[idx], result.registers[idx + 1])
            val = round(struct.unpack('>f', raw)[0], 2)
            analogs[tag] = {"value": val, "desc": desc, "unit": unit}

    # Digital tags (coils)
    coils_result = client.read_coils(address=1, count=4)
    digitals = {}
    if not coils_result.isError():
        for i, (tag, desc) in enumerate(COIL_DEFS):
            digitals[tag] = {"value": bool(coils_result.bits[i]), "desc": desc}

    client.close()
    return analogs, digitals


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
