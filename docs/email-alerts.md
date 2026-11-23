# Alertas de correo — Gmail OAuth y `.eml`

Estado: **implementado en v0.2.1**. Incluye Gmail OAuth en vivo con Google
Personal mode y el fallback de importación local `.eml`.

## 1. Dos caminos

| Camino | Estado | Uso |
|---|---|---|
| **Gmail OAuth** | En vivo, probado | Conecta la cuenta, busca alertas y previsualiza enlaces |
| **`.eml` local** | En vivo, probado | Sube un correo exportado de Gmail/Outlook |

En ambos casos el usuario elige qué enlaces importar. El correo original no se
guarda y el HTML no se persiste.

## 2. Gmail OAuth

### Google Cloud

La app usa un proyecto **Personal mode** de Google Cloud:

- Solo funciona con la cuenta Google que creó la app.
- No requiere verificación ni la pantalla de app no verificada.
- No tiene el límite de 100 usuarios.
- No sufre la expiración de refresh token a los 7 días del modo Testing.
- No requiere cuenta de facturación para Gmail API.

El proyecto local es `personal-mode-app` (ID `tough-cipher-515619-g0`) y el
cliente OAuth se llama `PractiCV Local`. La Gmail API está habilitada.

Redirect URI local usado en la prueba:

```text
http://localhost:8010/api/v1/email/google/callback
```

La UI usa `http://localhost:3001` como frontend y `http://127.0.0.1:8010` como
API porque `localhost:8000/3000` estaban ocupados por ContrataMYPE. Si usas
otros puertos, actualiza el redirect URI en Google Cloud, `backend/.env` y
`frontend/.env.local`.

### Variables

```env
PRACTICV_GOOGLE_CLIENT_ID=...
PRACTICV_GOOGLE_CLIENT_SECRET=...
PRACTICV_GOOGLE_REDIRECT_URI=http://localhost:8010/api/v1/email/google/callback
```

`backend/.env` está en `.gitignore`. No se commitean credenciales.

### Token

- El refresh token se guarda en el **llavero del sistema** vía `keyring`
  (Windows Credential Manager en esta máquina).
- Servicio: `practicv-google-oauth`.
- No hay tokens en PostgreSQL, `.env` del repo ni Git.
- Para desconectar, borra la entrada del llavero o usa `/email/google/status`
  para verificar el estado.

### Flujo

1. `GET /api/v1/email/google/authorize` devuelve la URL de Google con
   `gmail.readonly`, `access_type=offline`, `prompt=consent` y un `state`
   efímero.
2. El usuario elige su cuenta y acepta el scope de solo lectura.
3. Google redirige a `/api/v1/email/google/callback`; el backend intercambia
   el código y guarda el token.
4. La UI lista correos con `GET /api/v1/email/google/messages?q=...`.
5. Al abrir un correo, `POST /api/v1/email/google/preview` extrae los enlaces.
6. `POST /api/v1/email/google/import` captura los enlaces seleccionados con
   `capture_url` y deduplica.

### Filtro de enlaces

El parser descarta ruido típico de los digest de LinkedIn:

- feed, mensajes, notificaciones, premium, help, apps de iOS/Android;
- conserva solo `linkedin.com/jobs/view/<id>` y normaliza la URL canónica;
- deduplica las variantes de tracking del mismo empleo;
- prefiere el título descriptivo sobre “Oferta en linkedin.com”.

En la prueba real, un digest de LinkedIn produjo **6 ofertas limpias** desde
30 enlaces crudos.

## 3. Evidencia en vivo

- Proyecto Personal mode creado; Gmail API habilitada.
- OAuth completado con la cuenta personal del creador (Personal mode).
- `GET /api/v1/email/google/status` → `connected: true`.
- `GET /api/v1/email/google/messages?q=practicas` → 3 correos.
- `POST /api/v1/email/google/preview` → 6 candidatos canónicos de LinkedIn.
- Backend: **29/29 tests**.
- Playwright: **10/10 tests**.

## 4. `.eml` local

Sigue disponible para Outlook o cuando no quieras conectar OAuth:

1. Gmail: **Mostrar original → Descargar original**.
2. Outlook: **Guardar como** `.eml`.
3. Ofertas → Correo → `o importa un .eml`.

El parser es el mismo (`email_alerts.py`), así que el filtro de enlaces y la
deduplicación aplican igual.

## 5. Límites

- Solo Gmail; Outlook/Microsoft Graph no está implementado.
- Solo lectura (`gmail.readonly`): no se envían correos.
- Personal mode es intransferible; para varios usuarios habría que crear un
  proyecto External y pasar verificación/CASA.
- La búsqueda lista hasta 10 correos y consulta metadatos secuencialmente
  (~10-12 s en una cuenta grande).
- No se autentica en LinkedIn ni se hace scraping; solo se leen alertas que el
  usuario ya recibe.
- No se guardan correos, HTML crudo ni tokens en el repositorio.
