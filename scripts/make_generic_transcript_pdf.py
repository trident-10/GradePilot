"""Generate a generic-format transcript PDF for local visual QA only.

The generic parser asks the user to confirm extracted rows, so this exercises
the confirmation screen. Writes outside the repo so fixtures stay untouched.
"""

from pathlib import Path

from fpdf import FPDF

OUT = Path(r"C:\Temp\qa_generic_transcript.pdf")

TEXT = """
Example University
Academic Transcript

Course Credit ECTS Grade

CENG101 Programming 3 6 BA
CENG102 Data Structures 4 7 BB
MATH101 Calculus 4 6 CB
PHYS101 Physics 3 5 AA
CENG201 Algorithms 3 6 CC
CENG202 Operating Systems 4 7 DC
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
