"""Generate the PractiCV v0.2 Power BI project and its synthetic data.

The CSV is synthetic: no CVs, emails, or real applications. The report is a
single funnel page backed by one imported table.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPORT = ROOT / "PractiCV.Report"
MODEL = ROOT / "PractiCV.SemanticModel"

STATUSES = [
    ("saved", "Guardada"),
    ("applied", "Postulada"),
    ("interview", "Entrevista"),
    ("offer", "Oferta"),
    ("rejected", "Rechazada"),
]
COMPANIES = [
    ("Banco Demo", "Practicante de Datos"),
    ("Retail Demo", "Practicante de BI"),
    ("Seguros Demo", "Practicante de Riesgos"),
    ("Minera Demo", "Practicante de Operaciones"),
    ("Consultora Demo", "Practicante de Analitica"),
    ("Fintech Demo", "Practicante de Producto"),
]
COUNTS = {"saved": 8, "applied": 6, "interview": 4, "rejected": 3, "offer": 3}


def write_data() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    rows = []
    index = 0
    for status, label in STATUSES:
        status_order = [value for value, _ in STATUSES].index(status) + 1
        for _ in range(COUNTS[status]):
            company, title = COMPANIES[index % len(COMPANIES)]
            match = 55 + (index * 7) % 40
            rows.append(
                {
                    "empresa": company,
                    "puesto": title,
                    "estado": status,
                    "estado_etiqueta": label,
                    "funnel_etapa": f"{status_order}. {label}",
                    "orden_embudo": status_order,
                    "match": match,
                    "must_have": max(40, match - 8),
                    "decision": "Aplicar" if match >= 70 else "Preparar CV",
                    "postulada": f"2026-11-{(index % 24) + 1:02d}",
                    "proxima_accion": f"2026-12-{(index % 24) + 1:02d}",
                    "nota": "Dato sintetico de demo.",
                }
            )
            index += 1
    path = DATA / "applications.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def literal(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def textbox(name: str, x: int, y: int, width: int, height: int, text: str, size: int, bold: bool = False) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": 1000, "height": height, "width": width, "tabOrder": 1000},
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {
                                            "value": text,
                                            "textStyle": {
                                                "fontFamily": "Segoe UI Semibold" if bold else "Segoe UI",
                                                "fontSize": f"{size}px",
                                                "color": "#0F172A",
                                                "fontWeight": "bold" if bold else "normal",
                                            },
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            },
            "visualContainerObjects": {
                "background": [{"properties": {"show": literal("false")}}],
                "border": [{"properties": {"show": literal("false")}}],
            },
        },
    }


def card(name: str, x: int, label: str, measure: str, number_format: str = "0") -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
        "name": name,
        "position": {"x": x, "y": 118, "z": 1000, "height": 88, "width": 226, "tabOrder": 1000},
        "visual": {
            "visualType": "cardVisual",
            "query": {
                "queryState": {
                    "Data": {
                        "projections": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": {"SourceRef": {"Entity": "Applications"}},
                                        "Property": measure,
                                    }
                                },
                                "queryRef": f"Applications.{measure}",
                                "nativeQueryRef": measure,
                            }
                        ]
                    }
                }
            },
            "objects": {
                "value": [
                    {
                        "properties": {
                            "fontSize": literal("26D"),
                            "fontColor": {
                                "solid": {"color": literal("'#0F172A'")}
                            },
                            "bold": literal("true"),
                            "labelPrecision": literal("1L" if number_format == "0.0" else "0L"),
                        },
                        "selector": {"id": "default"},
                    }
                ],
                "label": [
                    {
                        "properties": {
                            "show": literal("true"),
                            "text": literal(f"'{label}'"),
                            "fontSize": literal("11D"),
                            "fontColor": {"solid": {"color": literal("'#475569'")}},
                        },
                        "selector": {"id": "default"},
                    }
                ],
            },
            "visualContainerObjects": {
                "background": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal("'#FFFFFF'")}}}}],
                "border": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal("'#E2E8F0'")}}, "radius": literal("8D")}}],
                "visualHeader": [{"properties": {"show": literal("false")}}],
                "title": [{"properties": {"show": literal("false")}}],
            },
        },
    }


def field(column: str, role: str = "Column") -> dict:
    return {
        "field": {
            role: {
                "Expression": {"SourceRef": {"Entity": "Applications"}},
                "Property": column,
            }
        },
        "queryRef": f"Applications.{column}",
        "nativeQueryRef": column,
    }


def funnel(name: str) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
        "name": name,
        "position": {"x": 24, "y": 218, "z": 1000, "height": 420, "width": 600, "tabOrder": 1000},
        "visual": {
            "visualType": "funnel",
            "query": {
                "queryState": {
                    "Category": {"projections": [field("funnel_etapa")]},
                    "Y": {"projections": [field("Total", "Measure")]},
                },
            },
            "visualContainerObjects": {
                "background": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal("'#FFFFFF'")}}}}],
                "border": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal("'#E2E8F0'")}}, "radius": literal("8D")}}],
                "visualHeader": [{"properties": {"show": literal("false")}}],
                "title": [
                    {
                        "properties": {
                            "show": literal("true"),
                            "text": literal("'Embudo por etapa'"),
                            "fontSize": literal("14D"),
                            "bold": literal("true"),
                            "fontColor": {"solid": {"color": literal("'#0F172A'")}},
                        }
                    }
                ],
                "subTitle": [{"properties": {"show": literal("false")}}],
            },
        },
    }


def slicer(name: str, x: int, y: int, width: int, height: int) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": 1000, "height": height, "width": width, "tabOrder": 1000},
        "visual": {
            "visualType": "slicer",
            "query": {"queryState": {"Values": {"projections": [field("estado_etiqueta")]}}},
            "objects": {
                "data": [{"properties": {"mode": literal("'Dropdown'")}}],
                "header": [
                    {
                        "properties": {
                            "show": literal("true"),
                            "text": literal("'Estado'"),
                            "showRestatement": literal("false"),
                        }
                    }
                ],
            },
            "visualContainerObjects": {
                "background": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal("'#FFFFFF'")}}}}],
                "border": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal("'#E2E8F0'")}}, "radius": literal("8D")}}],
                "visualHeader": [{"properties": {"show": literal("false")}}],
            },
        },
    }


def table(name: str) -> dict:
    columns = ["puesto", "empresa", "estado_etiqueta", "match", "proxima_accion"]
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
        "name": name,
        "position": {"x": 650, "y": 218, "z": 1000, "height": 420, "width": 606, "tabOrder": 1000},
        "visual": {
            "visualType": "tableEx",
            "query": {"queryState": {"Values": {"projections": [field(column) for column in columns]}}},
            "visualContainerObjects": {
                "background": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal("'#FFFFFF'")}}}}],
                "border": [{"properties": {"show": literal("true"), "color": {"solid": {"color": literal("'#E2E8F0'")}}, "radius": literal("8D")}}],
                "visualHeader": [{"properties": {"show": literal("false")}}],
                "title": [
                    {
                        "properties": {
                            "show": literal("true"),
                            "text": literal("'Postulaciones'"),
                            "fontSize": literal("14D"),
                            "bold": literal("true"),
                            "fontColor": {"solid": {"color": literal("'#0F172A'")}},
                        }
                    }
                ],
            },
        },
    }


def write_report() -> None:
    page_name = "practicv-funnel"
    visuals = {
        "practicv-title": textbox("practicv-title", 24, 16, 1100, 64, "PractiCV - Embudo de postulaciones", 30, True),
        "practicv-subtitle": textbox(
            "practicv-subtitle",
            24,
            78,
            1100,
            34,
            "Datos sinteticos de demo; el embudo se alimenta del export de PractiCV.",
            11,
        ),
        "practicv-total": card("practicv-total", 24, "Total", "Total"),
        "practicv-applied": card("practicv-applied", 266, "Postuladas", "Postuladas"),
        "practicv-interview": card("practicv-interview", 508, "Entrevistas", "Entrevistas"),
        "practicv-offer": card("practicv-offer", 750, "Ofertas", "Ofertas"),
        "practicv-match": card("practicv-match", 992, "Match promedio", "Match promedio", "0.0"),
        "practicv-slicer": slicer("practicv-slicer", 1136, 16, 120, 80),
        "practicv-funnel-visual": funnel("practicv-funnel-visual"),
        "practicv-table": table("practicv-table"),
        "practicv-footer": textbox(
            "practicv-footer",
            24,
            650,
            1232,
            34,
            "PractiCV v0.2 - dashboard local; no incluye PII.",
            10,
        ),
    }

    for directory in (
        REPORT / "definition" / "pages" / page_name / "visuals",
        MODEL / "definition" / "tables",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    report_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {
            "baseTheme": {
                "name": "Fluent2-CY26SU10",
                "reportVersionAtImport": {
                    "visual": "2.11.0",
                    "report": "3.4.0",
                    "page": "2.3.1",
                },
                "type": "SharedResources",
            }
        },
        "resourcePackages": [
            {
                "name": "SharedResources",
                "type": "SharedResources",
                "items": [
                    {
                        "name": "Fluent2-CY26SU10",
                        "path": "BaseThemes/Fluent2-CY26SU10.json",
                        "type": "BaseTheme",
                    }
                ],
            }
        ],
        "settings": {
            "useStylableVisualContainerHeader": True,
            "exportDataMode": "AllowSummarized",
            "useEnhancedTooltips": True,
        },
    }
    (REPORT / "definition" / "report.json").write_text(
        json.dumps(report_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (REPORT / "definition" / "version.json").write_text(
        json.dumps(
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
                "version": "2.0.0",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (REPORT / "definition.pbir").write_text(
        json.dumps(
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
                "version": "4.0",
                "datasetReference": {"byPath": {"path": "../PractiCV.SemanticModel"}},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (REPORT / ".platform").write_text(
        json.dumps(
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.1.0/schema.json",
                "metadata": {"type": "Report", "displayName": "PractiCV"},
                "config": {"version": "2.0", "logicalId": "a1b2c3d4-1111-4222-8333-944455556666"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (REPORT / "definition" / "pages" / "pages.json").write_text(
        json.dumps(
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
                "pageOrder": [page_name],
                "activePageName": page_name,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    page = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": page_name,
        "displayName": "Embudo",
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
        "objects": {
            "background": [
                {
                    "properties": {
                        "color": {"solid": {"color": literal("'#F8FAFC'")}},
                        "transparency": literal("0D"),
                    }
                }
            ]
        },
    }
    (REPORT / "definition" / "pages" / page_name / "page.json").write_text(
        json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name, visual in visuals.items():
        folder = REPORT / "definition" / "pages" / page_name / "visuals" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "visual.json").write_text(
            json.dumps(visual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    model = """model PractiCV
\tculture: es-PE
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tsourceQueryCulture: es-PE
\tdataAccessOptions
\t\tlegacyRedirects
\t\treturnErrorValuesAsNull

ref table Applications
"""
    (MODEL / "definition" / "model.tmdl").write_text(model, encoding="utf-8")
    (MODEL / "definition" / "database.tmdl").write_text(
        "database PractiCV\n\tcompatibilityLevel: 1702\n", encoding="utf-8"
    )
    (MODEL / "definition" / "expressions.tmdl").write_text(
        '/// Carpeta del CSV sintetico del dashboard.\nexpression DataFolder = "C:\\Users\\Public\\practicv\\dashboard\\data" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n',
        encoding="utf-8",
    )
    (MODEL / "definition.pbism").write_text(
        json.dumps({"version": "4.2", "settings": {"qnaEnabled": True}}, indent=2) + "\n",
        encoding="utf-8",
    )
    (MODEL / ".platform").write_text(
        json.dumps(
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
                "metadata": {"type": "SemanticModel", "displayName": "PractiCV"},
                "config": {"version": "2.0", "logicalId": "b2c3d4e5-2222-4333-8444-955566667777"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    table_tmdl = """table Applications
\tcolumn empresa
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: empresa

\tcolumn puesto
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: puesto

\tcolumn estado
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: estado

\tcolumn estado_etiqueta
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: estado_etiqueta
\t\tsortByColumn: orden_embudo

\tcolumn funnel_etapa
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: funnel_etapa

\tcolumn orden_embudo
\t\tdataType: int64
\t\tsummarizeBy: none
\t\tsourceColumn: orden_embudo

\tcolumn match
\t\tdataType: double
\t\tsummarizeBy: none
\t\tsourceColumn: match

\tcolumn must_have
\t\tdataType: double
\t\tsummarizeBy: none
\t\tsourceColumn: must_have

\tcolumn decision
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: decision

\tcolumn postulada
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: postulada

\tcolumn proxima_accion
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: proxima_accion

\tcolumn nota
\t\tdataType: string
\t\tsummarizeBy: none
\t\tsourceColumn: nota

\tmeasure Total = COUNTROWS('Applications')
\t\tformatString: 0

\tmeasure Postuladas = CALCULATE([Total], Applications[estado] = "applied")
\t\tformatString: 0

\tmeasure Entrevistas = CALCULATE([Total], Applications[estado] = "interview")
\t\tformatString: 0

\tmeasure Ofertas = CALCULATE([Total], Applications[estado] = "offer")
\t\tformatString: 0

\tmeasure 'Match promedio' = AVERAGE(Applications[match])
\t\tformatString: 0.0

\tpartition Applications = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Csv.Document(File.Contents(DataFolder & "\\applications.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
\t\t\t\t    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t\t\t    Typed = Table.TransformColumnTypes(Promoted, {{"empresa", type text}, {"puesto", type text}, {"estado", type text}, {"estado_etiqueta", type text}, {"funnel_etapa", type text}, {"orden_embudo", Int64.Type}, {"match", type number}, {"must_have", type number}, {"decision", type text}, {"postulada", type text}, {"proxima_accion", type text}, {"nota", type text}})
\t\t\t\tin
\t\t\t\t    Typed
"""
    (MODEL / "definition" / "tables" / "Applications.tmdl").write_text(table_tmdl, encoding="utf-8")
    (ROOT / "PractiCV.pbip").write_text(
        json.dumps(
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
                "version": "1.0",
                "artifacts": [{"report": {"path": "PractiCV.Report"}}],
                "settings": {"enableAutoRecovery": True},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    write_data()
    write_report()
    print(f"data={DATA / 'applications.csv'}")
    print(f"report={REPORT}")
    print(f"model={MODEL}")
