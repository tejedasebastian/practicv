# SQL y performance — Fase 1

> Motor: PostgreSQL 17 (Docker local).
> Dataset de demo: 1,005 ofertas, 505 matches, 3 postulaciones, 2 recordatorios.
> Fecha: 17 de noviembre de 2026.

---

## 1. Modelo

La Fase 1 crea un modelo relacional normalizado:

- `profiles`
- `cv_documents`
- `skills`
- `profile_skills` (PK compuesta)
- `offers`
- `offer_skills` (PK compuesta)
- `offer_links`
- `matches`
- `applications`
- `application_events`
- `reminders`
- `source_configs`

Decisiones relevantes:

- `offers.dedupe_hash` UNIQUE para ingesta idempotente.
- `applications(profile_id, offer_id)` UNIQUE para no duplicar postulaciones.
- `JSONB` para `target_roles`, `parsed_json`, `gaps_json`, `explanation_json` y `aliases`.
- Fechas con timezone.
- Checks para niveles (0–3), scores (0–100) y salario no negativo.

---

## 2. Vista con CTE + window function

`v_offer_ranking` rankea las ofertas de cada perfil por score y fecha límite.

```sql
CREATE OR REPLACE VIEW v_offer_ranking AS
WITH scored AS (
    SELECT
        o.id AS offer_id,
        o.title,
        o.company,
        o.deadline_at,
        m.profile_id,
        m.overall_score,
        m.must_have_score,
        ROW_NUMBER() OVER (
            PARTITION BY m.profile_id
            ORDER BY m.overall_score DESC, o.deadline_at ASC NULLS LAST
        ) AS rank
    FROM offers o
    JOIN matches m ON m.offer_id = o.id
)
SELECT offer_id, title, company, deadline_at, profile_id,
       overall_score, must_have_score, rank
FROM scored;
```

Consulta:

```sql
SELECT rank, title, company, overall_score, must_have_score
FROM v_offer_ranking
WHERE profile_id = (SELECT id FROM profiles WHERE email = 'demo@practicv.local')
ORDER BY rank
LIMIT 5;
```

Resultado observado:

```text
 rank |              title              |        company        | overall_score | must_have_score
------+---------------------------------+-----------------------+---------------+-----------------
    1 | Oferta demo 0249                | Empresa Demo 49       |          99.0 |            64.0
    2 | Oferta demo 0399                | Empresa Demo 49       |          99.0 |            94.0
    3 | Oferta demo 0099                | Empresa Demo 49       |          99.0 |            74.0
    4 | Oferta demo 0349                | Empresa Demo 49       |          99.0 |            84.0
    5 | Oferta demo 0499                | Empresa Demo 49       |          99.0 |            74.0
```

---

## 3. Función PL/pgSQL

`fn_top_offers_for_profile(uuid)` devuelve las ofertas rankeadas de un perfil.

```sql
CREATE OR REPLACE FUNCTION fn_top_offers_for_profile(p_profile_id uuid)
RETURNS TABLE (
    offer_id uuid,
    title text,
    company text,
    overall_score double precision,
    must_have_score double precision,
    decision text
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.title::text,
        o.company::text,
        m.overall_score,
        m.must_have_score,
        m.decision::text
    FROM offers o
    JOIN matches m ON m.offer_id = o.id
    WHERE m.profile_id = p_profile_id
    ORDER BY m.overall_score DESC, o.deadline_at ASC NULLS LAST;
END;
$$;
```

Uso:

```sql
SELECT offer_id, title, overall_score, decision
FROM fn_top_offers_for_profile(
    (SELECT id FROM profiles WHERE email = 'demo@practicv.local')
)
LIMIT 5;
```

Resultado observado:

```text
              offer_id              |           title           | overall_score |     decision
------------------------------------+---------------------------+---------------+------------------
 df52c39e-675b-4073-b2be-494b662249d9 | Oferta demo 0249        |          99.0 | apply_with_gaps
 9625a615-7266-4f2f-9153-f1ced5ce608a | Oferta demo 0399        |          99.0 | apply_with_gaps
 894a1c8f-2cec-424d-a24d-92cfa232c64a | Oferta demo 0099        |          99.0 | apply_with_gaps
 fe2d9e07-f339-4bc4-b6c4-c2b10208b7b4 | Oferta demo 0349        |          99.0 | apply_with_gaps
 05eecad1-eedd-4ae6-bd58-8595c89d0e2c | Oferta demo 0499        |          99.0 | apply_with_gaps
```

---

## 4. Índices

La migración `3ba0135828de` agrega:

```sql
CREATE INDEX IF NOT EXISTS ix_matches_profile_score_covering
ON matches (profile_id, overall_score DESC)
INCLUDE (must_have_score, offer_id);

CREATE INDEX IF NOT EXISTS ix_offers_open_deadline
ON offers (deadline_at)
WHERE deadline_at IS NOT NULL;
```

El índice covering permite resolver el ranking sin ir al heap de `matches` para `must_have_score` y `offer_id`.

---

## 5. EXPLAIN ANALYZE

Consulta:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM v_offer_ranking
WHERE profile_id = (SELECT id FROM profiles WHERE email = 'demo@practicv.local')
  AND rank <= 5
ORDER BY rank;
```

Plan observado:

```text
Sort  (cost=16.69..16.69 rows=2 width=96) (actual time=0.365..0.366 rows=5 loops=1)
  Sort Key: (row_number() OVER (?))
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=166
  ->  WindowAgg  (cost=16.64..16.68 rows=2 width=96) (actual time=0.336..0.339 rows=5 loops=1)
        Run Condition: (row_number() OVER (?) <= 5)
        Buffers: shared hit=166
        ->  Incremental Sort  (cost=16.60..16.64 rows=2 width=88) (actual time=0.273..0.274 rows=6 loops=1)
              Sort Key: m.overall_score DESC, o.deadline_at
              Presorted Key: m.overall_score
              ->  Nested Loop  (cost=0.55..16.59 rows=1 width=88) (actual time=0.070..0.231 rows=41 loops=1)
                    ->  Index Only Scan using ix_matches_profile_score_covering on matches m
                          (cost=0.27..8.29 rows=1 width=48) (actual time=0.039..0.070 rows=41 loops=1)
                          Index Cond: (profile_id = '4cdcabf2-5ba6-4e53-8867-3bcc58881f0c'::uuid)
                          Heap Fetches: 41
                          Buffers: shared hit=43
                    ->  Index Scan using offers_pkey on offers o
                          (cost=0.28..8.29 rows=1 width=56) (actual time=0.003..0.003 rows=1 loops=41)
                          Index Cond: (id = m.offer_id)
                          Buffers: shared hit=123
Planning:
  Buffers: shared hit=4
Planning Time: 0.702 ms
Execution Time: 0.517 ms
```

Lectura:

- `WindowAgg` ejecuta `ROW_NUMBER()`.
- `Index Only Scan` usa `ix_matches_profile_score_covering`; no necesita el heap para los campos incluidos.
- `Incremental Sort` aprovecha el orden del índice por `overall_score`.
- `Execution Time`: **0.517 ms** con 505 matches.

---

## 6. Reproducir

```powershell
cd backend
$env:PRACTICV_DATABASE_URL="postgresql+psycopg://practicv:practicv@localhost:5434/practicv"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m practicv seed --demo --volume 1000
docker exec practicv-db-1 psql -U practicv -d practicv
```

Dentro de `psql`:

```sql
SELECT count(*) FROM offers;
SELECT rank, title, overall_score FROM v_offer_ranking
WHERE profile_id = (SELECT id FROM profiles WHERE email = 'demo@practicv.local')
ORDER BY rank LIMIT 5;
SELECT * FROM fn_top_offers_for_profile(
  (SELECT id FROM profiles WHERE email = 'demo@practicv.local')
) LIMIT 5;
```
