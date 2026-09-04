from core.course_impact_engine import analyze_course_impact
from core.future_semester_engine import calculate_projected_cgpa
from core.gpa_engine import calculate_gpa
from core.grade_scale import GRADE_POINTS
from core.required_gpa_engine import calculate_required_semester_gpa
from core.scenario_engine import simulate_multiple_grade_changes
from core.semester_engine import calculate_semester_gpas
from core.strategy_engine import rank_grade_improvements
from core.target_engine import find_target_plan

from models.course import Course

from parsers.transcript_parser import keep_latest_attempts

from services.transcript_service import process_transcript

def load_transcript(pdf_path: str):
    result = process_transcript(pdf_path)

    if result.requires_credit_selection:
        if not result.credit_options:
            raise ValueError(
                "Bu transkript formatında kullanılabilecek "
                "bir kredi alanı tespit edilemedi."
            )

        print(
            "\nGANO hesabında hangi değer kullanılıyor?"
        )
        print(
            "Üniversitenizin genel not ortalaması hesabında "
            "kullandığı değeri seçin."
        )

        for index, option in enumerate(
            result.credit_options,
            start=1,
        ):
            print(
                f"{index} - {option.label} "
                f"(örnek: {option.sample_values})"
            )

        while True:
            choice = input(
                "\nSeçim: "
            ).strip()

            try:
                selected_index = int(choice) - 1
            except ValueError:
                print(
                    "Geçerli bir seçenek numarası gir."
                )
                continue

            if (
                0 <= selected_index
                < len(result.credit_options)
            ):
                break

            print(
                "Geçersiz seçim."
            )

        selected_option = (
            result.credit_options[selected_index]
        )

        result = process_transcript(
            pdf_path,
            gpa_weighting_field=selected_option.field_key,
        )

    if not result.courses:
        raise ValueError(
            "Transkriptten hiçbir ders okunamadı."
        )

    if result.requires_user_confirmation:
        print(
            "\nUYARI: Bu transkript generic parser "
            "ile işlendi."
        )

        print(
            "Çıkarılan ders ve kredi bilgilerini "
            "kontrol etmen önerilir."
        )

    all_courses = result.courses

    active_courses = keep_latest_attempts(
        all_courses
    )

    return active_courses, all_courses

def show_courses(courses):
    print("\n--- DERSLER ---")

    for course in courses:
        print(
            f"{course.code:<10}"
            f"{course.grade:<5}"
            f"{course.gpa_credit:<6}"
            f"{course.name}"
        )


def show_gpa_info(courses):
    gpa = calculate_gpa(
        courses
    )

    total_credits = sum(
        course.gpa_credit
        for course in courses
    )

    print("\n--- GPA BİLGİLERİ ---")
    print(f"Toplam aktif ders : {len(courses)}")
    print(f"Toplam kredi      : {total_credits:.0f}")
    print(f"Mevcut GPA        : {gpa:.2f}")


def select_strategy():
    print("\n--- STRATEJİ SEÇ ---")
    print("1 - En az sayıda ders")
    print("2 - En düşük notlardan başla")
    print("3 - En az not değişimi")

    strategies = {
        "1": "min_courses",
        "2": "lowest_grades",
        "3": "minimal_change",
    }

    while True:
        choice = input(
            "\nSeçim: "
        ).strip()

        if choice in strategies:
            return strategies[choice]

        print(
            "Geçersiz seçim. 1, 2 veya 3 gir."
        )


def select_max_grade():
    print("\n--- MAKSİMUM HEDEF NOT ---")
    print("1 - AA")
    print("2 - BA")
    print("3 - BB")
    print("4 - CB")
    print("5 - CC")

    grades = {
        "1": "AA",
        "2": "BA",
        "3": "BB",
        "4": "CB",
        "5": "CC",
    }

    while True:
        choice = input(
            "\nSeçim: "
        ).strip()

        if choice in grades:
            return grades[choice]

        print(
            "Geçersiz seçim."
        )


def target_gpa_menu(courses):
    print("\n--- HEDEF GPA PLANI ---")

    try:
        target_gpa = float(
            input(
                "Hedef GPA: "
            ).strip()
        )

        strategy = select_strategy()
        max_grade = select_max_grade()

        result = find_target_plan(
            courses=courses,
            target_gpa=target_gpa,
            strategy=strategy,
            max_grade=max_grade,
        )

    except ValueError as error:
        print(
            f"\nHata: {error}"
        )
        return

    print("\n--- PLAN SONUCU ---")

    if result["already_reached"]:
        print(
            "Bu hedef GPA'ya zaten ulaşılmış."
        )
        return

    if not result["reachable"]:
        print(
            f"Hedef GPA {target_gpa:.2f}, "
            f"{max_grade} sınırıyla ulaşılamıyor."
        )

        print(
            f"Ulaşılabilecek yaklaşık GPA: "
            f"{result['projected_gpa']:.2f}"
        )
        return

    print(
        f"Hedef GPA       : {target_gpa:.2f}"
    )

    print(
        f"Maksimum not    : {max_grade}"
    )

    print(
        f"Tahmini GPA     : "
        f"{result['projected_gpa']:.2f}"
    )

    print(
        f"Gerekli ek puan : "
        f"{result['required_point_gain']:.2f}"
    )

    print("\nÖnerilen dersler:")

    for item in result["plan"]:
        print(
            f"{item['course_code']:<10}"
            f"{item['old_grade']} → "
            f"{item['new_grade']}   "
            f"+{item['point_gain']:.2f} puan"
        )


def manual_scenario_menu(courses):
    changes = {}

    valid_course_codes = {
        course.code
        for course in courses
    }

    print("\n--- MANUEL SENARYO ---")

    while True:
        course_code = input(
            "\nDers kodu: "
        ).strip().upper()

        if course_code not in valid_course_codes:
            print(
                "Bu ders bulunamadı."
            )
            continue

        new_grade = input(
            "Yeni not: "
        ).strip().upper()

        changes[course_code] = new_grade

        answer = input(
            "Başka ders ekle? (E/H): "
        ).strip().upper()

        if answer != "E":
            break

    try:
        result = simulate_multiple_grade_changes(
            courses,
            changes
        )

    except ValueError as error:
        print(
            f"\nHata: {error}"
        )
        return

    print("\n--- SENARYO SONUCU ---")

    for change in result["changes"]:
        print(
            f"{change['course_code']:<10}"
            f"{change['old_grade']} → "
            f"{change['new_grade']}"
        )

    print(
        f"\nMevcut GPA : "
        f"{result['current_gpa']:.2f}"
    )

    print(
        f"Yeni GPA   : "
        f"{result['new_gpa']:.2f}"
    )

    difference = result["difference"]

    print(
        f"GPA farkı  : "
        f"{difference:+.3f}"
    )


def show_rankings(courses):
    rankings = rank_grade_improvements(
        courses
    )

    print(
        "\n--- EN AVANTAJLI NOT YÜKSELTMELERİ ---"
    )

    shown = 0

    for item in rankings:
        if item["difference"] <= 0:
            continue

        print(
            f"{item['course_code']:<10}"
            f"{item['old_grade']} → "
            f"{item['new_grade']}   "
            f"{item['difference']:+.3f} GPA"
        )

        shown += 1

        if shown == 10:
            break


def show_main_menu():
    print("\n====================================")
    print("             GRADEPILOT")
    print("====================================")
    print("1 - GPA bilgilerimi göster")
    print("2 - Hedef GPA planı oluştur")
    print("3 - Manuel not senaryosu oluştur")
    print("4 - En avantajlı dersleri göster")
    print("5 - Dersleri göster")
    print("6 - Dönem GPA analizi")
    print("7 - Gelecek dönem simülasyonu")
    print("8 - Ders bazında etki analizi")
    print("9 - Hedef CGPA için gereken dönem GPA")
    print("0 - Çıkış")

def show_semester_gpas(all_courses):
    results = calculate_semester_gpas(
        all_courses
    )

    print("\n--- DÖNEM GPA ANALİZİ ---")

    for result in results:
        print(
            f"{result['semester']:<22}"
            f"GPA: {result['gpa']:.2f}   "
            f"Kredi: {result['credits']:.0f}"
        )


def future_semester_menu(courses):
    future_courses = []

    print("\n--- GELECEK DÖNEM SİMÜLASYONU ---")
    print(
        "Gelecek dönem alacağın dersleri "
        "ve tahmini notlarını gir."
    )

    while True:
        course_code = input(
            "\nDers kodu: "
        ).strip().upper()

        course_name = input(
            "Ders adı: "
        ).strip()

        try:
            credit = float(
                input(
                    "Kredi: "
                ).strip()
            )

            if credit <= 0:
                print(
                    "Kredi 0'dan büyük olmalı."
                )
                continue

        except ValueError:
            print(
                "Kredi sayı olmalı."
            )
            continue

        grade = input(
            "Tahmini not: "
        ).strip().upper()

        if grade not in GRADE_POINTS:
            print(
                "Geçersiz harf notu."
            )
            continue

        future_courses.append(
            Course(
                code=course_code,
                name=course_name,
                gpa_credit=credit,
                grade=grade,
                semester="Future"
            )
        )

        answer = input(
            "Başka ders ekle? (E/H): "
        ).strip().upper()

        if answer != "E":
            break

    result = calculate_projected_cgpa(
        current_courses=courses,
        future_courses=future_courses
    )

    print("\n--- GELECEK DÖNEM SONUCU ---")

    print(
        f"Dönem kredisi    : "
        f"{result['future_credits']:.0f}"
    )

    print(
        f"Dönem GPA        : "
        f"{result['semester_gpa']:.2f}"
    )

    print(
        f"Yeni toplam kredi: "
        f"{result['total_credits']:.0f}"
    )

    print(
        f"Yeni genel GPA   : "
        f"{result['projected_cgpa']:.2f}"
    )


def course_impact_menu(courses):
    print("\n--- DERS BAZINDA ETKİ ANALİZİ ---")

    course_code = input(
        "Ders kodu: "
    ).strip().upper()

    try:
        result = analyze_course_impact(
            courses=courses,
            course_code=course_code
        )

    except ValueError as error:
        print(
            f"\nHata: {error}"
        )
        return

    print("\n--- DERS BİLGİSİ ---")

    print(
        f"Ders       : "
        f"{result['course_code']} - "
        f"{result['course_name']}"
    )

    print(
        f"Kredi      : "
        f"{result['credit']:.0f}"
    )

    print(
        f"Mevcut not : "
        f"{result['current_grade']}"
    )

    if not result["scenarios"]:
        print(
            "\nBu ders zaten en yüksek notta."
        )
        return

    print("\n--- NOT YÜKSELTME ETKİLERİ ---")

    for scenario in result["scenarios"]:
        print(
            f"{scenario['grade']:<3} → "
            f"GPA {scenario['new_gpa']:.3f}   "
            f"{scenario['difference']:+.3f}"
        )

def required_semester_gpa_menu(courses):
    print("\n--- HEDEF CGPA İÇİN GEREKEN DÖNEM GPA ---")

    try:
        future_credits = float(
            input(
                "Gelecek dönem toplam kredi: "
            ).strip()
        )

        target_cgpa = float(
            input(
                "Hedef genel GPA: "
            ).strip()
        )

        result = calculate_required_semester_gpa(
            courses=courses,
            future_credits=future_credits,
            target_cgpa=target_cgpa,
        )

    except ValueError as error:
        print(
            f"\nHata: {error}"
        )
        return

    print("\n--- SONUÇ ---")

    print(
        f"Mevcut GPA         : "
        f"{result['current_cgpa']:.2f}"
    )

    print(
        f"Mevcut kredi       : "
        f"{result['current_credits']:.0f}"
    )

    print(
        f"Gelecek kredi      : "
        f"{result['future_credits']:.0f}"
    )

    print(
        f"Hedef genel GPA    : "
        f"{result['target_cgpa']:.2f}"
    )

    if result["already_reached"]:
        print(
            "\nBu hedef GPA'ya zaten ulaşılmış."
        )
        return

    if not result["reachable"]:
        print(
            "\nBu hedefe belirtilen kredi ile "
            "tek dönemde ulaşmak mümkün değil."
        )

        print(
            f"Gereken dönem GPA: "
            f"{result['required_semester_gpa']:.2f}"
        )

        print(
            "Maksimum mümkün dönem GPA: 4.00"
        )

        return

    print(
        f"\nGereken minimum dönem GPA: "
        f"{result['required_semester_gpa']:.2f}"
    )

    print(
        f"Gereken dönem kalite puanı: "
        f"{result['required_future_points']:.2f}"
    )

def main():
    pdf_path = input(
        "Transkript PDF dosyasının yolunu gir: "
    ).strip().strip('"')

    try:
        courses, all_courses = load_transcript(
            pdf_path
        )

    except (
        FileNotFoundError,
        ValueError
    ) as error:

        print(
            f"\nBaşlatma hatası: {error}"
        )
        return



    while True:
        show_main_menu()

        choice = input(
            "\nSeçim: "
        ).strip()

        if choice == "1":
            show_gpa_info(
                courses
            )

        elif choice == "2":
            target_gpa_menu(
                courses
            )

        elif choice == "3":
            manual_scenario_menu(
                courses
            )

        elif choice == "4":
            show_rankings(
                courses
            )

        elif choice == "5":
            show_courses(
                courses
            )

        elif choice == "6":
            show_semester_gpas(
                all_courses
            )

        elif choice == "7":
            future_semester_menu(
                courses
            )

        elif choice == "8":
            course_impact_menu(
                courses
            )
        elif choice == "9":
            required_semester_gpa_menu(
                courses
            )       

        elif choice == "0":
            print(
                "\nGradePilot kapatılıyor."
            )
            break

        else:
            print(
                "\nGeçersiz seçim."
            )


if __name__ == "__main__":
    main()