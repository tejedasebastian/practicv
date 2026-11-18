# ADR-001 — Monolito modular

## Estado

Aceptado.

## Contexto

PractiCV es una aplicación local-first de un solo usuario. El producto tiene contextos bien diferenciados (perfil, ofertas, matching, postulaciones, exportaciones), pero no necesita infraestructura distribuida.

La tentación de usar microservicios reales agrega complejidad operativa sin valor para el MVP: múltiples deployables, red, descubrimiento, colas, observabilidad distribuida y consistencia eventual.

## Decisión

Construir un **monolito modular** con principios de microservicios:

- Un solo deployable local.
- Contextos separados por boundaries.
- Contratos explícitos entre contextos.
- Adaptadores aislados para fuentes externas.
- Idempotencia en la ingesta.
- Observabilidad con logs estructurados y `run_manifest`.
- Sin colas, brokers ni servicios distribuidos.

## Consecuencias

### Positivas

- Menor complejidad operativa.
- Desarrollo más rápido.
- Fácil de ejecutar en la máquina del usuario.
- Los boundaries siguen siendo claros y testeables.
- Se puede extraer un contexto a servicio si el producto crece.

### Negativas

- Un solo proceso puede convertirse en un cuello de botella.
- Los límites deben cuidarse manualmente; no hay barreras de red.
- El despliegue escala como una unidad.

## Reglas

- El dominio no importa FastAPI, SQLAlchemy ni clientes HTTP.
- Los contextos no comparten modelos ORM.
- Las comunicaciones internas usan interfaces y contratos.
- Si un contexto necesita datos de otro, usa su interfaz pública, no su tabla.
