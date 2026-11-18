---
description: Ejecuta el roadmap de PractiCV con E2E-first y commits por checkpoint
---

Completa el proyecto PractiCV.

Lee, en este orden:

- `SPECS.md`
- `ROADMAP.md`
- `README.md`
- `CODESTYLE.md`
- `AGENTS.md`

Trabaja los checkpoints de `ROADMAP.md` en orden. No saltes ninguno.

## Reglas obligatorias

- E2E-first: antes de implementar un checkpoint, escribe el escenario E2E que describe el comportamiento esperado.
- Ejecuta el E2E y confirma que falla por la razón correcta.
- Implementa lo mínimo para que pase.
- No escribas unit tests después del código.
- No modifiques fixtures para hacer pasar tests.
- No uses tests tautológicos ni change-detector.
- No avances si el E2E no pasa.
- Si necesitas aislar un sistema, primero enumera todas las formas en que puede fallar y luego implementa.
- Usa un escenario E2E medio-difícil, no el más simple.
- Genera artefactos repetibles en `artifacts/e2e/` con checksums y `run_manifest.json`.
- No llames al sitio real de practicas.pe en tests; usa fixtures.
- Si el MCP o Practilizate no están disponibles, usa el fallback definido en `SPECS.md`.

## Después de cada checkpoint

1. Ejecuta el E2E completo.
2. Genera o actualiza los artefactos.
3. Marca el checkbox en `ROADMAP.md`.
4. Actualiza `README.md` y `README.en.md` si cambian métricas, capturas o uso.
5. Ejecuta `ruff format`, `ruff check`, `pnpm lint` y `pnpm typecheck`.
6. Haz commit con conventional commits:
   - `feat: ...`
   - `fix: ...`
   - `docs: ...`
   - `test: ...`
   - `refactor: ...`
   - `chore: ...`
7. Pasa al siguiente checkpoint.

## Arquitectura

- Monolito modular con boundaries de microservicios.
- Contextos: `profile`, `offers`, `matching`, `applications`, `exports`, `shared`.
- El dominio no importa FastAPI, SQLAlchemy ni clientes HTTP.
- Los contextos se comunican por contratos, no por tablas.
- La ingesta es idempotente.
- No agregues colas, brokers ni microservicios reales.
- No acoples el núcleo a Practilizate ni al MCP.

## Idioma

- Documentación en español.
- UI en español e inglés.
- Código, nombres técnicos, logs y commits en inglés.
- No hardcodees strings de UI; usa i18n.

## Calidad

Actúa como si Linus Torvalds revisara cada cambio.

- Prioriza corrección y simplicidad.
- No agregues abstracciones innecesarias.
- No dejes código muerto.
- No comentes lo obvio.
- No ocultes fallos.
- Si un requisito es ambiguo, detente y propón 2–3 opciones con tradeoffs.
- Si rompes un boundary, justifícalo en un ADR.

## Criterio de parada

Detente y pide revisión si:

- El E2E falla y no entiendes por qué.
- Una fuente de datos bloquea o cambia.
- Hay riesgo de PII, legal o de seguridad.
- Necesitas romper un boundary.
- Una decisión cambia el alcance del MVP.

No sigas a ciegas. Es mejor una pausa corta que un commit malo.

## Definición de terminado

El proyecto está terminado cuando:

- Todos los checkpoints de `ROADMAP.md` están marcados.
- El E2E medio-difícil pasa desde cero.
- Los artefactos existen y son reproducibles.
- La demo funciona con datos sintéticos.
- README y README.en.md están completos.
- La UI funciona en español e inglés.
- No hay dependencia de Practilizate ni del MCP para arrancar.
- No hay PII ni secretos en el repositorio.
- `ruff` y `pnpm lint` pasan.
- El tag `v0.1.0` y el release están creados.
