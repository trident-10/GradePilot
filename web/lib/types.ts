export type AppPhase =
  | "empty"
  | "uploading"
  | "credit_selection"
  | "confirmation"
  | "ready"
  | "error";

/** Public GPA weighting choice from the backend (never invent client-side). */
export type CreditOption = {
  id: string;
  label: string;
};

/** Course row mapped from the Python backend response. */
export type Course = {
  code: string;
  name: string;
  gpaCredit: number;
  ects: number | null;
  localCredit: number | null;
  grade: string;
  semester: string | null;
  /** Original transcript extraction order. Do not display. */
  sourceOrder: number | null;
};

export type SemesterSummary = {
  semester: string;
  gpa: number;
  weight: number;
  courseCount: number;
};

export type AcademicSummary = {
  currentGpa: number;
  totalGpaWeight: number;
  activeCourseCount: number;
  semesters: SemesterSummary[];
};

/** Legacy display helpers for unused placeholder components. */
export type SemesterPoint = {
  label: string;
  gpa: number;
};

export type ImprovementRow = {
  code: string;
  from: string;
  to: string;
  points: number;
};

/**
 * Academic result fields that must come from the Python backend.
 * Frontend only stores and displays these; it must not compute GPA.
 */
export type TranscriptResult = {
  formatName: string | null;
  warnings: string[];
  courses: Course[];
};
