# Bookmarklet — captura desde el navegador

Estado: **implementado en v0.2**. No hay extensión ni scraping masivo.

## 1. Flujo

1. El usuario arrastra el botón de `/bookmarklet` a su barra de marcadores.
2. En una oferta, pulsa el marcador.
3. El bookmarklet lee `location.href`, `document.title`, los bloques
   `application/ld+json` y el texto visible (máximo 20,000 caracteres).
4. Abre `http://<tu-app>/captura#<payload-base64url>` en una pestaña nueva.
5. La app llama a `POST /api/v1/offers/bookmarklet/preview` y muestra los
   campos editables.
6. El usuario confirma con `POST /api/v1/offers/bookmarklet`.

El JSON-LD y el texto viajan en el **hash** de la URL: no se envían a un
servidor externo ni se guarda HTML crudo. La app local es la única que recibe
los datos, y solo después de la confirmación.

## 2. Por qué no hace POST directo desde la página

Un POST desde `https://portal.example` a `http://localhost:3000` requiere CORS
permisivo o `no-cors` (sin leer la respuesta). El hash + página local evita CORS,
mantiene la confirmación explícita y no expone un endpoint de escritura a
cualquier sitio abierto en el navegador.

## 3. Extracción

- `JobPosting` en JSON-LD, incluyendo `@graph`.
- `title` y `hiringOrganization.name`.
- `jobLocation.address` y `baseSalary`.
- `datePosted` y `validThrough`.
- Si no hay JSON-LD: usa el título de la pestaña, el `og:site_name` y el texto
  visible; marca advertencias para que el usuario complete empresa o título.

El texto visible se recorta a 20,000 caracteres. La descripción se guarda como
texto plano, sin etiquetas HTML.

## 4. API

| Método | Ruta | Uso |
|---|---|---|
| `POST` | `/api/v1/offers/bookmarklet/preview` | Extrae campos; no persiste |
| `POST` | `/api/v1/offers/bookmarklet` | Crea la oferta con `source_type=bookmarklet` |

`preview` recibe `url`, `title`, `jsonld[]`, `text` y devuelve los campos +
`confidence` + `warnings`. `create` recibe los campos editados y usa el mismo
`normalize_offer`/`save_offer` del resto de fuentes, con deduplicación.

## 5. Evidencia

- Backend: `backend/tests/e2e/test_bookmarklet.py` — 3 tests con JSON-LD, `@graph`,
  fallback sin JSON-LD y duplicado.
- Playwright: `tests/e2e/phase6-bookmarklet.spec.ts` — abre una página
  `https://jobs.example.com/offer`, ejecuta el bookmarklet, captura el popup,
  confirma y verifica el POST.
- Resultado: **9/9 Playwright**, **25/25 backend**.

## 6. Límites

- Requiere la app local abierta en el origen desde el que se instaló el botón.
- El texto visible puede incluir ruido de la página; el usuario revisa.
- No captura páginas con login si el texto/JSON-LD no está en el DOM.
- No hay auto-postulación ni envío de datos a terceros.
- El fallback para páginas sin datos mínimos es pegar el texto en `/ofertas`.
