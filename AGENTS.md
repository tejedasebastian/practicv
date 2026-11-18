# AGENTS.md — PractiCV

## 1. Lee esto antes de tocar código

Lee, en este orden:

1. `SPECS.md`
2. `ROADMAP.md`
3. `CODESTYLE.md`
4. `README.md`
5. `AGENTS.md`

Si hay contradicción:

- `SPECS.md` manda sobre el comportamiento del producto.
- `AGENTS.md` manda sobre el proceso de trabajo.
- `CODESTYLE.md` manda sobre forma, nombres y formato.

---

## 2. Rol y estándar de calidad

Actúa como si **Linus Torvalds** revisara cada cambio. No es un personaje decorativo: es un quality gate.

Principios:

- La corrección y la simplicidad están por encima de la elegancia.
- No agregues abstracciones que no resuelvan un problema real.
- No dejes código muerto, TODOs sin dueño ni comentarios que narran lo obvio.
- Si no sabes qué es lo correcto, **detente y propón 2–3 opciones con tradeoffs**. No adivines.
- Si un requisito es ambiguo, pregunta antes de implementar.
- Si un test falla, no lo maquilles: entiende la causa o documenta la limitación.
- No ocultes fallos en logs, README ni métricas.
- Deja el código mejor de como lo encontraste.

### Principios de *The Clean Coder*

- No commitees código que sabes que está roto.
- Haz commits pequeños y significativos.
- Di “no” a un requisito ambiguo o mal definido.
- Los tests son parte del trabajo profesional, no un extra.
- No trabajes cansado en decisiones irreversibles.
- Asume responsabilidad por lo que entregas.

---

## 3. Reglas de testing — obligatorias

### Texto original (inglés)

- NEVER write unit tests after you write code.
- Highly prefer E2E tests as the sole testing mechanism. Use them to verify complex features work. At the end of E2E tests, produce a verifiable and repeatable artifact.
- If you must test a system in isolation, FIRST write all the ways it could fail, THEN write the code.
- Tautological tests considered harmful.
- Change-detector tests considered harmful.
- Do not create regression tests for bug fixes without a genuine gap in behavior testing.
- Additionally when writing an e2e test don't pick the simplest possible scenario to prove it works, pick a medium to hard scenario when verifying the work with e2e test.

### Traducción operativa

- **Nunca** escribas unit tests después de escribir el código.
- Prefiere **E2E** como mecanismo principal de prueba. Al terminar, deja un **artefacto verificable y repetible**.
- Si necesitas probar algo aislado, **primero** enumera todas las formas en que puede fallar; **después** escribe el código.
- Los tests tautológicos están prohibidos.
- Los tests “change-detector” están prohibidos.
- No crees tests de regresión para un bug si no hay una brecha real de comportamiento.
- El E2E no debe usar el escenario más simple: usa un escenario **medio-difícil**.
- No modifiques fixtures para hacer pasar un test. Arregla el código o documenta la limitación real.
- Si un test falla, no lo borres ni lo skipees sin justificarlo por escrito.

### E2E-first en PractiCV

Cada checkpoint del `ROADMAP.md` sigue este orden:

1. Escribe el escenario E2E que describe el comportamiento esperado.
2. Ejecútalo y confirma que falla por la razón correcta.
3. Implementa lo mínimo para que pase.
4. Ejecuta el E2E completo.
5. Genera artefactos en `artifacts/e2e/`.
6. Actualiza `ROADMAP.md` y `README.md` si cambian métricas o capturas.
7. Formatea y lint.
8. Commit convencional.

**No avances al siguiente checkpoint si el E2E no pasa.**

### Artefactos E2E esperados

```text
artifacts/e2e/
├─ run_manifest.json
├─ matches.json
├─ applications.xlsx
├─ applications.csv
├─ calendar.ics
├─ quality_report.json
└─ checksums.sha256
```

---

## 4. Arquitectura — reglas de boundaries

PractiCV es un **monolito modular** con principios de microservicios, no un conjunto de microservicios reales.

### Contextos

- `profile`: perfil, CV, habilidades.
- `offers`: captura, normalización, taxonomía, procedencia.
- `matching`: requisitos, score y explicación.
- `applications`: Kanban, eventos y recordatorios.
- `exports`: Excel, CSV, ICS.
- `shared`: contratos, configuración, logging, errores.

### Reglas

- Cada contexto tiene `domain`, `application` y `adapters`.
- Cada contexto expone una **interfaz pública**; los demás no tocan sus tablas ni sus modelos ORM.
- El dominio no importa FastAPI, SQLAlchemy ni nada de infraestructura.
- Los adaptadores externos (MCP, CSV, URL, Practilizate) viven en `adapters/sources/`.
- Los contratos entre contextos son Pydantic o tipos TypeScript; no diccionarios sueltos.
- La ingesta debe ser **idempotente**: deduplicar por URL o `dedupe_hash`.
- Los errores deben ser explícitos y mapeados a HTTP; no silenciar excepciones.
- Los logs deben ser estructurados, con `request_id` y sin PII.
- No agregues colas, brokers ni servicios distribuidos para el MVP. Sería complejidad sin valor.

### Prohibido

- Importar modelos ORM de un contexto en otro.
- Hacer SQL directo desde la UI o desde el dominio.
- Compartir una tabla como “contrato” entre módulos.
- Acoplar PractiCV a Practilizate.
- Hacer que el núcleo dependa del MCP `practicas-pe`.

---

## 5. Idioma y documentación

- **Documentación** (`SPECS.md`, `ROADMAP.md`, `CODESTYLE.md`, `AGENTS.md`, `README.md`): español.
- **README.en.md**: traducción al inglés para reclutadores.
- **UI**: español e inglés, con i18n; sin strings hardcodeados.
- **Código, nombres de variables, tablas, columnas, logs y commits**: inglés.
- **Comentarios**: solo decisiones técnicas no obvias; en inglés.
- **Mensajes de error visibles al usuario**: español e inglés.

---

## 6. Datos, privacidad y legal

- **Local-first:** el CV y las postulaciones viven en la máquina del usuario.
- **Sin telemetría** por defecto.
- **Sin PII en el repositorio**: ni CVs reales, ni correos, ni teléfonos.
- **Sin secretos**: `.env` fuera de Git; usar `.env.example`.
- **Sin scraping masivo**: solo una página por acción del usuario.
- **Sin LinkedIn scraping**: no autenticarse ni crawlear LinkedIn.
- **Sin auto-postulación**: el usuario decide y envía.
- **MCP `practicas-pe`:** fuente opcional. Si falla, fallback a texto/CSV/URL.
- **Practilizate:** adaptador opcional. No es dependencia; no imports de su código.
- **Datos de demo:** sintéticos y reproducibles.
- **Atribución:** si se usa el MCP o Practilizate, acreditar la fuente.
- **Legal:** revisar `robots.txt` y términos de practicas.pe antes de distribuir.
- **Disclaimer:** el match es una estimación, no una promesa de empleo.

---

## 7. Flujo de trabajo

1. Abre el checkpoint actual en `ROADMAP.md`.
2. Escribe el E2E del comportamiento.
3. Implementa.
4. Ejecuta el E2E y genera artefactos.
5. Actualiza el checkbox de `ROADMAP.md`.
6. Actualiza `README.md` si cambian métricas, capturas o uso.
7. Ejecuta `ruff format`, `ruff check`, `pnpm lint` y `pnpm format`.
8. Haz commit con conventional commits.
9. Pasa al siguiente checkpoint.

**No saltes checkpoints. No commitees con tests rojos. No dejes artefactos sin checksums.**

---

## 8. Convención de commits

```text
feat: add multi-source offer ingestion
fix: handle missing salary values
docs: add matching explanation
test: add medium-hard e2e scenario
refactor: isolate offer source adapters
chore: configure ruff and eslint
```

Reglas:

- Un commit por checkpoint significativo.
- Mensaje en inglés, imperativo, corto.
- No mezclar refactor grande con feature.
- Formatear antes de commitear.

---

## 9. Definición de terminado

Un checkpoint está terminado cuando:

- El E2E del checkpoint pasa.
- El artefacto correspondiente existe y es reproducible.
- `ROADMAP.md` tiene el checkbox marcado.
- `README.md` está actualizado si cambió algo visible.
- `ruff format` y `ruff check` pasan.
- `pnpm lint` y `pnpm format` pasan.
- No hay PII, secretos ni datos crudos en el repo.
- El commit está hecho.

El proyecto está terminado cuando:

- Todos los checkpoints del `ROADMAP.md` están marcados.
- El E2E medio-difícil pasa desde cero.
- La demo funciona con datos sintéticos.
- README y README.en.md están completos.
- La UI funciona en español e inglés.
- No hay dependencia de Practilizate ni del MCP para arrancar.
- La licencia y los créditos están claros.

---

## 10. Cuándo detenerte y preguntar

Detente y propón opciones si:

- Un requisito es ambiguo.
- Un test falla y no entiendes por qué.
- Una fuente de datos bloquea o cambia.
- Hay riesgo de PII, legal o de seguridad.
- Necesitas romper un boundary de arquitectura.
- Una decisión afecta el alcance del MVP.

No sigas “a ciegas” para parecer productivo. Es mejor una pausa corta que un commit malo.
