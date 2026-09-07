import re
from parsers.text_normalization import fold

LABELS = re.compile(
    r"\b(?P<cgpa>cumulative\s+(?:grade\s+point\s+average|gpa)|cgpa|gano|agno|gno|"
    r"genel\s+(?:agirlikli\s+|akademik\s+)?not\s+(?:ortalamasi|ort))\b\.?|"
    r"\b(?P<gpa>(?:semester|term)\s+(?:grade\s+point\s+average|gpa)|dgpa|dno|dano|yano|"
    r"(?:donem|yariyil)\s+(?:not\s+)?(?:ortalamasi|ort)|gpa)\b\.?|"
    r"\b(?P<credit>(?:(?:tamamlanan|completed)\s+)?(?:(?:semester|term|donem|yariyil)\s+)?"
    r"(?:tuk|tnk|d\.\s*kredi|basarilan\s+kredi|credits\s+completed|total\s+(?:local\s+)?credits?|toplam\s+(?:yerel\s+|ulusal\s+)?kredi(?:si)?|"
    r"local\s+credits?|yerel\s+kredi|ulusal\s+kredi|kredi\s+toplami|kredisi|kredi|credits?)\b(?:\s*\(yerel\))?)|"
    r"\b(?P<ects>(?:(?:tamamlanan|kazanilan|completed)\s+)?(?:(?:semester|term|donem|yariyil)\s+)?"
    r"(?:total\s+|toplam\s+)?(?:takts|tects|akts\s*/\s*ects|ects\s*/\s*akts|akts|ects)(?:\s+toplami)?)\b|"
    r"\b(?P<total_course_count>total\s+courses?|(?:kayitli\s+(?:olunan\s+)?)?toplam\s+(?:alinan\s+)?ders(?:\s+sayisi)?)\b|"
    r"\b(?P<semester_count>semester\s+count|donem\s+sayisi)\b"
)
OVERALL_HEADING = re.compile(r"^(?:genel\s+ozet|transcript\s+summary|overall\s+summary|cumulative\s+summary|mezuniyet\s+ozeti|(?:genel\s+akademik|mezuniyet\s+tescil)\b.*\bozeti|mezuniyet\s+kayit\b.*\braporu)\s*:?")
SEMESTER_HEADING = re.compile(r"^(?:(?:semester|term)\s+summary|(?:donem|yariyil)\s+ozeti)\s*:?")
SEMESTER_WORD = re.compile(r"\b(semester|term|donem|yariyil)\b")
COMPLETED_TOTAL = re.compile(r"^(?:tamamlanan\s+(?:toplam|ulusal|yerel)|kazanilan\s+toplam|completed\s+total|basarilan\s+kredi|credits\s+completed)\b")



def is_summary_line(line: str) -> bool:
    normalized = fold(line.strip())
    first = LABELS.search(normalized)
    return bool(OVERALL_HEADING.match(normalized) or SEMESTER_HEADING.match(normalized)
                or (first and first.start() == 0)
                # Wrapped totals may start with an amount from an adjacent
                # cell, followed by explicit DNO/GNO/AKTS labels.
                or (first and re.fullmatch(r"\d+(?:[.,]\d+)?[)\s]+(?:\(\s*(?:deg|degerlendirilen)\s*:\s*)?", normalized[:first.start()])
                    and re.match(r"\s*[:=]", normalized[first.end():])))
