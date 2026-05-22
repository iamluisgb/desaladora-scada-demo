#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCADA_SRC="${SCADA_SRC:-/opt/scada}"
BIN_DIR="$ROOT_DIR/docker/scada-bin"

echo "=== Preparando binarios de Rapid SCADA desde $SCADA_SRC ==="

mkdir -p "$BIN_DIR/ScadaServerWkr" "$BIN_DIR/ScadaCommWkr" "$BIN_DIR/ScadaWeb" \
         "$BIN_DIR/ScadaServerApp" "$BIN_DIR/ScadaCommApp" "$BIN_DIR/Config"

echo "Copiando Workers..."
cp -r "$SCADA_SRC/ScadaServerWkr/"*.dll "$BIN_DIR/ScadaServerWkr/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaServerWkr/"*.json "$BIN_DIR/ScadaServerWkr/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaServerWkr/"*.pdb "$BIN_DIR/ScadaServerWkr/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaServerWkr/"*.xml "$BIN_DIR/ScadaServerWkr/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaServerWkr/"*Config* "$BIN_DIR/ScadaServerWkr/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaServerWkr/"runtimes "$BIN_DIR/ScadaServerWkr/" 2>/dev/null || true

cp -r "$SCADA_SRC/ScadaCommWkr/"*.dll "$BIN_DIR/ScadaCommWkr/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaCommWkr/"*.json "$BIN_DIR/ScadaCommWkr/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaCommWkr/"*.pdb "$BIN_DIR/ScadaCommWkr/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaCommWkr/"*.xml "$BIN_DIR/ScadaCommWkr/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaCommWkr/"*Config* "$BIN_DIR/ScadaCommWkr/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaCommWkr/"runtimes "$BIN_DIR/ScadaCommWkr/" 2>/dev/null || true

cp -r "$SCADA_SRC/ScadaWeb/"*.dll "$BIN_DIR/ScadaWeb/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaWeb/"*.json "$BIN_DIR/ScadaWeb/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaWeb/"*.pdb "$BIN_DIR/ScadaWeb/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaWeb/"*.xml "$BIN_DIR/ScadaWeb/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaWeb/wwwroot "$BIN_DIR/ScadaWeb/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaWeb/runtimes "$BIN_DIR/ScadaWeb/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaWeb/config "$BIN_DIR/ScadaWeb/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaWeb/Lang "$BIN_DIR/ScadaWeb/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaWeb/web.config "$BIN_DIR/ScadaWeb/" 2>/dev/null || true
cp -r "$SCADA_SRC/ScadaWeb/appsettings* "$BIN_DIR/ScadaWeb/" 2>/dev/null || true

echo "=== Construyendo imágenes Docker ==="

cd "$ROOT_DIR"

docker compose build

echo "=== Hecho! Ejecuta: docker compose up ==="