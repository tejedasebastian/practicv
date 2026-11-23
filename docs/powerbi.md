# Dashboard Power BI — embudo de postulaciones

Estado: **implementado en v0.2**. PBIP validado con
`powerbi-report-author validate` en **0 errores / 0 warnings**.

## 1. Artefacto

```text
dashboard/
├─ PractiCV.pbip
├─ PractiCV.Report/
│  ├─ definition.pbir
│  ├─ definition/report.json
│  ├─ definition/pages/practicv-funnel/page.json
│  ├─ definition/pages/practicv-funnel/visuals/...
│  └─ StaticResources/SharedResources/BaseThemes/
├─ PractiCV.SemanticModel/
│  ├─ definition.pbism
│  ├─ definition/model.tmdl
│  ├─ definition/tables/Applications.tmdl
│  └─ definition/expressions.tmdl
├─ data/applications.csv
└─ build_report.py
```

- Tabla `Applications`: `empresa`, `puesto`, `estado`, `estado_etiqueta`,
  `funnel_etapa`, `orden_embudo`, `match`, `must_have`, `decision`,
  `postulada`, `proxima_accion`, `nota`.
- Medidas: `Total`, `Postuladas`, `Entrevistas`, `Ofertas`, `Match promedio`.
- Página `Embudo`: 5 tarjetas, funnel por etapa, slicer de estado, tabla de
  postulaciones y nota de demo.
- Los datos son **sintéticos** (24 filas): no hay CVs, correos ni postulaciones
  reales.

## 2. Ruta de datos

El modelo usa:

```text
DataFolder = C:\Users\Public\practicv\dashboard\data
```

Crea el junction una vez:

```powershell
New-Item -ItemType Junction `
  -Path "C:\Users\Public\practicv" `
  -Target "C:\Users\sebas\Desktop\practicas\projects\practicv"
```

Si mueves el repo, recrea el junction. El PBIP no contiene rutas con tu usuario.

## 3. Abrir y refrescar

1. Abre `dashboard/PractiCV.pbip` con Power BI Desktop.
2. Si aparece “Actualizar ahora”, actualiza el modelo.
3. Aplica los cambios pendientes de Power Query si Desktop los muestra.
4. La página `Embudo` debe mostrar 24 postulaciones y las 5 tarjetas.

## 4. Validar y capturar

```powershell
powerbi-report-author validate dashboard\PractiCV.pbip
powerbi-report-author preview dashboard\PractiCV.pbip --host desktop --status
powerbi-report-author preview dashboard\PractiCV.pbip --host desktop --screenshot "docs\assets\practicv-dashboard.png"
```

Resultado de validación: `succeeded`, `errorCount=0`, `warningCount=0`.
Captura revisada: `docs/assets/practicv-dashboard.png`.

## 5. Regenerar el demo

```powershell
backend\.venv\Scripts\python.exe dashboard\build_report.py
```

El generador reescribe el CSV sintético, el modelo, la página y los visuales.
No toca `StaticResources` ni datos reales.

## 6. Límites

- Datos de demo, no un refresh automático del export real.
- Una página; el detalle por fecha se ve en la tabla, no hay slicer de fecha.
- No se publica en Power BI Service; el artefacto es local.
- El PBIP requiere Power BI Desktop y el junction para refrescar.
- No se incluye PII ni secretos.
