/**
 * Presentation-only helpers for dashboard charts and filters.
 *
 * These functions count or compare values already stored on course/semester
 * records from the backend. They do not compute GPA, weights, or academic
 * outcomes.
 */

import { LETTER_GRADES } from "@/lib/grades";
import type { Course, SemesterSummary } from "@/lib/types";

export type GradeCount = {
  grade: (typeof LETTER_GRADES)[number];
  count: number;
};

/** Count active-course letter grades as they appear on transcript rows. */
export function countActiveGrades(courses: Course[]): GradeCount[] {
  const tallies = new Map<string, number>();
  for (const course of courses) {
    tallies.set(course.grade, (tallies.get(course.grade) ?? 0) + 1);
  }
  return LETTER_GRADES.map((grade) => ({
    grade,
    count: tallies.get(grade) ?? 0,
  }));
}

/** Pick the backend semester row with the highest already-computed GPA. */
export function highestSemesterSummary(
  semesters: SemesterSummary[],
): SemesterSummary | null {
  if (semesters.length === 0) return null;
  return semesters.reduce((best, row) => (row.gpa > best.gpa ? row : best));
}
