# ADR-002 — Fuentes de datos y fallbacks

## Estado

Aceptado.

## Contexto

PractiCV necesita ofertas de prácticas, pero no puede depender de una sola fuente:

- practicas.pe puede cambiar, bloquear o limitar el acceso.
- El MCP `practicas-pe` es local y opcional.
- Los estudiantes encuentran ofertas en muchos portales.
- Practilizate es un observatorio de datos agregados, no una API de ofertas individuales.

Una dependencia dura de Practilizate o del MCP haría que PractiCV no arranque si esas piezas fallan.

## Decisión

Aplicar el principio **“trae tu propia oferta” (BYOO)** y una arquitectura de adaptadores con fallback:

1. **MCP `practicas-pe`**: fuente opcional para buscar ofertas de practicas.pe.
2. **Texto pegado**: fuente principal y más confiable.
3. **CSV/Excel**: carga masiva.
4. **URL + JSON-LD**: captura individual best effort.
5. **Bookmarklet y correos**: v0.2.
6. **Practilizate**: adaptador opcional de benchmarks o CSV local, nunca dependencia.

Reglas:

- Si el MCP falla, la UI ofrece pegar texto o importar CSV.
- Si la URL no se puede leer, se pide pegar el texto.
- Si Practilizate no está, la app funciona igual.
- No se guarda HTML crudo.
- No se hace scraping masivo.
- Cada oferta conserva `source_type`, `source_url` y `captured_at`.
- La ingesta es idempotente por URL canónica o `dedupe_hash`.

## Consecuencias

### Positivas

- La app funciona desde el día 1 con datos del usuario.
- No se rompe si cambia un portal.
- Es legalmente más segura.
- Permite ofertas que no están en ningún portal.
- El MCP y Practilizate quedan como fuentes opcionales.

### Negativas

- La captura manual requiere más trabajo del usuario.
- La calidad de los datos depende de lo que el usuario pegue o importe.
- Hay que mantener varios adaptadores.

## Reglas de testing

- Los adaptadores se prueban con fixtures, nunca contra el sitio real en CI.
- El E2E debe cubrir el fallback del MCP.
- No se modifica un fixture para que pase un test.
