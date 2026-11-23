# PractiCV v0.2.1

**Gmail OAuth en vivo, además de bookmarklet, Practilizate y Power BI.**

v0.2.1 cierra la fase de alertas de correo con una conexión real a Gmail usando
Google **Personal mode**. Sigue siendo una app local-first, de un solo usuario,
sin auto-postulación y sin promesas de empleo.

---

## Qué incluye

### Gmail OAuth (nuevo en v0.2.1)

- Conexión con `gmail.readonly` y `access_type=offline`.
- Token guardado en el **llavero del sistema** (`keyring`); no en PostgreSQL ni
  en Git.
- Búsqueda de alertas desde la UI y preview de enlaces.
- Filtro de ruido de LinkedIn: solo `jobs/view/<id>`, URLs canónicas y títulos
  descriptivos.
- Probado en vivo: cuenta conectada, 3 correos listados y **6 ofertas limpias**
  extraídas de un digest real.
- Google Personal mode: sin verificación, sin límite de 100 usuarios y sin
  expiración de refresh token a los 7 días.
- Outlook/Microsoft Graph queda como extensión futura.

### Bookmarklet

- Botón instalable desde `/bookmarklet`.
- Lee JSON-LD, título y texto visible; abre `/captura` con los datos en el hash.
- Preview editable y confirmación antes de guardar.
- No guarda HTML crudo ni hace POST cross-origin.

### Alertas `.eml`

- Importa un `.eml` exportado de Gmail/Outlook.
- Extrae enlaces de HTML y texto, con selección y deduplicación.
- Usa el mismo filtro de ruido que Gmail.

### Practilizate

- Adaptador CSV opcional, desactivado por defecto
  (`PRACTICV_PRACTILIZATE_ENABLED=false`).
- Mapeo explícito de columnas; sin dependencia de código ni base de datos.

### Dashboard Power BI

- `dashboard/PractiCV.pbip` con tabla `Applications`.
- Página `Embudo`: tarjetas, funnel por etapa, slicer de estado y tabla.
- Datos sintéticos de demo, sin PII.
- Validación: **0 errores / 0 warnings**.
- Captura: `docs/assets/practicv-dashboard.png`.

### Recordatorios con Power Automate

- Flujo manual `PractiCV Recordatorios` en UNMSM.
- Archivo de entrada + `Send an email (V2)` con adjunto.
- Ejecución real: 985 ms, `Succeeded`.
- No es programado: Microsoft retiró PA para cuentas personales y OneDrive
  UNMSM está bloqueado por el tenant.

---

## Calidad

- Backend: **29/29 tests E2E**.
- Playwright: **10/10 tests**.
- Power BI: **0 errores / 0 warnings** y captura revisada.
- Sin datos crudos, correos reales, CVs reales ni secretos en el repo.

---

## Cómo probarlo

```powershell
docker compose up -d db

cd backend
.venv\Scripts\Activate.ps1
alembic upgrade head
python -m practicv seed --demo --volume 1000
uvicorn practicv.main:app --host 127.0.0.1 --port 8010
```

En otra terminal:

```powershell
cd frontend
npm install
# .env.local: NEXT_PUBLIC_API_URL=http://127.0.0.1:8010
npm run dev -- --port 3001
```

Abrir `http://localhost:3001`.

- Gmail: Ofertas → Correo → Conectar Gmail.
- Bookmarklet: `/bookmarklet`.
- `.eml`: Ofertas → Correo → o importa un `.eml`.
- Practilizate: activar el flag y subir el CSV.
- Power BI: abrir `dashboard/PractiCV.pbip` con el junction
  `C:\Users\Public\practicv` (ver `docs/powerbi.md`).

El redirect local de Gmail es:

```text
http://localhost:8010/api/v1/email/google/callback
```

Si usas otros puertos, actualiza Google Cloud, `backend/.env` y
`frontend/.env.local`.

---

## Límites conocidos

- Solo Gmail; Outlook/Microsoft Graph no está implementado.
- Personal mode solo funciona con la cuenta Google que creó la app.
- Solo lectura: la app no envía correos.
- El bookmarklet requiere la app local abierta en el mismo origen.
- El dashboard usa datos sintéticos y refresh manual.
- El adaptador Practilizate no sincroniza automáticamente.
- El match es una heurística explicable, no asesoría legal ni garantía de empleo.

## Atribución

Datos de prácticas: practicas.pe / MCP `practicas-pe`, según sus términos.
Practilizate es una fuente opcional y no una dependencia.
