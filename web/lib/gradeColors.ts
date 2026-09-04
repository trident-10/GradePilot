import { LETTER_GRADES } from "@/lib/grades";

function letterKey(grade: string): string | null {
  const key = grade.toUpperCase();
  if (!(LETTER_GRADES as readonly string[]).includes(key)) return null;
  return key.toLowerCase();
}

export function gradeBadgeClass(grade: string): string {
  const key = letterKey(grade);
  return key ? `gp-grade-${key}` : "bg-surface-muted text-muted";
}

export function gradeBarClass(grade: string): string {
  const key = letterKey(grade);
  return key ? `gp-grade-bar-${key}` : "bg-info/70";
}
