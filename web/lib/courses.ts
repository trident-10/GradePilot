import type { Course } from "@/lib/types";

/**
 * Mirrors parsers.transcript_parser.keep_latest_attempts.
 * Used only to split display lists; GPA is never computed here.
 */
export function selectActiveCourses(courses: Course[]): Course[] {
  const latest = new Map<
    string,
    { rank0: number; rank1: number; course: Course }
  >();

  courses.forEach((course, index) => {
    const rank0 = course.sourceOrder !== null ? 1 : 0;
    const rank1 = course.sourceOrder !== null ? course.sourceOrder : index;
    const previous = latest.get(course.code);
    const isNewer =
      previous === undefined ||
      rank0 > previous.rank0 ||
      (rank0 === previous.rank0 && rank1 >= previous.rank1);

    if (isNewer) {
      latest.set(course.code, { rank0, rank1, course });
    }
  });

  return [...latest.values()].map((item) => item.course);
}

export function selectHistoricalCourses(courses: Course[]): Course[] {
  const active = new Set(selectActiveCourses(courses));
  return courses.filter((course) => !active.has(course));
}
