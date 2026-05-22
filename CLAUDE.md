# Demo: Desaladora con Rapid SCADA

## Instrucciones para Claude — Actualización del Backlog

Al completar **cada tarea individual** del plan, Claude debe actualizar [BACKLOG.md](BACKLOG.md) de la siguiente forma:

1. Marcar el ítem como completado: cambiar `- [ ]` por `- [x]`
2. Mover el ítem (con su fase) a la sección **Completado** si toda la fase terminó
3. Añadir una fila en la tabla **Registro de cambios** con la fecha actual y la tarea completada

Hacer esto **inmediatamente** después de verificar que la tarea funciona, no al final del bloque de fases.

---

## Objetivo

Construir una demo funcional de un sistema SCADA para planta desaladora (RO - Osmosis Inversa) usando Rapid SCADA v6, con datos simulados en tiempo real. La demo se mostrará a clientes.

## Entorno

- OS: Ubuntu Linux (kernel 6.1.167)
- RAM: 9.8 GB disponibles
- Disco: 73 GB libres
- Python 3.14 disponible
- Sin Docker, sin .NET preinstalado

---

## Plan de Ejecución

### Fase 1 — Instalar .NET 8 Runtime

Rapid SCADA v6 requiere .NET 8 (ASP.NET Core). Usaremos el script oficial de Microsoft ya que apt solo tiene .NET 10.

```bash
# Descargar e instalar .NET 8 via script oficial
curl -fsSL https://dot.net/v1/dotnet-install.sh | bash -s -- --channel 8.0 --install-dir /opt/dotnet
echo 'export DOTNET_ROOT=/opt/dotnet' >> ~/.bashrc
echo 'export PATH=$PATH:/opt/dotnet' >> ~/.bashrc
source ~/.bashrc
dotnet --version
```

### Fase 2 — Instalar Rapid SCADA v6

Rapid SCADA v6 se distribuye como archivo zip con binarios precompilados. La instalación en Linux es manual.

**Estructura que instalaremos en `/opt/scada/`:**

```
/opt/scada/
├── Server/       # Motor principal (ScadaServer)
├── Comm/         # Módulo de comunicación (ScadaComm)
├── Web/          # Interfaz web (ScadaWeb - ASP.NET Core)
├── Admin/        # Herramienta de administración
└── Config/       # Configuración del proyecto
```

**Pasos:**
1. Descargar Rapid SCADA 6.x desde el repositorio oficial de GitHub (rapidscada/scada-v6)
2. Extraer en `/opt/scada/`
3. Configurar permisos
4. Crear servicios systemd para Server, Comm y Web

### Fase 3 — Crear el Simulador de Desaladora

Script Python que simula los instrumentos de una planta de osmosis inversa y publica los datos vía **Modbus TCP** (protocolo que Rapid SCADA lee nativamente).

**Variables simuladas del proceso:**

| Tag | Descripción | Rango | Unidad |
|-----|-------------|-------|--------|
| FT-101 | Caudal agua de alimentación | 80–120 | m³/h |
| FT-201 | Caudal permeado (agua tratada) | 40–60 | m³/h |
| FT-301 | Caudal concentrado (rechazo) | 30–50 | m³/h |
| PT-101 | Presión alta (HP) | 55–65 | bar |
| PT-102 | Presión baja (LP entrada) | 2–4 | bar |
| PT-201 | Presión permeado | 0.5–1.5 | bar |
| CT-101 | Conductividad alimentación | 45000–55000 | µS/cm |
| CT-201 | Conductividad permeado | 100–300 | µS/cm |
| TT-101 | Temperatura agua | 18–25 | °C |
| AT-101 | pH alimentación | 6.8–7.2 | pH |
| AT-201 | pH permeado | 6.5–7.0 | pH |
| KW-101 | Potencia bomba HP | 45–55 | kW |
| SP-101 | Estado bomba HP (ON/OFF) | 0/1 | — |
| SP-102 | Estado bomba baja presión | 0/1 | — |
| VL-101 | Apertura válvula antiscalant | 0–100 | % |
| RECOV | Tasa de recuperación | 40–55 | % |
| REJEC | Tasa de rechazo de sal | 98–99.9 | % |
| PROD-H | Producción acumulada hora | acum. | m³ |
| PROD-D | Producción acumulada día | acum. | m³ |
| ALRM-1 | Alarma conductividad alta | 0/1 | — |
| ALRM-2 | Alarma presión alta | 0/1 | — |

**Archivo:** `simulator/desaladora_sim.py`

El simulador usará la librería `pymodbus` para exponer los datos como servidor Modbus TCP en el puerto 502.

### Fase 4 — Configurar Rapid SCADA

Configurar el proyecto SCADA con:

1. **Comunicador (Comm):** Línea Modbus TCP apuntando a `localhost:502`, con todos los tags mapeados a registros Modbus.

2. **Servidor (Server):** Canales para cada tag, con:
   - Límites de alarma configurados
   - Fórmulas de cálculo (ej. tasa de recuperación = FT-201/FT-101 × 100)
   - Archivos de tendencias históricas

3. **Vistas Web:** Páginas del HMI:
   - **Vista General:** Diagrama de flujo P&ID simplificado con valores en tiempo real
   - **Tendencias:** Gráficos históricos de variables principales (24h)
   - **Alarmas:** Panel de alarmas activas y registro histórico
   - **Producción:** KPIs de producción y eficiencia

### Fase 5 — Configurar Servicios

Crear servicios systemd para arranque automático:

```
scada-server.service   # Motor Rapid SCADA Server
scada-comm.service     # Communicator (Modbus reader)
scada-web.service      # Web HMI (puerto 5000)
desaladora-sim.service # Simulador Python
```

### Fase 6 — Validación y Demo

1. Verificar que todos los servicios arrancan correctamente
2. Confirmar datos en tiempo real en la web (`http://localhost:5000`)
3. Disparar alarmas de prueba manualmente (subir conductividad simulada)
4. Revisar históricos y tendencias
5. Ajustar visualización para presentación a clientes

---

## Arquitectura Final

```
┌─────────────────────────────────────────────────────────┐
│                      SERVIDOR DEMO                       │
│                                                         │
│  ┌──────────────────┐     ┌──────────────────────────┐  │
│  │  desaladora_sim  │────▶│   Rapid SCADA Comm       │  │
│  │  (Python/Modbus) │     │   (Modbus TCP client)    │  │
│  │  puerto :502     │     └──────────┬───────────────┘  │
│  └──────────────────┘                │                  │
│                                      ▼                  │
│                           ┌──────────────────────────┐  │
│                           │   Rapid SCADA Server     │  │
│                           │   (motor + historicos)   │  │
│                           └──────────┬───────────────┘  │
│                                      │                  │
│                           ┌──────────▼───────────────┐  │
│                           │   Rapid SCADA Web HMI    │  │
│                           │   http://localhost:5000  │  │
│                           └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                                    │
                          Clientes (navegador web)
```

---

## Dependencias Python

```
pymodbus>=3.6.0    # Servidor Modbus TCP para el simulador
```

---

## Credenciales Demo

- URL: `http://<IP_SERVIDOR>:5000`
- Usuario: `admin`
- Contraseña: `scada123` (configurar durante instalación)

---

## Orden de Ejecución

1. `fase1_instalar_dotnet.sh`
2. `fase2_instalar_scada.sh`
3. `fase3_simulador.sh` (instala deps Python + configura servicio)
4. `fase4_configurar_scada.sh` (copia config del proyecto)
5. `fase5_servicios.sh` (habilita e inicia todos los servicios)
6. Validación manual en el navegador

---

## Notas para la Demo con Clientes

- El simulador introduce variabilidad realista (ruido gaussiano + tendencias lentas)
- Las alarmas se disparan automáticamente cuando la conductividad del permeado supera 400 µS/cm
- Los datos históricos se precargan con 24h de historia simulada al inicio
- La tasa de recuperación y rechazo de sal se calculan en tiempo real dentro del SCADA
