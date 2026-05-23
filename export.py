from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import io

def export_results_pdf(result: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Document Intelligence Report", styles['Title']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Summary", styles['Heading1']))
    story.append(Paragraph(result.get("summary", {}).get("oneline", ""), styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(result.get("summary", {}).get("paragraph", ""), styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Entities", styles['Heading1']))
    for entity in result.get("entities", []):
        story.append(Paragraph(f"• {entity}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Risks", styles['Heading1']))
    for risk in result.get("risks", []):
        story.append(Paragraph(f"⚠ {risk}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Insights", styles['Heading1']))
    for insight in result.get("insights", []):
        story.append(Paragraph(f"💡 {insight}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Statistics", styles['Heading1']))
    story.append(Paragraph(f"Pages: {result.get('pages', 0)}", styles['Normal']))
    story.append(Paragraph(f"Words: {result.get('word_count', 0)}", styles['Normal']))
    story.append(Paragraph(f"Time: {result.get('processing_time', 0)}s", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()