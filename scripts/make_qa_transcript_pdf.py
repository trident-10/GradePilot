"""Generate a richer multi-semester Cankaya-like PDF for local visual QA only.

Not used by the test suite; writes outside the repo so fixtures stay untouched.
"""

from pathlib import Path

from fpdf import FPDF

OUT = Path(r"C:\Temp\qa_transcript.pdf")

TEXT = """
Çankaya University
Official Transcript

2023-2024 Güz Dönemi
CENG 111 Bilgisayar Programlama I Z İng. 3 2 4 6 DD 1.00
MATH 157 Genel Matematik I Z Tr 3 2 4 6 BB 3.00
PHYS 101 Genel Fizik I Z İng. 3 2 4 6 CC 2.00
TURK 101 Türk Dili I Z Tr 2 0 2 2 BA 3.50
HIST 201 Atatürk İlkeleri I Z Tr 2 0 2 2 AA 4.00
ENG 121 İngilizce I Z İng. 3 0 3 3 CB 2.50

2023-2024 Bahar Dönemi
CENG 112 Bilgisayar Programlama II Z İng. 3 2 4 6 CB 2.50
MATH 158 Genel Matematik II Z Tr 3 2 4 6 CC 2.00
PHYS 102 Genel Fizik II Z İng. 3 2 4 6 DC 1.50
TURK 102 Türk Dili II Z Tr 2 0 2 2 AA 4.00
HIST 202 Atatürk İlkeleri II Z Tr 2 0 2 2 BA 3.50
ENG 122 İngilizce II Z İng. 3 0 3 3 BB 3.00

2024-2025 Güz Dönemi
CENG 218 Veri Yapıları Z İng. 3 2 4 7 DC 1.50
CENG 221 Ayrık Hesaplama Yapıları Z İng. 3 0 3 6 CC 2.00
CENG 220 Sayısal Mantık Tasarımı Z İng. 3 2 4 6 BB 3.00
MATH 275 Lineer Cebir Z Tr 3 0 3 5 CB 2.50
STAT 293 Olasılık ve İstatistik Z Tr 3 0 3 5 BA 3.50
CENG 111 Bilgisayar Programlama I Z İng. 3 2 4 6 BB 3.00

2024-2025 Bahar Dönemi
CENG 316 Yazılım Mühendisliği Z İng. 3 2 4 7 BA 3.50
CENG 331 İşletim Sistemleri Z İng. 3 2 4 7 CB 2.50
CENG 371 Veritabanı Yönetimi Z İng. 3 2 4 7 AA 4.00
CENG 302 Algoritma Analizi Z İng. 3 0 3 6 BB 3.00
ECON 213 Ekonomiye Giriş S Tr 3 0 3 4 CC 2.00
CENG 384 Sinyaller ve Sistemler Z İng. 3 0 3 5 DC 1.50

2025-2026 Güz Dönemi
CENG 408 Yenilikçi Sistem Tasarımı Z İng. 2 2 3 8 BA 3.50
CENG 435 Bilgisayar Ağları Z İng. 3 0 3 6 BB 3.00
CENG 476 Bilgisayar Grafikleri S İng. 3 0 3 5 CB 2.50
CENG 218 Veri Yapıları Z İng. 3 2 4 7 BB 3.00
CENG 241 Nesneye Yönelik Programlama Z İng. 3 2 4 6 DD 1.00
MAN 351 Yönetim ve Organizasyon S Tr 3 0 3 4 AA 4.00
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    font = Path(r"C:\Windows\Fonts\arial.ttf")
    if not font.exists():
        raise SystemExit(f"Font not found: {font}")
    pdf.add_font("ArialUni", fname=str(font))
    pdf.set_font("ArialUni", size=10)
    for line in TEXT.strip().splitlines():
        pdf.cell(0, 7, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(OUT))
    print(OUT)


if __name__ == "__main__":
    main()
