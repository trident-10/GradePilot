/**
 * Isolated development fixture.
 * Do NOT import this from production UI / AppState.
 * Python backend is the source of truth for transcript data.
 */

export type FixtureCourse = {
  code: string;
  name: string;
  gpaCredit: number;
  ects: number | null;
  localCredit: number | null;
  grade: string;
  semester: string | null;
};

export const FIXTURE_COURSES: FixtureCourse[] = [
  {
    code: "CENG101",
    name: "Programlama",
    gpaCredit: 3,
    ects: 6,
    localCredit: 3,
    grade: "BA",
    semester: "2024 Güz",
  },
];

export const FIXTURE_CREDIT_OPTIONS = [
  { id: "credit", label: "Kredi" },
  { id: "ects", label: "AKTS / ECTS" },
];
