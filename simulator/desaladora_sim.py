#!/usr/bin/env python3
"""
Simulador Modbus TCP - Planta Desaladora (Osmosis Inversa)
Expone 21 tags de proceso en el puerto 502 como servidor Modbus TCP.

Mapeo de registros (1-based, como requiere pymodbus 3.x):
  HoldingRegisters (float32, 2 regs cada uno):
    1-2:   FT-101  Caudal alimentación  (m³/h)
    3-4:   FT-201  Caudal permeado      (m³/h)
    5-6:   FT-301  Caudal concentrado   (m³/h)
    7-8:   PT-101  Presión HP           (bar)
    9-10:  PT-102  Presión LP entrada   (bar)
    11-12: PT-201  Presión permeado     (bar)
    13-14: CT-101  Conductividad alim.  (µS/cm)
    15-16: CT-201  Conductividad perm.  (µS/cm)
    17-18: TT-101  Temperatura          (°C)
    19-20: AT-101  pH alimentación
    21-22: AT-201  pH permeado
    23-24: KW-101  Potencia bomba HP    (kW)
    25-26: VL-101  Apertura válvula     (%)
    27-28: RECOV   Tasa recuperación    (%)
    29-30: REJEC   Tasa rechazo sal     (%)
    31-32: PROD-H  Producción hora      (m³)
    33-34: PROD-D  Producción día       (m³)

  Coils (1-based, Rapid SCADA reads via PDU address=1):
    1: SP-101  Bomba HP ON/OFF
    2: SP-102  Bomba LP ON/OFF
    3: ALRM-1  Alarma conductividad alta
    4: ALRM-2  Alarma presión alta
"""

import json
import os
import struct
import math
import random
import logging
import asyncio
from datetime import datetime

from pymodbus.simulator.simdevice import SimDevice
from pymodbus.simulator.simdata import SimData, DataType
from pymodbus.server import StartAsyncTcpServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Shared state (updated by background loop)
# ─────────────────────────────────────────────

# 34 raw 16-bit register values for HoldingRegisters 1..34
HR_REGS: list[int] = [0] * 34
# 4 coil values for Coils 1..4
COIL_VALS: list[bool] = [False] * 4


def float_to_regs(f: float) -> tuple[int, int]:
    """Convert float to two 16-bit big-endian words."""
    packed = struct.pack('>f', float(f))
    hi = struct.unpack('>H', packed[0:2])[0]
    lo = struct.unpack('>H', packed[2:4])[0]
    return hi, lo


def pack_analog_tags(tags: dict) -> list[int]:
    """Pack all 17 analog tags into 34 register words."""
    order = [
        'FT101', 'FT201', 'FT301',
        'PT101', 'PT102', 'PT201',
        'CT101', 'CT201', 'TT101', 'AT101', 'AT201',
        'KW101', 'VL101', 'RECOV', 'REJEC',
        'PRODH', 'PRODD',
    ]
    regs = []
    for tag in order:
        hi, lo = float_to_regs(tags[tag])
        regs.extend([hi, lo])
    return regs  # 34 words


# ─────────────────────────────────────────────
# Process simulation
# ─────────────────────────────────────────────

OVERRIDE_FILE = "/tmp/override.json"

def load_overrides() -> dict:
    try:
        with open(OVERRIDE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

class DesaladoProcess:
    def __init__(self):
        self.t = 0.0
        self.prod_hour = 0.0
        self.prod_day  = 0.0
        self.hour_reset_at = 3600.0
        self.day_reset_at  = 86400.0

    @staticmethod
    def _clamp(v, lo, hi):
        return max(lo, min(hi, v))

    def _sin(self, period_s, amp, phase=0.0):
        return amp * math.sin(2 * math.pi * (self.t + phase) / period_s)

    def tick(self, dt: float, overrides: dict = None) -> dict:
        self.t += dt

        drift = self._sin(7200, 1.0)

        ft101 = self._clamp(100.0 + drift * 3 + random.gauss(0, 0.5), 80, 120)
        ft201 = self._clamp(50.0  + drift * 1.5 + random.gauss(0, 0.3), 40, 60)
        ft301 = self._clamp(ft101 - ft201 + random.gauss(0, 0.2), 30, 50)

        pt101 = self._clamp(60.0 + self._sin(3600, 1.5) + random.gauss(0, 0.3), 55, 65)
        pt102 = self._clamp(3.0  + random.gauss(0, 0.1), 2, 4)
        pt201 = self._clamp(1.0  + random.gauss(0, 0.05), 0.5, 1.5)

        ct101 = self._clamp(50000 + self._sin(10800, 2000) + random.gauss(0, 200), 45000, 55000)
        if os.path.exists('/tmp/trigger_alarm'):
            ct201 = 500.0  # forced high conductivity for alarm test
        else:
            ct201 = self._clamp(200   + self._sin(5400, 80)   + random.gauss(0, 10),  100,   300)

        tt101 = self._clamp(21.5 + self._sin(86400, 2.0) + random.gauss(0, 0.2), 18, 25)
        at101 = self._clamp(7.0  + random.gauss(0, 0.05), 6.8, 7.2)
        at201 = self._clamp(6.75 + random.gauss(0, 0.04), 6.5, 7.0)

        kw101 = self._clamp(50.0  + (pt101 - 60) * 0.5 + random.gauss(0, 0.3), 45, 55)
        vl101 = self._clamp(65.0  + random.gauss(0, 1.0), 0, 100)

        recov = self._clamp((ft201 / ft101) * 100, 40, 55) if ft101 > 0 else 47.0
        rejec = self._clamp((1 - ct201 / ct101) * 100, 98, 99.9) if ct101 > 0 else 99.4

        self.prod_hour += ft201 * dt / 3600.0
        self.prod_day  += ft201 * dt / 3600.0

        if self.t >= self.hour_reset_at:
            self.prod_hour = 0.0
            self.hour_reset_at += 3600.0
        if self.t >= self.day_reset_at:
            self.prod_day = 0.0
            self.day_reset_at += 86400.0

        sp101  = 1
        sp102  = 1
        alrm1  = 1 if ct201 > 400 else 0
        alrm2  = 1 if pt101 > 67  else 0

        # Apply user overrides from file (set via dashboard)
        ovr = overrides or {}
        if 'SP101' in ovr:
            sp101 = 1 if ovr['SP101'] else 0
        if 'SP102' in ovr:
            sp102 = 1 if ovr['SP102'] else 0
        if 'VL101' in ovr:
            vl101 = max(0, min(100, float(ovr['VL101'])))
        if 'FORCE_ALARM' in ovr and ovr['FORCE_ALARM']:
            ct201 = 500.0
            alrm1 = 1

        return {
            'FT101': ft101, 'FT201': ft201, 'FT301': ft301,
            'PT101': pt101, 'PT102': pt102, 'PT201': pt201,
            'CT101': ct101, 'CT201': ct201,
            'TT101': tt101, 'AT101': at101, 'AT201': at201,
            'KW101': kw101, 'VL101': vl101,
            'RECOV': recov, 'REJEC': rejec,
            'PRODH': self.prod_hour, 'PRODD': self.prod_day,
            'SP101': sp101, 'SP102': sp102,
            'ALRM1': alrm1, 'ALRM2': alrm2,
        }


# ─────────────────────────────────────────────
# Modbus action callback (called on every read)
# ─────────────────────────────────────────────

async def modbus_action(
    function_code: int,
    start_address: int,
    address: int,
    count: int,
    current_registers: list,
    set_values,
):
    """Populate current_registers from the shared state on every read.

    pymodbus passes the FULL block as current_registers. After this callback,
    it returns registers[offset:offset+count] where offset = address - start_address.
    So we must copy our data to the ABSOLUTE block position (index = value - 1 for 1-based).
    """
    global HR_REGS, COIL_VALS

    if function_code == 3:  # Read Holding Registers
        # current_registers is the full holding-register block (34 words)
        for i in range(min(len(current_registers), len(HR_REGS))):
            current_registers[i] = HR_REGS[i]

    elif function_code == 1:  # Read Coils
        # Non-shared blocks with use_bit_addressing=True (default).
        # SimData(address=0, count=4) → pymodbus stores bits in registers[0].
        # Bit layout: registers[0] bits 0-15, where coil N maps to bit N.
        # Rapid SCADA reads PDU address=1 → get_bit_block:
        #   offset = int(1/16) - 0 = 0, bit_offset = 1%16 = 1
        #   Returns registersToBits(registers[0:1])[1:5] = bits 1,2,3,4
        # So COIL_VALS[i] maps to bit (i+1) in current_registers[0].
        val0 = 0
        for i, coil in enumerate(COIL_VALS):
            bit_pos = i + 1  # coil 0 → bit 1, coil 1 → bit 2, etc.
            if coil:
                val0 |= (1 << bit_pos)
        current_registers[0] = val0


# ─────────────────────────────────────────────
# Background update loop
# ─────────────────────────────────────────────

async def update_loop(process: DesaladoProcess):
    global HR_REGS, COIL_VALS
    while True:
        overrides = load_overrides()
        tags = process.tick(1.0, overrides)
        HR_REGS = pack_analog_tags(tags)
        COIL_VALS = [
            bool(tags['SP101']),
            bool(tags['SP102']),
            bool(tags['ALRM1']),
            bool(tags['ALRM2']),
        ]
        if int(process.t) % 10 == 0:
            log.info(
                f"FT101={tags['FT101']:.1f} m³/h | PT101={tags['PT101']:.1f} bar | "
                f"CT201={tags['CT201']:.0f} µS/cm | RECOV={tags['RECOV']:.1f}% | "
                f"REJEC={tags['REJEC']:.2f}% | ALRM1={tags['ALRM1']} ALRM2={tags['ALRM2']}"
            )
        await asyncio.sleep(1.0)


# ─────────────────────────────────────────────
# Server startup
# ─────────────────────────────────────────────

async def main():
    process = DesaladoProcess()

    # Pre-populate initial values
    tags = process.tick(0.0)
    HR_REGS[:] = pack_analog_tags(tags)
    COIL_VALS[:] = [bool(tags['SP101']), bool(tags['SP102']),
                    bool(tags['ALRM1']), bool(tags['ALRM2'])]

    # Define device registers using non-shared block (4 separate blocks)
    # Coils: address=0 so that pymodbus stores bits in registers[0] and
    # Rapid SCADA reading from PDU address=1 maps to offset=1 which reads
    # the correct register block. With use_bit_addressing=True (default for
    # non-shared), address=0 means register 0, and read_coils(address=1)
    # uses offset=1 in the bit array.
    # Fix: use address=0 and let pymodbus handle bit layout naturally.
    coils_block   = [SimData(address=0, count=4,  datatype=DataType.BITS)]
    di_block      = [SimData(address=1, count=1,  datatype=DataType.BITS)]
    hr_block      = [SimData(address=1, count=34, datatype=DataType.REGISTERS)]
    ir_block      = [SimData(address=1, count=1,  datatype=DataType.REGISTERS)]

    device = SimDevice(
        id=1,
        simdata=(coils_block, di_block, hr_block, ir_block),
        action=modbus_action,
    )

    log.info("Starting Desaladora Modbus TCP simulator on 0.0.0.0:502")
    log.info("21 tags: 17 analog (HR float32 regs 1-34) + 4 digital (Coils 1-4)")

    asyncio.create_task(update_loop(process))

    await StartAsyncTcpServer(
        context=device,
        address=("0.0.0.0", 502),
    )


if __name__ == "__main__":
    asyncio.run(main())
