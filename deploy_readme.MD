# Prode 2025 — Runbook (MVP)

Esta guía te deja el proyecto corriendo en minutos, sin sobreingeniería.

## Requisitos
- Linux/macOS
- Python 3.11+
- Node.js 18+

## 1) Backend (Django + DRF)

1. Crear entorno y deps
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

2. Variables de entorno (copiar ejemplo y ajustar si hace falta)
```bash
cp .env.example .env
# Editá DEADLINE, ALLOWED_ORIGINS si fuera necesario
```

3. Migraciones y runserver
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Endpoints relevantes (MVP):
- GET http://localhost:8000/api/metadata
- GET http://localhost:8000/api/predictions/mine?email=mail@ejemplo.com
- POST http://localhost:8000/api/predictions

Notas:
- El backend aplica check de `DEADLINE` para POST (403 post-cierre).
- Valida fuerzas/provincias contra `prode/static/*.json`.

## 2) Frontend (Vite + Vue 3)

1. Instalar deps
```bash
cd ../frontend
npm install
```

2. Variables de entorno (copiar ejemplo)
```bash
cp .env.example .env
# VITE_API_BASE apunta al backend (por defecto http://localhost:8000)
# VITE_DEADLINE controla la cuenta regresiva del Home
```

3. Correr el dev server
```bash
npm run dev
```

- App en http://localhost:5173
- Navegación:
  - Inicio → cuenta regresiva
  - Jugar → formulario MVP (precarga por email, guarda antes del deadline)
  - Resultados/Ranking → placeholders del MVP

## 3) Datos y validaciones
- Fuerzas válidas: `backend/prode/static/fuerzas.json`
- Provincias válidas: `backend/prode/static/provincias.json`
- Cambios en estos archivos no requieren migraciones.

## 4) Variables de entorno
Backend (`backend/.env`):
```
DEBUG=1
DJANGO_SECRET_KEY=change-me
ALLOWED_HOSTS=*
ALLOWED_ORIGINS=http://localhost:5173
DEADLINE=2025-11-01T00:00:00Z
```

Frontend (`frontend/.env`):
```
VITE_API_BASE=http://localhost:8000
VITE_DEADLINE=2025-11-01T23:59:00Z
```

## 5) Opcional — Docker rápido (dev)

Si preferís containers, podés usar este esquema básico (no incluido por defecto):
- Backend: Python 3.11, expone 8000
- Frontend: Node 18, expone 5173
- Montar el código como volumen para hot-reload

## 6) Troubleshooting
- CORS: asegurate que `ALLOWED_ORIGINS` en backend incluya la URL del frontend.
- Precarga por email: en Jugar, al cambiar el email se intenta GET `/api/predictions/mine`.
- 403 al guardar: probablemente el `DEADLINE` ya pasó.

## 7) Qué incluye el MVP
- Flujo mínimo: Home (countdown) → Play (form nacional) → guardar/precargar.
- Validaciones suaves en frontend y estrictas mínimas en backend.
- Estructura lista para expandir a provinciales/bonus y ranking real.

