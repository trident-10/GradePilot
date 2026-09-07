"""PDF text acquisition, independent of transcript workflow."""
import pdfplumber
from parsers.pdf_layout import extract_page_text


def extract_text_from_pdf(
    pdf_path: str
) -> str:

    text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_text = extract_page_text(page)

            if not page_text.strip() and page.images:
                # A scanned page in an otherwise textual PDF must not vanish
                # from the transcript and silently lower its course count.
                raise ValueError("PDF contains a page without extractable text.")

            if page_text:
                text += page_text + "\n"

    return text


