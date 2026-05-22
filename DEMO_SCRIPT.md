# Guion de Demo — Planta Desaladora RO (Osmosis Inversa)

> **Público:** Clientes potenciales / Stakeholders
> **Duración estimada:** 15–20 minutos
> **URL:** `http://<IP_SERVIDOR>:5000`
> **Usuario:** `admin` / **Contraseña:** `scada123`

---

## 0. Preparación (antes de la demo)

```bash
# Verificar que todos los servicios estén activos
sudo systemctl is-active desaladora-sim scada-server scada-comm scada-web
# Los 4 deben devolver: active

# Verificar puertos
sudo ss -tlnp | grep -E '502|5000|10000'
# Deben aparecer: :502 (simulador), :10000 (server), :5000 (web)
```

---

## 1. Introducción (2 min)

> "Les voy a mostrar un sistema SCADA completo para una planta de desalación por ósmosis inversa, corriendo en tiempo real sobre Linux con Rapid SCADA v6 de código abierto."

**Puntos clave:**
- Plataforma 100% open-source (Rapid SCADA + Python)
- Corriendo en Ubuntu Linux sobre hardware estándar
- Datos simulados en tiempo real con variabilidad realista
- 21 canales de proceso monitoreados

---

## 2. Vista General — Diagrama de Flujo (4 min)

Abrir `http://<IP>:5000` → Login → **Vista General**

> "Esta es la vista principal. Muestra todos los parámetros críticos de la planta en una sola pantalla."

**Recorrer los grupos de datos:**

| Grupo | Qué mostrar | Valores típicos |
|-------|-------------|-----------------|
| **Caudales** | FT-101, FT-201, FT-301 | ~100, ~50, ~50 m³/h |
| **Presiones** | PT-101 (HP), PT-102 (LP), PT-201 | ~60, ~3, ~1 bar |
| **Calidad de Agua** | CT-101, CT-201, TT-101, AT-101, AT-201 | ~50000, ~200, ~22°C, ~7.0 pH |
| **Equipos** | SP-101, SP-102 (bombas ON/OFF) | ON / ON |
| **Eficiencia** | RECOV (recuperación), REJEC (rechazo sal) | ~50%, ~99.4% |
| **Producción** | PROD-H (hora), PROD-D (día) | Acumulados en m³ |
| **Alarmas** | ALRM-1 (conductividad), ALRM-2 (presión) | Off / Off |

**Punto de énfasis:**
> "Los valores se actualizan en tiempo real cada segundo. Las bombas HP y LP están encendidas, la planta está operando normalmente."

---

## 3. Simulación en Tiempo Real (2 min)

> "El simulador genera datos realistas con ruido gaussiano, tendencias cíclicas y variaciones operativas."

**Mostrar variación natural:**
- Esperar 10-15 segundos para que los valores cambien visiblemente
- Señalar cómo caudales y presiones fluctúan naturalmente
> "Pueden ver cómo los valores varían suavemente, como en una planta real."

---

## 4. Disparar una Alarma (3 min)

> "Ahora voy a simular un problema real: un aumento de conductividad en el permeado que indica una falla en las membranas."

**Acción:**
```bash
# Simular conductividad alta (>400 µS/cm)
echo "" > /tmp/trigger_alarm
```

**Qué esperar:**
- CT-201 salta a 500 µS/cm instantáneamente
- ALRM-1 se activa (muestra "On" en rojo)
- Se genera un evento de alarma en el sistema

> "La alarma se disparó automáticamente porque la conductividad del permeado superó el límite de 400 µS/cm. Esto indicaría una posible degradación de las membranas RO."

**Para revertir:**
```bash
rm /tmp/trigger_alarm
```

**Qué esperar:**
- CT-201 vuelve a ~200 µS/cm
- ALRM-1 se desactiva automáticamente

---

## 5. Vista Alarmas y Estado (2 min)

Navegar a **Alarmas y Estado**

> "Aquí tenemos un panel dedicado a las alarmas y las variables críticas del proceso."

**Secciones:**
1. **Alarmas Activas** — ALRM-1 y ALRM-2 con estado On/Off
2. **Conductividad** — Alimentación y permeado comparados
3. **Presión** — Las tres presiones del proceso
4. **Estado Equipos** — Bombas HP y LP
5. **pH** — Alimentación y permeado
6. **Temperatura** — Agua de alimentación

**Punto de énfasis:**
> "Esta vista permite al operador tener un panorama rápido del estado de salud de la planta. Las alarmas se ordenan por prioridad y se registra cada cambio de estado."

---

## 6. Vista Producción y KPIs (2 min)

Navegar a **Producción y KPIs**

> "Esta vista se enfoca en la eficiencia y producción de la planta."

**Secciones:**
1. **Producción Acumulada** — Hora y día en m³
2. **Recuperación y Rechazo** — RECOV (~50%) y REJEC (~99.4%)
3. **Caudales** — Alimentación, permeado y concentrado
4. **Potencia** — Consumo de la bomba HP (~50 kW)
5. **Válvula Antiscalant** — Apertura (~65%)

**Punto de énfasis:**
> "La tasa de recuperación del 50% es típica de una planta RO de doble paso. El rechazo de sal del 99.4% indica un buen desempeño de las membranas."

---

## 7. Tendencias 24h (2 min)

Navegar a **Tendencias 24h**

> "Los datos históricos se almacenan a nivel de minuto y se consolidan por hora. Aquí pueden ver las tendencias de las últimas 24 horas."

**Mostrar:**
- Caudales y presiones (gráfico de líneas)
- Conductividad y eficiencia
- Producción acumulada

**Punto de énfasis:**
> "El sistema archiva automáticamente datos cada minuto, con retención configurable. Esto permite análisis de eficiencia, detección de tendencias y reporting."

---

## 8. Arquitectura del Sistema (1 min)

> "Para que entiendan cómo funciona por debajo:"

```
┌──────────────────────────────────────────────┐
│              SERVIDOR DEMO                    │
│                                              │
│  Simulador Python (Modbus TCP :502)          │
│    └─ 21 tags: 17 analógicos + 4 digitales   │
│              │                               │
│  Rapid SCADA Communicator (lee Modbus)       │
│    └─ Driver Modbus TCP → valores en memoria │
│              │                               │
│  Rapid SCADA Server (motor principal)        │
│    └─ Alarmas, históricos, fórmulas, eventos │
│              │                               │
│  Rapid SCADA Web HMI (puerto :5000)          │
│    └─ 4 vistas: General, Tendencias,         │
│       Alarmas, Producción                    │
└──────────────────────────────────────────────┘
```

**Stack tecnológico:**
- **Simulador:** Python 3 + pymodbus (servidor Modbus TCP)
- **SCADA:** Rapid SCADA v6 (open-source, .NET 8)
- **Base de datos:** Archivos binarios DAT (minuto/hora)
- **Web:** ASP.NET Core + Bootstrap + Chart.js
- **Protocolo:** Modbus TCP (estándar industrial)

---

## 9. Cierre y Preguntas (2-3 min)

> "Este es un sistema SCADA completo, funcional y en tiempo real, construido 100% con software open-source. Puede escalarse a cualquier cantidad de dispositivos y canales."

**Puntos de cierre:**
- Código fuente disponible (GitHub Rapid SCADA)
- Protocolo abierto Modbus TCP
- Sin licencias ni costos de software
- Deployable en cualquier servidor Linux
- Extensible con drivers Modbus, OPC-UA, etc.

---

## Apéndice: Referencias Rápidas

### Credenciales
| Campo | Valor |
|-------|-------|
| URL | `http://<IP>:5000` |
| Usuario | `admin` |
| Contraseña | `scada123` |

### Canales del Proceso

| Canal | Tag | Descripción | Unidad | Rango |
|-------|-----|-------------|--------|-------|
| 101 | FT-101 | Caudal alimentación | m³/h | 80-120 |
| 102 | FT-201 | Caudal permeado | m³/h | 40-60 |
| 103 | FT-301 | Caudal concentrado | m³/h | 30-50 |
| 104 | PT-101 | Presión alta HP | bar | 55-65 |
| 105 | PT-102 | Presión baja LP | bar | 2-4 |
| 106 | PT-201 | Presión permeado | bar | 0.5-1.5 |
| 107 | CT-101 | Conductividad alimentación | µS/cm | 45000-55000 |
| 108 | CT-201 | Conductividad permeado | µS/cm | 100-300 |
| 109 | TT-101 | Temperatura | °C | 18-25 |
| 110 | AT-101 | pH alimentación | pH | 6.8-7.2 |
| 111 | AT-201 | pH permeado | pH | 6.5-7.0 |
| 112 | KW-101 | Potencia bomba HP | kW | 45-55 |
| 113 | SP-101 | Estado bomba HP | ON/OFF | 0/1 |
| 114 | SP-102 | Estado bomba LP | ON/OFF | 0/1 |
| 115 | VL-101 | Válvula antiscalant | % | 0-100 |
| 116 | RECOV | Tasa recuperación | % | 40-55 |
| 117 | REJEC | Tasa rechazo sal | % | 98-99.9 |
| 118 | PROD-H | Producción hora | m³ | acum. |
| 119 | PROD-D | Producción día | m³ | acum. |
| 120 | ALRM-1 | Alarma conductividad alta | On/Off | 0/1 |
| 121 | ALRM-2 | Alarma presión alta | On/Off | 0/1 |

### Disparar Alarma de Prueba
```bash
# Activar conductividad alta (simula falla de membranas)
echo "" > /tmp/trigger_alarm

# Desactivar
rm /tmp/trigger_alarm
```

### Servicios
```bash
sudo systemctl status desaladora-sim scada-server scada-comm scada-web
```

### Archivos Clave
| Archivo | Propósito |
|---------|-----------|
| `simulator/desaladora_sim.py` | Simulador Modbus TCP |
| `/opt/scada/ScadaCommWkr/Config/DrvModbus_Desaladora.xml` | Mapeo Modbus |
| `/opt/scada/Views/Desaladora/` | Vistas web HMI |
| `/opt/scada/Archive/Min/` | Históricos minuto a minuto |
| `/opt/scada/Archive/Hour/` | Históricos consolidados |
