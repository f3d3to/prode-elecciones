# 🗳️ PRODE ELECTORAL LEGISLATIVO 2025 — Especificación reformulada y unificada

---

## 1️⃣ Experiencia del usuario — qué ve y qué responde

### Inicio e identificación

El usuario ingresa al sitio y ve una **portada con cuenta regresiva** hasta el cierre del prode. Las acciones visibles son “Jugar”, “Resultados” y “Ranking”; la pestaña “Administración” está oculta y solo accesible a staff.
Al presionar “Jugar”, aparece un modal de **identificación mínima** con dos campos obligatorios:

* **Nombre de usuario** (texto libre UTF-8).
* **Email** (único y con formato válido).

No hay registro ni contraseñas. Si el correo ya participó, se **precarga** su pronóstico y puede **editarlo hasta el deadline**.

### Pestaña “Nacional”

Presenta las preguntas **centrales** del prode, ligadas al puntaje principal.
El usuario debe:

* Ordenar el **Top-3** de fuerzas (desde la lista de fuerzas definidas en `fuerzas.json`).
* Asignar **porcentajes por fuerza nacional** (la suma debe ser ≈ 100 %).
* Estimar el **porcentaje de participación**.
* Calcular el **margen entre 1.º y 2.º**.
* Completar el **voto blanco/nulo/impugnado** y, opcionalmente, el **total de votos**.

El frontend valida rangos (0–100 %) y coherencia, mostrando advertencias pero sin bloquear el avance.

### Pestaña “Provinciales”

El usuario carga pronósticos para 8–12 provincias clave (extraídas de `provincias.json`).
Para cada provincia:

* % por fuerza (solo las predefinidas).
* Fuerza dominante (selección única).

La UI impide ingresar nombres de fuerzas o provincias no registradas.

### Pestaña “Bonus y especiales”

Campos de puntaje secundario:

* Provincia más reñida.
* Provincia que cambia de ganador respecto 2023.
* Donde **FIT** saca mayor %.
* Donde **LLA** más crece.
* Donde **Fuerza Patria** obtiene mayor %.

### Pestaña “Resumen y envío”

Muestra todo lo ingresado, el estado de sincronización (“Guardado / Pendiente”), y un botón **Guardar** activo solo antes del cierre.

### Post-deadline

Cuando la cuenta regresiva llega a cero, las pestañas se vuelven **solo lectura** y aparece el cartel **“Elecciones finalizadas”**.
El jugador aún puede ver su pronóstico, pero no modificarlo.

### Resultados y ranking

Antes de la publicación oficial: mensaje **“A la espera de resultados oficiales”**.
Luego:

* Panel **Nacional** con porcentajes reales.
* Panel **Provincial** con tabla de resultados por distrito.
* **Ranking general** con posición, usuario, puntaje total, medallas, bonus y fecha de envío.

El buscador permite filtrar por nombre o email.

### Administración (staff con login de sesión)

Acceso oculto en menú. Solo visible para usuarios con credenciales definidas en base o variables de entorno. Permite:

* Subir resultados oficiales.
* Ejecutar el **reprocesamiento de puntajes**. (El puntaje se recalcula automáticamente al publicar resultados. El botón de reprocesamiento permite forzar un recálculo manual (útil si se corrigen resultados).)
* Reintentar sincronizaciones con Google Sheets.
* Exportar ranking a CSV.
* Ver métricas del sistema (deadline, conteos, sincronización, estado del cronómetro).

---

## 2️⃣ Flujo cronológico del usuario

1. Ingresa al **inicio** y observa la cuenta regresiva.
2. Toca **Jugar**, completa nombre y email.
3. Avanza por **Nacional → Provinciales → Bonus**, completando cada sección.
4. Revisa el **Resumen** y presiona **Guardar** antes del `DEADLINE`.
5. Si intenta guardar luego del cierre, ve “Elecciones finalizadas”.
6. Cuando se publiquen resultados, puede acceder a **Resultados**, **Puntaje bonus** y **Ranking general**.

---

## 3️⃣ Funcionamiento técnico — soporte del flujo

* **Archivos estáticos** (`fuerzas.json`, `provincias.json`) definen los únicos valores válidos; si un valor no coincide, el backend rechaza el envío.
* **Deadline** en variable de entorno (`DEADLINE` / `VITE_DEADLINE`, ISO-UTC); el **backend es autoridad final**.
* **Dual-write:** cada “Guardar” persiste en **base relacional** (fuente de verdad) y refleja en **Google Sheets** (`pronosticos`).

  * Si falla Sheets, se marca `sync_pending = true` y se puede reintentar desde Administración.
* **Unicidad por email:** antes del deadline, el envío **actualiza** si ya existe; después del cierre, la API responde 403.
* **Resultados oficiales:** cargados por staff; se guardan en base y en la hoja `resultados_oficiales`.
* **Scoring:** tras publicar resultados, el backend calcula **puntaje principal** (error absoluto sobre campos “importantes”) y **bonus** (reglas fijas), y expone `/api/score` (estructuras reducidas, sin payloads sensibles).

---

## 4️⃣ Diagrama integral del sistema

```
             ┌──────────────────────────────┐
             │          Usuario             │
             │ (Inicio → Jugar → Prode)     │
             └──────────────┬───────────────┘
                            │
                            ▼
                  [ SPA Vue Frontend ]
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
  GET /api/predictions/mine │  POST /api/predictions (deadline check)
 (precarga por email)        │
          │                 │
          ▼                 ▼
     [BD principal]  ⇆  [Google Sheets: pronosticos]
                            │
                     (sync_pending si falla)
                            │
                            ▼
            [Admin login → POST /api/results]
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
 [BD: resultados_oficiales]       [Sheets: resultados_oficiales]
                            │
                  Script de scoring backend
                            ▼
          [BD: ranking_calculado] ⇆ [Sheets: ranking]
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
 [SPA: Resultados]                   [SPA: Ranking público]
```

---

## 5️⃣ Tecnologías y arquitectura (backend y frontend)

### Backend (Django)

* **Framework**: **Django 5** con **Django REST Framework** para la API.
* **Base de datos**: **PostgreSQL** (o SQLite en desarrollo).
* **Autenticación administrativa**: **sesiones Django** con CSRF activo para la pestaña “Administración”; usuarios `is_staff`.
* **Documentación**: **drf-spectacular** (OpenAPI JSON y UI de docs).
* **Sincronización con Google Sheets**: **gspread** + **google-auth**. Pestañas: `pronosticos`, `resultados_oficiales`, `ranking`.
* **Configuración por entorno**: `DEADLINE` (ISO-UTC), `SHEETS_SPREADSHEET_ID`, `ALLOWED_ORIGINS`, credenciales del Service Account.
* **Validaciones**:

  * Deadline en el endpoint de escritura de pronósticos.
  * Chequeo contra listas de **fuerzas** y **provincias** cargadas desde archivos estáticos.
  * Unicidad por **email** y edición permitida hasta el cierre.
* **Scoring**: motor interno que calcula puntaje principal (error absoluto ponderado, orden Top-3, participación y margen) y puntaje bonus (reglas fijas).
* **Observabilidad**: logging de sincronización con Sheets y de reprocesos; métricas básicas en `/api/admin/overview`. Válidación visual de problemas simples.
* **CORS**: habilitado únicamente para el dominio del frontend; soporte a credenciales para la sesión admin.
* **Despliegue**: contenedorizable; variables inyectadas por entorno; migraciones gestionadas por Django.

### Frontend (Vue.js 3)

* **Framework**: **Vue 3** (Composition API) con **TypeScript**.
* **Bundler**: **Vite**.
* **Estado global**: **Pinia** (stores para jugador, prode, resultados y administración).
* **Router**: **Vue Router** (rutas: Inicio, Prode con subtabs, Resultados, Ranking, Administración).
* **UI**: **Vuetify** como framework de componentes (inputs, tablas, modales, alerts, layouts responsivos).
* **HTTP**: **Axios** con manejo de estados (cargando, éxito, pendiente de sync) y tratamiento de 403 post-deadline.
* **Config por entorno**: `VITE_DEADLINE` (ISO-UTC), `VITE_API_BASE`.
* **UX**: validaciones suaves (rangos 0–100, suma ≈ 100 %), **cuenta regresiva**, bloqueo visual post-deadline, precarga por email, buscador en ranking, exportación a CSV (vía API admin).
* **Acceso admin**: login de sesión (form simple), vistas de carga de resultados, reintento de sincronización y métricas.

# 🗳️ PRODE ELECTORAL LEGISLATIVO 2025 — Especificación reformulada y unificada

---

## 1️⃣ Experiencia del usuario — qué ve y qué responde

### Inicio e identificación

El usuario ingresa al sitio y ve una **portada con cuenta regresiva** hasta el cierre del prode. Las acciones visibles son “Jugar”, “Resultados” y “Ranking”; la pestaña “Administración” está oculta y solo accesible a staff.
Al presionar “Jugar”, aparece un modal de **identificación mínima** con dos campos obligatorios:

* **Nombre de usuario** (texto libre UTF-8).
* **Email** (único y con formato válido).

No hay registro ni contraseñas. Si el correo ya participó, se **precarga** su pronóstico y puede **editarlo hasta el deadline**.

### Pestaña “Nacional”

Presenta las preguntas **centrales** del prode, ligadas al puntaje principal.
El usuario debe:

* Ordenar el **Top-3** de fuerzas (desde la lista de fuerzas definidas en `fuerzas.json`).
* Asignar **porcentajes por fuerza nacional** (la suma debe ser ≈ 100 %).
* Estimar el **porcentaje de participación**.
* Calcular el **margen entre 1.º y 2.º**.
* Completar el **voto blanco/nulo/impugnado**.

El frontend valida rangos (0–100 %) y coherencia, mostrando advertencias pero sin bloquear el avance.

### Pestaña “Provinciales”

El usuario carga pronósticos para 8–12 provincias clave (extraídas de `provincias.json`).
Para cada provincia:

* % por fuerza (solo las predefinidas).
* Fuerza dominante (selección única).

La UI impide ingresar nombres de fuerzas o provincias no registradas.

### Pestaña “Bonus y especiales”

Campos de puntaje secundario:

* Provincia más reñida.
* Provincia que cambia de ganador respecto 2023.
* Donde **FIT** saca mayor %.
* Donde **LLA** más crece.
* Donde **Fuerza Patria** obtiene mayor %.

### Pestaña “Resumen y envío”

Muestra todo lo ingresado, el estado de sincronización (“Guardado / Pendiente”), y un botón **Guardar** activo solo antes del cierre.

### Post-deadline

Cuando la cuenta regresiva llega a cero, las pestañas se vuelven **solo lectura** y aparece el cartel **“Elecciones finalizadas”**.
El jugador aún puede ver su pronóstico, pero no modificarlo.

### Resultados y ranking

Antes de la publicación oficial: mensaje **“A la espera de resultados oficiales”**.
Luego:

* Panel **Nacional** con porcentajes reales.
* Panel **Provincial** con tabla de resultados por distrito.
* **Ranking general** con posición, usuario, puntaje total, medallas, bonus y fecha de envío.

El buscador permite filtrar por nombre o email.

### Administración (staff con login de sesión)

Acceso oculto en menú. Solo visible para usuarios con credenciales definidas en base o variables de entorno. Permite:

* Subir resultados oficiales.
* Ejecutar el **reprocesamiento de puntajes**.
* Reintentar sincronizaciones con Google Sheets.
* Exportar ranking a CSV.
* Ver métricas del sistema (deadline, conteos, sincronización, estado del cronómetro).

---

## 2️⃣ Flujo cronológico del usuario

1. Ingresa al **inicio** y observa la cuenta regresiva.
2. Toca **Jugar**, completa nombre y email.
3. Avanza por **Nacional → Provinciales → Bonus**, completando cada sección.
4. Revisa el **Resumen** y presiona **Guardar** antes del `DEADLINE`.
5. Si intenta guardar luego del cierre, ve “Elecciones finalizadas”.
6. Cuando se publiquen resultados, puede acceder a **Resultados**, **Puntaje bonus** y **Ranking general**.

---

## 3️⃣ Funcionamiento técnico — soporte del flujo

* **Archivos estáticos** (`fuerzas.json`, `provincias.json`) definen los únicos valores válidos; si un valor no coincide, el backend rechaza el envío.
* **Deadline** en variable de entorno (`DEADLINE` / `VITE_DEADLINE`, ISO-UTC); el **backend es autoridad final**.
* **Dual-write:** cada “Guardar” persiste en **base relacional** (fuente de verdad) y refleja en **Google Sheets** (`pronosticos`).

  * Si falla Sheets, se marca `sync_pending = true` y se puede reintentar desde Administración.
* **Unicidad por email:** antes del deadline, el envío **actualiza** si ya existe; después del cierre, la API responde 403.
* **Resultados oficiales:** cargados por staff; se guardan en base y en la hoja `resultados_oficiales`.
* **Scoring:** tras publicar resultados, el backend calcula **puntaje principal** (error absoluto sobre campos “importantes”) y **bonus** (reglas fijas), y expone `/api/score` (estructuras reducidas, sin payloads sensibles).

---

## 4️⃣ Diagrama integral del sistema

```
             ┌──────────────────────────────┐
             │          Usuario             │
             │ (Inicio → Jugar → Prode)     │
             └──────────────┬───────────────┘
                            │
                            ▼
                  [ SPA Vue Frontend ]
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
  GET /api/predictions/mine │  POST /api/predictions (deadline check)
 (precarga por email)        │
          │                 │
          ▼                 ▼
     [BD principal]  ⇆  [Google Sheets: pronosticos]
                            │
                     (sync_pending si falla)
                            │
                            ▼
            [Admin login → POST /api/results]
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
 [BD: resultados_oficiales]       [Sheets: resultados_oficiales]
                            │
                  Script de scoring backend
                            ▼
          [BD: ranking_calculado] ⇆ [Sheets: ranking]
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
 [SPA: Resultados]                   [SPA: Ranking público]
```

---

## 5️⃣ Tecnologías y arquitectura (backend y frontend)

### Backend (Django)

* **Framework**: **Django 5** con **Django REST Framework** para la API.
* **Base de datos**: **PostgreSQL** (o SQLite en desarrollo).
* **Autenticación administrativa**: **sesiones Django** con CSRF activo para la pestaña “Administración”; usuarios `is_staff`.
* **Documentación**: **drf-spectacular** (OpenAPI JSON y UI de docs).
* **Sincronización con Google Sheets**: **gspread** + **google-auth**. Pestañas: `pronosticos`, `resultados_oficiales`, `ranking`.
* **Configuración por entorno**: `DEADLINE` (ISO-UTC), `SHEETS_SPREADSHEET_ID`, `ALLOWED_ORIGINS`, credenciales del Service Account.
* **Validaciones**:

  * Deadline en el endpoint de escritura de pronósticos.
  * Chequeo contra listas de **fuerzas** y **provincias** cargadas desde archivos estáticos.
  * Unicidad por **email** y edición permitida hasta el cierre.
* **Scoring**: motor interno que calcula puntaje principal (error absoluto ponderado, orden Top-3, participación y margen) y puntaje bonus (reglas fijas).
* **Observabilidad**: logging de sincronización con Sheets y de reprocesos; métricas básicas en `/api/admin/overview`. Válidación visual de problemas simples.
* **CORS**: habilitado únicamente para el dominio del frontend; soporte a credenciales para la sesión admin.
* **Despliegue**: contenedorizable; variables inyectadas por entorno; migraciones gestionadas por Django.

### Frontend (Vue.js 3)

* **Framework**: **Vue 3** (Composition API) con **TypeScript**.
* **Bundler**: **Vite**.
* **Estado global**: **Pinia** (stores para jugador, prode, resultados y administración).
* **Router**: **Vue Router** (rutas: Inicio, Prode con subtabs, Resultados, Ranking, Administración).
* **UI**: **Vuetify** como framework de componentes (inputs, tablas, modales, alerts, layouts responsivos).
* **HTTP**: **Axios** con manejo de estados (cargando, éxito, pendiente de sync) y tratamiento de 403 post-deadline.
* **Config por entorno**: `VITE_DEADLINE` (ISO-UTC), `VITE_API_BASE`.
* **UX**: validaciones suaves (rangos 0–100, suma ≈ 100 %), **cuenta regresiva**, bloqueo visual post-deadline, precarga por email, buscador en ranking, exportación a CSV (vía API admin).
* **Acceso admin**: login de sesión (form simple), vistas de carga de resultados, reintento de sincronización y métricas.
