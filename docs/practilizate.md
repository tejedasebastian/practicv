# Adaptador Practilizate — CSV opcional

Estado: **implementado en v0.2**. Desactivado por defecto; no es una dependencia
del producto.

## 1. Qué hace

- Lee un CSV exportado por Practilizate (`dashboard_dataset.csv`) con ofertas
  de prácticas.
- Mapea columnas: `title`, `company`, `url`, `offer_id`, `location`,
  `modality`, `salary_amount`, `salary_currency`, `published_at`,
  `deadline_at`, `requirements_text`.
- Importa las ofertas con `source_type=practilizate`, aplicando la misma
  normalización y deduplicación que el resto de fuentes.
- No importa código, no se conecta a su base y no se ejecuta si el adaptador
  está desactivado.

## 2. Activación

Por defecto:

```env
PRACTICV_PRACTILIZATE_ENABLED=false
```

Para usarlo en local:

```env
PRACTICV_PRACTILIZATE_ENABLED=true
```

Reinicia la API. En la UI, **Ofertas → Practilizate** muestra el estado y
habilita el selector de CSV. El flag vive en `.env`/entorno, no en Git.

## 3. API

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/api/v1/offers/sources/practilizate/status` | `enabled` + detalle |
| `POST` | `/api/v1/offers/import/practilizate` | Multipart CSV; importa |

Si está desactivado, el POST responde `422` con la instrucción de activación.
El CSV debe ser UTF-8 y tener `title`, `company` y `url`; se rechazan columnas
faltantes, archivos vacíos y más de 500 filas.

## 4. Datos

- El CSV real de Practilizate **no se commitea**; el adaptador recibe el archivo
  por upload.
- El dashboard usa un CSV sintético distinto (`dashboard/data/applications.csv`).
- El test usa un CSV sintético con una fila válida, una duplicada, una sin
  empresa y una sin URL.

## 5. Evidencia

- Backend: `backend/tests/e2e/test_practilizate.py` — estado habilitado,
  importación con conteos exactos, consulta por `source_type` y CSV inválido.
- Resultado: **25/25 backend**.

## 6. Límites

- No hay sincronización automática ni lector de PostgreSQL; se importa el CSV
  que exporta Practilizate.
- No filtra ofertas vencidas: el usuario decide qué importar.
- El adaptador es opcional; si no está activo, el resto de PractiCV funciona
  igual.
- No se importa código ni se comparte base de datos entre ambos proyectos.
