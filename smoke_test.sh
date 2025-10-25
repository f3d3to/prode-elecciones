#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
FRONTEND_URL=${FRONTEND_URL:-http://localhost:5173}

# 1) Backend metadata
meta=$(curl -fsS "$BACKEND_URL/api/metadata")
echo "[OK] backend metadata: fuerzas=$(echo "$meta" | jq '.fuerzas|length') provincias=$(echo "$meta" | jq '.provincias|length')"

# 2) Backend health
health=$(curl -fsS "$BACKEND_URL/api/health")
echo "[OK] backend health: $(echo "$health" | jq -r '.status') db=$(echo "$health" | jq -r '.db')"

# 3) Create/Upsert prediction
payload='{"email":"smoke@example.com","username":"Smoke","top3":["LLA","UxP","JxC"],"national_percentages":{"LLA":40,"UxP":30,"JxC":20,"FIT":5,"Fuerza Patria":5},"participation":70,"margin_1_2":3.2,"blanco_nulo_impugnado":2.5, "provinciales": {"CABA": {"porcentajes": {"LLA": 40, "UxP": 35, "JxC": 20, "FIT": 3, "Fuerza Patria": 2}, "winner": "LLA"}}, "bonus": {"mas_renida": "CABA", "cambia_ganador": "CABA", "fit_mayor": "CABA", "lla_mas_crece": "CABA", "fuerza_patria_mayor": "CABA"}}'
res=$(echo -n "$payload" | curl -fsS -H 'Content-Type: application/json' --data-binary @- "$BACKEND_URL/api/predictions")
echo "[OK] backend save: $(echo "$res" | jq -r '.email') updated=$(echo "$res" | jq -r '.updated_at')"

# 4) Fetch mine
mine=$(curl -fsS "$BACKEND_URL/api/predictions/mine?email=smoke@example.com")
echo "[OK] backend fetch: top3_0=$(echo "$mine" | jq -r '.top3[0]') LLA=$(echo "$mine" | jq -r '.national_percentages["LLA"]')"

# 5) Frontend served
html=$(curl -fsS "$FRONTEND_URL" | head -n 1)
echo "[OK] frontend: $(echo "$html" | tr -d '\r')"

# 6) Frontend -> Backend CORS probe via Origin
cors_deadline=$(curl -fsS -H "Origin: $FRONTEND_URL" -H "Referer: $FRONTEND_URL/" "$BACKEND_URL/api/metadata" | jq -r '.deadline')
echo "[OK] cors: deadline=$cors_deadline"

echo "All smoke tests passed."