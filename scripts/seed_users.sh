#!/usr/bin/env bash
# Crea cuentas de prueba usando el formulario de registro de la web.
#
# Uso:  SEED_PASSWORD=la_contraseña ./scripts/seed_users.sh [puerto]
#       (puerto por defecto: 8080 = dev; 8081 = prod)

set -u

PORT="${1:-8080}"
PASSWORD="${SEED_PASSWORD:?Falta SEED_PASSWORD. Ejemplo: SEED_PASSWORD=123456 $0 8080}"
PREFIX="hola"
START=1
END=10
BASE="http://localhost:${PORT}"

# Comprobar que la web responde antes de empezar
if [ "$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/status")" = "000" ]; then
  echo "No hay ninguna web en ${BASE}. Levanta el entorno con 'make up'."
  exit 1
fi

created=0
existing=0

for i in $(seq "$START" "$END"); do
  user="${PREFIX}${i}"
  code=$(curl -s -o /dev/null -w '%{http_code}' \
    --data-urlencode "username=${user}" \
    --data-urlencode "password=${PASSWORD}" \
    "${BASE}/register")

  case "$code" in
    302) echo "  creada      ${user}"; created=$((created + 1)) ;;
    200) echo "  ya existe   ${user}"; existing=$((existing + 1)) ;;
    *)   echo "  ERROR (${code}) ${user}" ;;
  esac
done

echo "Resultado en ${BASE}: ${created} creadas, ${existing} ya existían."