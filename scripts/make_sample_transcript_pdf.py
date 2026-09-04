"""Generate a tiny sample Cankaya-like PDF for local API/frontend checks."""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "sample_cankaya.pdf"

TEXT = """
Çankaya University
Official Transcript

2024-2025 Güz Dönemi
CENG 111 Bilgisayar Programlama I Z İng. 3 2 4 6 DD 1.00
MATH 157 Genel Matematik I Z Tr 3 2 4 6 BB 3.00
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    font = Path(r"C:\Windows\Fonts\arial.ttf")
    if not font.exists():
        raise SystemExit(f"Font not found: {font}")
    pdf.add_font("ArialUni", fname=str(font))
    pdf.set_font("ArialUni", size=11)
    for line in TEXT.strip().splitlines():
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(OUT))
    print(OUT)


if __name__ == "__main__":
    main()
