# Desaladora SCADA Demo

Demo funcional de un sistema SCADA para planta desaladora (Osmosis Inversa) usando **Rapid SCADA v6** con datos simulados en tiempo real.

## Requisitos

- Ubuntu Linux 20.04+ (kernel 5.x+)
- .NET 8 Runtime
- Python 3.8+
- 2 CPU cores, 4 GB RAM mínimo
- 2 GB disco libre

## Instalación rápida

### 1. Instalar .NET 8 Runtime

```bash
curl -fsSL https://dot.net/v1/dotnet-install.sh | bash -s -- --channel 8.0 --install-dir /opt/dotnet
echo 'export PATH=$PATH:/opt/dotnet' >> ~/.bashrc && source ~/.bashrc
dotnet --version
```

### 2. Instalar Rapid SCADA v6.4.6

```bash
wget https://github.com/rapidscada/scada-v6/releases/download/v6.4.6/RapidSCADA-6.4.6-Linux-x64.zip
unzip RapidSCADA-6.4.6-Linux-x64.zip -d /opt/scada/
chown -R $USER:$USER /opt/scada/
```

### 3. Clonar este repo y copiar configuración

```bash
git clone <repo-url>
cp -r desaladora-scada-demo/scada/* /opt/scada/
```

### 4. Instalar simulador

```bash
cd desaladora-scada-demo/simulator
pip3 install pymodbus
```

### 5. Generar BaseDAT desde BaseXML

Abrir el proyecto en Rapid SCADA Admin:
- `File` → `Import/Export` → `Generate DAT files`
- O manualmente: ejecutar `dotnet /opt/scada/ScadaServerApp/ScadaServerApp.dll --generate-dat`

### 6. Configurar servicios systemd

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now desaladora-sim scada-server scada-comm scada-web
```

### 7. Verificar

```bash
curl -s http://localhost:5000 | head -5
```

Debería devolver HTML de la interfaz web.

## Credenciales

| Campo | Valor |
|---|---|
| URL | `http://localhost:5000` |
| Usuario | `admin` |
| Contraseña | `scada123` |

## Arquitectura

```
┌──────────────────┐     ┌──────────────────┐
│ desaladora_sim   │────▶│ Rapid SCADA Comm │
│ (Python Modbus)  │     │ (Modbus TCP CLI) │
│   puerto :502    │     └────────┬─────────┘
└──────────────────┘              │
                                  ▼
                         ┌──────────────────┐
                         │ Rapid SCADA Server│
                         │ (motor + históricos)
                         └────────┬─────────┘
                                  ▼
                         ┌──────────────────┐
                         │ Rapid SCADA Web  │
                         │  http://:5000    │
                         └──────────────────┘
```

## Canales simulados (21)

| Tag | Descripción | Rango | Unidad |
|---|---|---|---|
| FT-101 | Caudal alimentación | 80–120 | m³/h |
| FT-201 | Caudal permeado | 40–60 | m³/h |
| FT-301 | Caudal concentrado | 30–50 | m³/h |
| PT-101 | Presión alta (HP) | 55–65 | bar |
| PT-102 | Presión baja (LP) | 2–4 | bar |
| PT-201 | Presión permeado | 0.5–1.5 | bar |
| CT-101 | Conductividad alimentación | 45000–55000 | µS/cm |
| CT-201 | Conductividad permeado | 100–300 | µS/cm |
| TT-101 | Temperatura agua | 18–25 | °C |
| AT-101 | pH alimentación | 6.8–7.2 | pH |
| AT-201 | pH permeado | 6.5–7.0 | pH |
| KW-101 | Potencia bomba HP | 45–55 | kW |
| SP-101 | Estado bomba HP | 0/1 | — |
| SP-102 | Estado bomba LP | 0/1 | — |
| VL-101 | Apertura válvula antiscalant | 0–100 | % |
| RECOV | Tasa de recuperación | 40–55 | % |
| REJEC | Tasa de rechazo de sal | 98–99.9 | % |
| PROD-H | Producción acumulada hora | acum. | m³ |
| PROD-D | Producción acumulada día | acum. | m³ |
| ALRM-1 | Alarma conductividad alta | 0/1 | — |
| ALRM-2 | Alarma presión alta | 0/1 | — |

## Vistas

- **General** — Diagrama de flujo P&ID simplificado con valores en tiempo real
- **Tendencias** — Gráficos históricos 24h (archivos minuto)
- **Alarmas** — Panel de alarmas activas y registro histórico
- **Producción** — KPIs de producción y eficiencia

## Dashboard FastAPI

Además de la interfaz web de Rapid SCADA, se incluye un dashboard alternativo construido con **FastAPI** + **Chart.js**.

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/live` | Datos corrientes de la planta (analógicos + digitales) |
| `GET` | `/api/history` | Historial reciente (últimos 300 samples) |
| `GET` | `/` | Dashboard web (index.html) |

### Respuesta `/api/live`

```json
{
  "timestamp": 1716384000,
  "analogs": {
    "FT-101": {"value": 95.3, "desc": "Caudal Alimentación", "unit": "m³/h"},
    "PT-101": {"value": 60.2, "desc": "Presión Alta (HP)", "unit": "bar"},
    "CT-201": {"value": 185, "desc": "Conductividad Permeado", "unit": "µS/cm"},
    ...
  },
  "digitals": {
    "SP-101": {"value": true, "desc": "Bomba HP"},
    "ALRM-1": {"value": false, "desc": "Alarma Conductividad Alta"},
    ...
  }
}
```

### Componentes del dashboard

- **4 KPIs** — Producción hoy, tasa de recuperación, rechazo de sal, potencia
- **Diagrama P&ID SVG** — Captación → Bomba LP → Bomba HP → Membranas RO → Permeado/Concentrado con flujo animado
- **6 gauges** — PT-101, CT-201, TT-101, AT-101, VL-101, RECOV (con alerta visual si CT-201 > 400)
- **Gráfico de tendencias** — Chart.js con 4 series (FT-101, FT-201, PT-101, CT-201), 5 min de ventana
- **Tabla de variables** — Todos los tags con valores y estado de alarmas
- **Panel de alarmas** — ALRM-1 (conductividad), ALRM-2 (presión), estado bombas HP/LP

### Ejecución

```bash
cd dashboard
pip3 install fastapi uvicorn pymodbus
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Acceder a `http://localhost:8000`

### Arquitectura

```
Dashboard (FastAPI) ──read_holding_registers──▶ Simulador (Modbus :502)
                    ──read_coils────────────────▶ Simulador (Modbus :502)
                         ▲
                    Polling 1s (fetch /api/live)
                         │
                    Navegador (Chart.js + SVG)
```

## Demo para clientes

Ver `DEMO_SCRIPT.md` — guía completa de 15-20 minutos para presentación a clientes.

## Estructura del proyecto

```
desaladora-scada-demo/
├── simulator/
│   └── desaladora_sim.py          # Simulador Modbus TCP (puerto :502)
├── dashboard/
│   ├── api.py                     # API FastAPI (puerto :8000)
│   └── static/
│       └── index.html             # Dashboard web (P&ID + Chart.js)
├── scada/
│   ├── Projects/Desaladora/
│   │   ├── BaseXML/               # Configuración del proyecto (21 canales)
│   │   ├── Views/                 # 4 vistas .tbl
│   │   └── Desaladora.rsproj
│   ├── ScadaServerApp/Config/     # Motor SCADA
│   ├── ScadaCommApp/Config/       # Comunicador Modbus
│   ├── ScadaCommApp/drv/          # Driver Modbus
│   ├── ScadaWeb/Config/           # Interfaz web
│   └── Config/                    # Instancia
├── DEMO_SCRIPT.md                 # Guion demo clientes
├── BACKLOG.md                     # Historial de tareas
└── CLAUDE.md                      # Instrucciones del proyecto
```

## Solución de problemas

### No puedo iniciar sesión como admin

Los archivos `BaseDAT/*.dat` son binarios compilados desde `BaseXML/*.xml`. Si no funciona:
1. Abrir el proyecto en Rapid SCADA Admin
2. `File` → `Import/Export` → `Generate DAT files`
3. Reiniciar `scada-server`

### Los datos no aparecen en la web

Verificar que todos los servicios están activos:
```bash
systemctl status desaladora-sim scada-server scada-comm scada-web
```

Revisar logs:
```bash
tail -f /opt/scada/ScadaCommWkr/Log/line001.log
tail -f /opt/scada/ScadaServerWkr/Log/ScadaServer.log
```

### El simulador no responde en Modbus

```bash
# Verificar que está escuchando en puerto 502
ss -tlnp | grep 502

# Probar conexión
python3 -c "from pymodbus import client; print(client.ModbusTcpClient('localhost').connect())"
```

## Licencia

Demo interna — Rapid SCADA es software de código abierto (LGPL).
