import pytest

from parsers.official_summary import extract_official_document


def document(text):
    return extract_official_document(text, [], [])


def test_scaled_official_gpa_with_explanation_is_separate_from_semester_gpa():
    result = document("""[[TABLE_BEGIN]]
2023-2024 Fall
D.Kredi: 17 | AKTS: 30 YANO: 3.82 | GANO: 3.12
[[TABLE_NEXT]]
2023-2024 Spring
D.Kredi: 16 | AKTS: 30 YANO: 3.90 | GANO: 3.24
[[TABLE_END]]
Tamamlanan Ulusal Kredi: 146 Kredi
Tamamlanan Toplam AKTS: 240 AKTS
GENEL NOT ORTALAMASI (GANO): GANO (CGPA): 3.24 / 4.00 (Tüm dönem dersleri ve tekrarlar ağırlıklı olarak tescil edilmiştir)
""")
    assert (result.summary.cgpa, result.summary.total_local_credit, result.summary.total_ects) == (3.24, 146, 240)
    assert [(s.summary.gpa, s.summary.cgpa) for s in result.semesters] == [(3.82, 3.12), (3.90, 3.24)]


def test_dense_summary_units_scale_and_adjacent_metadata_remain_separate():
    result = document("""2023-2024 Bahar
Dönem Kredi: 16 | AKTS: 29\tDÖNEM ORT. (YANO): 3.75
Toplam Alınan Ders Sayısı:\t49 Ders\tMezuniyet Durumu:\tGENEL AKADEMİK NOT ORTALAMASI
Tamamlanan Toplam Ulusal Kredi:\t150 Kredi\t✓ MEZUN EDİLDİ\tGANO (CGPA): 3.08 / 4.00
Tamamlanan Toplam AKTS:\t240 AKTS\tYönetim Kurulu Kararı No: 2024/412\tONUR ÖĞRENCİSİ (HONOURS)
""")
    assert result.summary.cgpa == 3.08
    assert result.summary.total_local_credit == 150
    assert result.summary.total_ects == 240
    assert result.summary.total_course_count == 49
    assert result.semesters[0].summary.gpa == 3.75
    assert result.semesters[0].summary.local_credit == 16
    assert result.semesters[0].summary.ects == 29
    assert len(result.observations) == 7


def test_eight_scoped_semester_summaries_preserve_every_printed_amount():
    blocks = []
    for index, year in enumerate(range(2020, 2024)):
        blocks.append(f"""[[TABLE_BEGIN]]
1. DÖNEM (GÜZ) {year} - {year + 1}
Dönem Kredi: {20 + index} | AKTS: {30 + index}\tDÖNEM ORT. (YANO): 2.83
[[TABLE_NEXT]]
2. DÖNEM (BAHAR) {year} - {year + 1}
Dönem Kredi: {24 + index} | AKTS: {34 + index}\tDÖNEM ORT. (YANO): 3.75
[[TABLE_END]]""")
    result = document("\n".join(blocks))
    assert len(result.semesters) == 8
    assert [s.summary.gpa for s in result.semesters] == [2.83, 3.75] * 4
    assert [s.summary.local_credit for s in result.semesters] == [20, 24, 21, 25, 22, 26, 23, 27]
    assert [s.summary.ects for s in result.semesters] == [30, 34, 31, 35, 32, 36, 33, 37]
    assert result.summary.cgpa is None
    assert result.summary.total_ects is None


@pytest.mark.parametrize("label", ["YANO", "Dönem Ort.", "DÖNEM ORT. (YANO)", "Yarıyıl Not Ort."])
def test_semester_gpa_abbreviations(label):
    result = document(f"2024-2025 Fall\nAKTS: 30 {label}: 3,25")
    assert result.semesters[0].summary.gpa == 3.25
    assert result.semesters[0].summary.ects == 30


@pytest.mark.parametrize("text", [
    "GANO (CGPA): 3,08 / 4,00",
    "GENEL AKADEMİK NOT ORTALAMASI\n3.08 / 4.00",
    "GANO (CGPA)\n3.08 / 4.00",
])
def test_gpa_scale_is_not_a_second_gpa(text):
    result = document(text)
    assert result.summary.cgpa == 3.08
    assert [observation.value for observation in result.observations] == [3.08]


def test_completed_totals_switch_to_document_scope_after_last_semester():
    result = document("""2024-2025 Spring
Dönem Kredi: 18 | AKTS: 30 YANO: 3.25
Tamamlanan Toplam Ulusal Kredi: 150 Kredi
Tamamlanan Toplam AKTS: 240 AKTS
Toplam Alınan Ders Sayısı: 49 Ders
""")
    assert result.summary.total_local_credit == 150
    assert result.summary.total_ects == 240
    assert result.summary.total_course_count == 49
    assert result.semesters[0].summary.local_credit == 18
    assert result.semesters[0].summary.ects == 30


@pytest.mark.parametrize("text", [
    "3.08 / 150 / 240",
    "GANO: 3.08 / 150 / 240",
    "GANO: 3.08 / 0.00",
    "GANO: 4.08 / 4.00",
    "GANO: 3.08 / 150",
    "GANO: 3.08 unknown 4.00",
    "Toplam Alınan Ders Sayısı: 49 unknown",
    "Toplam Alınan Ders Sayısı: 49 51",
    "Toplam Alınan Ders Sayısı: 49 Ders arbitrary prose",
])
def test_ambiguous_or_unlabelled_values_are_not_guessed(text):
    assert document(text).observations == []


def test_conflicting_scaled_gpas_and_course_counts_keep_observations():
    result = document("""GANO: 3.08 / 4.00
GANO: 3.10 / 4.00
Toplam Alınan Ders Sayısı: 49 Ders
Toplam Alınan Ders Sayısı: 51 Ders
""")
    assert result.summary.cgpa is None
    assert result.summary.total_course_count is None
    assert [observation.value for observation in result.observations] == [3.08, 3.1, 49, 51]


def test_explicit_graduation_status_preserves_printed_text():
    result = document("Mezuniyet Durumu: ✓ MEZUN EDİLDİ")
    assert result.summary.graduation_status == "MEZUN EDİLDİ"
    assert result.observations == []
