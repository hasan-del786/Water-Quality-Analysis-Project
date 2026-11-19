"""Renders the project's Python source as syntax-highlighted pictures and appends them to the report PDF.
Output: Water_Quality_Analysis_Report_with_Code.pdf   Install: pip install pygments pillow reportlab pypdf"""
import io
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import PythonLexer
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PIL import Image

FILES = ["generate_simulated_data.py", "water_quality_analysis.py"]
LINES_PER_PAGE = 46
PW, PH = landscape(A4); M = 1.5 * 28.35

fmt = lambda start: ImageFormatter(font_name="DejaVu Sans Mono", font_size=18, line_numbers=True,
                                   line_number_start=start, style="friendly", image_pad=10, line_pad=3)
pages = []
for fn in FILES:
    lines = open(fn, encoding="utf-8").read().splitlines()
    for a in range(0, len(lines), LINES_PER_PAGE):
        chunk = "\n".join(lines[a:a + LINES_PER_PAGE])
        png = highlight(chunk, PythonLexer(), fmt(a + 1))
        pages.append((fn, a + 1, min(a + LINES_PER_PAGE, len(lines)), Image.open(io.BytesIO(png))))

buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=landscape(A4))
for k, (fn, s, e, img) in enumerate(pages, 1):
    c.setFont("Helvetica-Bold", 12); c.setFillColor(colors.HexColor("#1F4E79"))
    c.drawString(M, PH - M, f"Code: {fn}   (lines {s}-{e})")
    box_w, box_h = PW - 2 * M, PH - 2 * M - 22
    sc = min(box_w / img.width, box_h / img.height)
    w, h = img.width * sc, img.height * sc
    c.setStrokeColor(colors.HexColor("#999999")); c.rect(M, PH - M - 12 - h, w, h)
    c.drawImage(ImageReader(img), M, PH - M - 12 - h, w, h)
    c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#666666"))
    c.drawString(M, 0.8 * 28.35, "Drinking-Water Quality Analysis - source code (simulated data for learning and analysis)")
    c.drawRightString(PW - M, 0.8 * 28.35, f"Code page {k} of {len(pages)}")
    c.showPage()
c.save(); buf.seek(0)

w = PdfWriter()
for p in PdfReader("Water_Quality_Analysis_Report.pdf").pages: w.add_page(p)
for p in PdfReader(buf).pages: w.add_page(p)
w.add_metadata({"/Title": "Drinking-Water Quality Analysis - report and code", "/Author": "Hasan Ali"})
w.write("Water_Quality_Analysis_Report_with_Code.pdf")
print("pages:", len(PdfReader("Water_Quality_Analysis_Report_with_Code.pdf").pages))
