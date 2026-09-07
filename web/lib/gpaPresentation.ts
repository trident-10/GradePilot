/** Display policy: prefer printed transcript CGPA; never invent values. */
export function validOfficialCgpa(value: number | null | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 4
    ? value
    : null;
}

export function gpaPresentation(officialCgpa: number | null | undefined, derivedCgpa: number | null) {
  const official = validOfficialCgpa(officialCgpa);
  return {
    value: official ?? derivedCgpa,
    isOfficial: official !== null,
    label: official !== null ? "GANO" : "Hesaplanan GANO",
    source: official !== null ? "Transkriptte belirtilen resmî GANO" : "Derslerden hesaplanan GANO",
  };
}
