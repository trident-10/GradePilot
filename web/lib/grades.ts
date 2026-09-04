/** Must match core/grade_scale.py GRADE_POINTS keys. */
export const LETTER_GRADES = [
  "AA",
  "BA",
  "BB",
  "CB",
  "CC",
  "DC",
  "DD",
  "FD",
  "FF",
] as const;

export type LetterGrade = (typeof LETTER_GRADES)[number];
