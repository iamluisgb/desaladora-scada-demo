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


@app.get("/api/kpis")
def get_kpis():
    """Return computed KPIs from historical data."""
    if not history:
        return {"status": "no_data"}

    count = len(history)
    prod_h = history[-1].get("PROD-H", 0) if count > 0 else 0
    prod_d = history[-1].get("PROD-D", 0) if count > 0 else 0
    avg_recov = sum(h.get("RECOV", 0) for h in history) / count
    avg_rejec = sum(h.get("REJEC", 0) for h in history) / count
    avg_pres = sum(h.get("PT-101", 0) for h in history) / count
    max_pres = max(h.get("PT-101", 0) for h in history)
    min_pres = min(h.get("PT-101", 0) for h in history)
    avg_ct201 = sum(h.get("CT-201", 0) for h in history) / count
    max_ct201 = max(h.get("CT-201", 0) for h in history)
    alarm_time_pct = sum(1 for h in history if h.get("CT-201", 0) > 400) / count * 100

    return {
        "count": count,
        "duration_min": round(count * 1.0 / 60, 1),
        "produccion_hora": round(prod_h, 1),
        "produccion_dia": round(prod_d, 0),
        "recuperacion_promedio": round(avg_recov, 1),
        "rechazo_promedio": round(avg_rejec, 2),
        "presion_promedio": round(avg_pres, 1),
        "presion_max": round(max_pres, 1),
        "presion_min": round(min_pres, 1),
        "conductividad_perm_promedio": round(avg_ct201, 0),
        "conductividad_perm_max": round(max_ct201, 0),
        "tiempo_alarma_pct": round(alarm_time_pct, 1),
    }


@app.get("/api/trends")
def get_trends(range_min: int = 5):
    """Return history for the last N minutes."""
    max_samples = range_min * 60
    if max_samples >= len(history):
        return history
    return history[-max_samples:]


@app.get("/")
def index():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")
