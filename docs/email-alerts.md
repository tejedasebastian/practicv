# Alertas de correo — importación local de `.eml`

Estado: **implementado en v0.2 como importación local**. La sincronización
OAuth en vivo queda pendiente de credenciales de una app registrada.

## 1. Qué hace

- Sube un archivo `.eml` exportado desde Gmail u Outlook.
- Extrae el asunto y los enlaces del cuerpo HTML y del texto plano.
- Muestra los enlaces con su título para que el usuario seleccione.
- Importa solo los seleccionados usando `capture_url` (JSON-LD/OpenGraph),
  con deduplicación por URL/`dedupe_hash`.

No se guarda el correo original, ni el HTML, ni tokens. El archivo se procesa en
memoria y se descarta.

## 2. Por qué `.eml` y no OAuth

La app es local-first y no tiene una app OAuth registrada en Google/Microsoft.
Implementar el baile OAuth sin credenciales de cliente no se puede probar de
punta a punta y obligaría a guardar secretos. En v0.2 se entrega el camino que
funciona hoy:

1. En Gmail: **Mostrar original → Descargar original**.
2. En Outlook: **Guardar como** un `.eml`.
3. Subir el archivo en **Ofertas → Correo (.eml)**.

La interfaz está separada del parser, así que un proveedor OAuth puede añadirse
después sin tocar el importador.

## 3. API

| Método | Ruta | Uso |
|---|---|---|
| `POST` | `/api/v1/offers/import/email/preview` | Multipart `.eml`; devuelve asunto, enlaces y avisos |
| `POST` | `/api/v1/offers/import/email` | JSON `{ "urls": [...] }`; captura y guarda |

Límites: 2 MB por `.eml`, 30 enlaces por correo, 30 URLs por importación.

## 4. Parser

`backend/practicv/adapters/sources/email_alerts.py`:

- `email.policy.default` + `BytesParser`.
- Recorre partes `text/html` y `text/plain`.
- HTML: `BeautifulSoup`, anclas `href` con texto.
- Texto: regex de URLs y la línea anterior como título aproximado.
- Normaliza URLs y elimina duplicados; conserva el primer título.
- Devuelve avisos si no hay cuerpo o no hay enlaces.

## 5. Evidencia

- Backend: `backend/tests/e2e/test_email_alerts.py` — correo HTML con dos
  enlaces (uno duplicado), un enlace roto, preview, importación y segunda
  importación deduplicada.
- Playwright: `tests/e2e/phase7-email.spec.ts` — sube un `.eml`, previsualiza,
  selecciona e importa.
- Resultado: **25/25 backend**, **9/9 Playwright**.

## 6. Límites y siguiente paso

- No hay bandeja conectada ni búsqueda automática; el usuario exporta el `.eml`.
- Los enlaces deben ser accesibles y permitir `robots.txt`; si fallan, se
  reportan por fila y se puede pegar el texto manualmente.
- OAuth Gmail/Outlook requiere registrar una app, definir `client_id`/`secret`
  y guardar tokens en el llavero del sistema. No se incluye en v0.2 para no
  commitear secretos ni simular una integración no verificada.
- No se autentica en LinkedIn ni en portales de empleo.
