/** Display policy only: never use the official rounded value as engine input. */
export function validOfficialCgpa(value: number | null | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 4
    ? value
    : null;
}

/** Two-decimal rounding/truncation on transcripts is normal; do not alarm at ≤0.01. */
export const GPA_DISPLAY_EPSILON = 0.011;

export function gpaPresentation(officialCgpa: number | null | undefined, derivedCgpa: number | null) {
  const official = validOfficialCgpa(officialCgpa);
  const hasSeparateDerived =
    official !== null &&
    derivedCgpa !== null &&
    Number.isFinite(derivedCgpa) &&
    Math.abs(official - derivedCgpa) > 1e-9;

  return {
    value: official ?? derivedCgpa,
    isOfficial: official !== null,
    label: official !== null ? "GANO" : "Hesaplanan GANO",
    source: official !== null ? "Transkriptte belirtilen resmî GANO" : "Derslerden hesaplanan GANO",
    /** Optional secondary line when official is primary; not an error by itself. */
    derivedSecondary:
      hasSeparateDerived && derivedCgpa !== null
        ? `GradePilot hesabı: ${derivedCgpa.toFixed(2)}`
        : null,
    // Larger gaps may surface in validation; small rounding gaps stay quiet.
    hasDiscrepancy:
      official !== null &&
      derivedCgpa !== null &&
      Math.abs(official - derivedCgpa) > GPA_DISPLAY_EPSILON,
  };
}
