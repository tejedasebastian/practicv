from __future__ import annotations

from io import BytesIO

from docx import Document
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf_cv() -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, title="CV Demo")
    styles = getSampleStyleSheet()
    skills_table = Table(
        [
            ["Python", "PowerBI", "SQL"],
            ["FastAPI", "Docker", "Excel"],
        ]
    )
    skills_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story = [
        Paragraph("Sebastian Demo", styles["Title"]),
        Paragraph("sebas.demo@example.com | +51 987 654 321", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("EXPERIENCIA", styles["Heading2"]),
        Paragraph("Practicante de datos en Banco Demo (2025-2026)", styles["Normal"]),
        Paragraph("Automaticé reportes con Python y SQL.", styles["Normal"]),
        Paragraph("PROYECTOS", styles["Heading2"]),
        Paragraph("Dashboard de prácticas con PowerBI y Excel.", styles["Normal"]),
        Paragraph("HABILIDADES", styles["Heading2"]),
        skills_table,
        Paragraph("CERTIFICACIONES", styles["Heading2"]),
        Paragraph("Power BI Intermedio", styles["Normal"]),
        Paragraph("IDIOMAS", styles["Heading2"]),
        Paragraph("Inglés intermedio", styles["Normal"]),
    ]
    document.build(story)
    return buffer.getvalue()


def build_docx_cv() -> bytes:
    document = Document()
    document.add_heading("Sebastian Demo", level=0)
    document.add_paragraph("sebas.demo@example.com | +51 987 654 321")
    document.add_heading("Experiencia", level=1)
    document.add_paragraph("Practicante de datos en Banco Demo (2025-2026)")
    document.add_paragraph("Automaticé reportes con Python y SQL.")
    document.add_heading("Habilidades", level=1)
    table = document.add_table(rows=2, cols=3)
    table.cell(0, 0).text = "Python"
    table.cell(0, 1).text = "PowerBI"
    table.cell(0, 2).text = "SQL"
    table.cell(1, 0).text = "FastAPI"
    table.cell(1, 1).text = "Docker"
    table.cell(1, 2).text = "Excel"
    document.add_heading("Idiomas", level=1)
    document.add_paragraph("Inglés intermedio")
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
