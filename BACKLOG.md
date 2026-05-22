# Backlog — Demo Desaladora Rapid SCADA

## Estado general: FASE 7 — Mejoras de alto impacto 🚀

---

## Pendiente

### Fase 7 — Mejoras de alto impacto
- [x] **Docker Compose** — Contenerizar todo el stack (sim, server, comm, web, dash)
- [x] **Modbus writes** — Encender/apagar bombas, ajustar válvula desde dashboard HTML + API PUT
- [x] **API de históricos** — Endpoints /api/kpis y /api/trends desde datos en vivo
- [x] **Dashboard responsive** — Vista adaptada a tablet/mobile con 3 breakpoints
- [x] **Simular fallo de membrana** — Botón que fuerza CT-201 a 500 µS/cm durante 10s

---

## Completado

### Fase 5 — Servicios systemd ✓
- [x] Crear `scada-server.service`
- [x] Crear `scada-comm.service`
- [x] Crear `scada-web.service`
- [x] Crear `desaladora-sim.service`
- [x] Habilitar e iniciar todos los servicios
- [x] Verificar estado con `systemctl status`

### Fase 3 — Simulador de Desaladora ✓
- [x] pymodbus 3.13 instalado
- [x] simulator/desaladora_sim.py con 21 tags (SimDevice API nueva)
- [x] Puerto 502 escuchando, 17 analógicos verificados con lectura Modbus

### Fase 2 — Instalar Rapid SCADA v6 ✓
- [x] Código fuente descargado de GitHub (v6.4.6)
- [x] Compilado con dotnet build (ScadaCommon, Server, Comm, Web, drivers Modbus)
- [x] Publicado en /opt/scada/ (ScadaServerApp, ScadaCommApp, ScadaWeb, ScadaAgentApp)
- [x] Proyecto Desaladora creado con 21 canales en BaseXML
- [x] BaseXML convertido a BaseDAT (21 canales cnl.dat)
- [x] Configs de instancia desplegadas a directorios de runtime

### Fase 1 — Instalar .NET 8 Runtime ✓
- [x] Descargar dotnet-install.sh desde Microsoft
- [x] Instalar .NET 8 en `/opt/dotnet`
- [x] Configurar variables de entorno (DOTNET_ROOT, PATH)
- [x] Verificar: `dotnet --version` devuelve `8.x.x`

---

## Registro de cambios

| Fecha | Tarea completada |
|-------|-----------------|
| 2026-05-22 | Fase 1 completa: .NET 8.0.421 instalado en /opt/dotnet, libicu instalado, vars de entorno configuradas |
| 2026-05-22 | Fase 2 completa: Rapid SCADA v6.4.6 compilado e instalado, proyecto Desaladora con 21 canales creado |
| 2026-05-22 | Fase 3 completa: simulador Python Modbus TCP escuchando en :502, 17 analógicos verificados |
| 2026-05-22 | Fase 5 completa: 4 servicios systemd creados, habilitados y activos |
| 2026-05-22 | Fase 4 parcial: proyecto con 21 canales, línea Modbus TCP, alarmas, fórmulas, vista General y Tendencias completadas |
| 2026-05-22 | Fase 6 parcial: datos en tiempo real confirmados en http://localhost:5000 (21 canales con valores correctos) |
| 2026-05-22 | Bug fix: Alarmas digitales (ALRM1) no se propagaban por Modbus — corregido mapeo de coils en SimDevice (address=0 + action callback reempaquetado) |
| 2026-05-22 | Validación: Rapid SCADA lee coils correctamente — respuesta Modbus `01 01 07` (SP101=T, SP102=T, ALRM1=T, ALRM2=F) al disparar alarma, y `01 01 03` (ALRM1=F) al normalizar |
| 2026-05-22 | Vista Alarmas completada: alarmas activas, conductividad, presión, equipos, pH, temperatura |
| 2026-05-22 | Vista Producción completada: producción acumulada, recuperación/rechazo, caudales, potencia, válvula |
| 2026-05-22 | Históricos validados: archives Min/Hour activos, eventos generados para todos los canales digitales |
| 2026-05-22 | Demo lista para clientes: 4 vistas configuradas, datos en tiempo real, alarmas funcionales, históricos operativos |
| 2026-05-22 | Script de demo creado: DEMO_SCRIPT.md con guion completo de 15-20 min para clientes |
| 2026-05-22 | Bug fix: Formatos de canales corregidos de hexadecimal (X8/X2) a decimal (N0/N1/N2), cnl.dat regenerado |
| 2026-05-22 | Dashboard visual creado: API FastAPI en :8000, P&ID animado, gauges, gráficos de tendencia, panel de variables |
| 2026-05-22 | Docker Compose: 5 servicios (sim, server, comm, web, dash) con Dockerfiles y build script |
| 2026-05-22 | Modbus writes: dashboard con botones toggle para bombas + slider válvula + Simular fallo. API POST /api/write con override file IPC |
| 2026-05-22 | API KPIs: /api/kpis (producción, recuperación, presiones, alarmas) y /api/trends con ventana configurable |
| 2026-05-22 | Dashboard responsive: 3 breakpoints (1024/768/480px) para tablet y mobile |
| 2026-05-22 | Fase 7 completa: Docker, writes, KPIs, responsive, fallo simulado ✓ |
