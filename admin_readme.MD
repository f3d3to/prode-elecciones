# Administración — Guía rápida

Esta guía explica cómo acceder y usar el apartado de Administración tanto en el backend (Django) como en el frontend (SPA Vue). El panel no está visible para el usuario promedio y requiere sesión de staff.

## Requisitos previos

- Backend levantado (Django)
- Usuario con permisos `is_staff`
- Frontend levantado (Vite)
- Variables de entorno configuradas: `DEADLINE`, `VITE_API_BASE`

---

## Backend (Django REST)

Ruta base de API: `/api`

### Sesión y CSRF
- El apartado admin usa **sesión Django** + **CSRF**.
- Flujos comunes del frontend:
  1) `GET /api/admin/csrf` — entrega y setea cookie `csrftoken`.
  2) `POST /api/admin/login` — con `{ username, password }`, cabecera `X-CSRFToken` y `withCredentials`.
  3) Resto de endpoints admin con sesión activa y `withCredentials`.

### Endpoints admin
- `GET /api/admin/login` — consulta estado de sesión (responde `{ authenticated, username, is_staff }`).
- `POST /api/admin/login` — inicia sesión (requiere usuario `is_staff`).
- `POST /api/admin/logout` — cierra la sesión.
- `GET /api/admin/overview` — métricas básicas: `deadline`, `after_deadline`, conteo de pronósticos y estado de publicación de resultados.
- `POST /api/admin/reprocess` — reproceso de puntajes. En este MVP el ranking se calcula on‑the‑fly; este endpoint devuelve un resumen.
- `GET /api/admin/export/ranking.csv` — descarga un CSV del ranking calculado en el momento.
- `POST /api/admin/retry-sheets` — placeholder (501). Integración con Google Sheets no implementada en el MVP.

### Resultados oficiales (público vs staff)
- `GET /api/results` — Público. Devuelve el último resultado **publicado** o 404 con `detail: "A la espera de resultados oficiales"`.
- `POST /api/results` — Solo staff. Crea/publica resultados. Si `is_published=true` y `published_at` vacío, el backend lo setea automáticamente.

Formato esperado (ejemplo):
```json
{
  "is_published": true,
  "national_percentages": { "LLA": 32.1, "UxP": 31.7, "JxC": 24.3 },
  "participation": 72.5,
  "margin_1_2": 0.4,
  "blanco_nulo_impugnado": 3.2,
  "total_votes": 20000000,
  "provinciales": {
    "Buenos Aires": { "percentages": { "LLA": 30, "UxP": 36, "JxC": 25 }, "winner": "UxP" },
    "CABA": { "percentages": { "LLA": 27, "UxP": 22, "JxC": 45 }, "winner": "JxC" }
  }
}
```

---

## Frontend (SPA Vue)

### Acceso al panel
- Ruta: `/admin`
- No está enlazada en la barra de navegación (oculto para usuarios regulares).

### Flujo de uso
1) Abrir `/admin`.
2) Ingresar usuario/contraseña de staff. El frontend obtiene CSRF y envía `X‑CSRFToken` en los POST.
3) Ver Overview (deadline, estado de publicación, conteos).
4) Acciones disponibles:
   - Reprocesar puntajes (MVP: devuelve resumen, ranking se calcula on‑the‑fly).
   - Exportar ranking CSV.
   - Reintentar Sheets (placeholder).
5) Publicar resultados oficiales:
   - Pegar JSON en el área de texto o usar el botón “Ejemplo”.
   - Marcar/Desmarcar “Publicar (visible para el público)”.
   - Enviar. Al publicar, el frontend de Resultados y Ranking reflejará los datos.

### Páginas relacionadas
- `Resultados` (`/results`):
  - Antes de publicar: muestra "A la espera de resultados oficiales".
  - Luego de publicar: Panel Nacional y tabla Provincial.
- `Ranking` (`/ranking`):
  - Tabla con puesto, usuario, email, puntaje y fecha de envío.
  - Buscador por nombre/email (`?q=`).

---

## Notas y limitaciones del MVP
- El **scoring** y el **ranking** se calculan on‑the‑fly en el backend a partir del último `OfficialResults` publicado.
- No hay persistencia de ranking ni integración con Google Sheets en este MVP (el endpoint `retry-sheets` devuelve 501).
- Las validaciones de resultados incluyen rangos básicos y suma ≈100% en nacionales.
- CORS está habilitado para desarrollo y el backend controla el `DEADLINE`.

---

## Troubleshooting
- 403 en POST admin: asegurarse de haber llamado `GET /api/admin/csrf` y de enviar cabecera `X‑CSRFToken` con `withCredentials: true`.
- 404 en `/api/results`: aún no hay resultados publicados (`is_published=false` o no existen registros).
- El login requiere usuario con `is_staff=true` en Django.
