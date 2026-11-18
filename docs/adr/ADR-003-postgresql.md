# ADR-003 — PostgreSQL como motor principal

## Estado

Aceptado.

## Contexto

PractiCV necesita persistencia local, pero también debe demostrar el nivel **SQL Avanzado** declarado en el CV:

- CTEs y window functions.
- Vistas y funciones almacenadas.
- `JSONB` para datos flexibles.
- Índices y optimización con `EXPLAIN ANALYZE`.
- Modelamiento relacional defendible en entrevistas.

SQLite es excelente para prototipos local-first, pero se queda corto para mostrar esos conceptos y no es el motor que más se pide en roles de datos/BI.

## Decisión

Usar **PostgreSQL 17** como motor principal, ejecutado localmente con Docker Compose.

- Driver: `psycopg` 3.
- ORM/toolkit: SQLAlchemy 2.
- Migraciones: Alembic.
- Analítica: SQLAlchemy Core o SQL parametrizado con CTEs/window functions.
- CI: servicio PostgreSQL 17.

SQLite queda descartado como motor principal. No se mantiene una capa de compatibilidad con SQLite porque limitaría el uso de `JSONB`, vistas y PL/pgSQL.

## Consecuencias

### Positivas

- El proyecto demuestra SQL avanzado de verdad.
- PostgreSQL es muy valorado en data/BI y analytics.
- `JSONB`, CTEs, window functions y funciones PL/pgSQL están disponibles.
- El mismo motor corre en local, Docker y CI.
- Se pueden documentar índices y planes de ejecución.

### Negativas

- Requiere Docker para desarrollar.
- El arranque no es tan simple como un archivo SQLite.
- Hay que versionar migraciones y cuidar la compatibilidad.

## Reglas

- No usar `create_all` en producción; solo Alembic.
- No concatenar SQL; usar parámetros.
- Toda vista o función va en una migración.
- Las consultas lentas se documentan con `EXPLAIN ANALYZE`.
- El seed de demo no debe contener PII.
