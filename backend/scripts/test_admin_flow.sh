#!/usr/bin/env bash
# Script de prueba del apartado de Administración usando curl
# Requiere: backend corriendo en http://localhost:8000
# Crea usuario admin: admin / 1234 (si no existe), hace login por sesión, overview, reproceso, export CSV y logout.
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000}"
USER="${ADMIN_USER:-admin}"
PASS="${ADMIN_PASS:-1234}"
COOKIE_JAR="$(mktemp)"
CSRF=""

cleanup() { rm -f "$COOKIE_JAR" || true; }
trap cleanup EXIT

step() { echo -e "\n==> $*"; }

step "Creando/asegurando usuario admin ($USER)"
python manage.py ensure_admin --username "$USER" --password "$PASS"

step "Obteniendo CSRF y cookies"
# Obtener CSRF y setear cookie csrftoken
CSRF=$(curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" -X GET "$BASE_URL/api/admin/csrf" | python -c 'import sys,json; print(json.load(sys.stdin).get("csrfToken",""))')
echo "CSRF: ${CSRF:0:6}..."

step "Login de sesión"
curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" -H "X-CSRFToken: $CSRF" -H 'Content-Type: application/json' \
  -X POST "$BASE_URL/api/admin/login" \
  -d "{\"username\": \"$USER\", \"password\": \"$PASS\"}"

step "Overview"
curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" -X GET "$BASE_URL/api/admin/overview" | jq . || true

step "Reprocesar (MVP)"
curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" -H "X-CSRFToken: $CSRF" -X POST "$BASE_URL/api/admin/reprocess" | jq . || true

step "Exportar ranking CSV (guardado en ./ranking_test.csv)"
curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" -L -o ranking_test.csv "$BASE_URL/api/admin/export/ranking.csv" || true
ls -lh ranking_test.csv || true

step "Logout"
curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" -H "X-CSRFToken: $CSRF" -X POST "$BASE_URL/api/admin/logout" | jq . || true

echo -e "\nFlujo admin OK"
