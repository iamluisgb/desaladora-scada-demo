#!/bin/bash
set -e

case "${1:-server}" in
  server)
    cd /opt/scada/ScadaServerWkr
    exec dotnet ScadaServerWkr.dll
    ;;
  comm)
    cd /opt/scada/ScadaCommWkr
    exec dotnet ScadaCommWkr.dll
    ;;
  web)
    cd /opt/scada/ScadaWeb
    export ASPNETCORE_URLS=http://0.0.0.0:5000
    exec dotnet ScadaWeb.dll
    ;;
  *)
    exec "$@"
    ;;
esac