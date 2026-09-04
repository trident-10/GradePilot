/** Display helpers only. Do not compute GPA here. */

export function formatGpa(value: number): string {
  return value.toFixed(2);
}

export function formatSigned(value: number): string {
  const formatted = value.toFixed(2);
  return value > 0 ? `+${formatted}` : formatted;
}

export function weightingCopy(mode: string | null): string {
  if (mode === "ects" || mode === "akts") {
    return "Hesaplama AKTS üzerinden yapılıyor.";
  }
  if (mode === "credit" || mode === "kredi" || mode === "local_credit") {
    return "Hesaplama Kredi üzerinden yapılıyor.";
  }
  return "Hesaplama seçilen GANO ağırlığı üzerinden yapılıyor.";
}

/** Compact contextual chip label — prefer over full weightingCopy in UI. */
export function weightingChip(mode: string | null): string {
  if (isEctsMode(mode)) return "AKTS";
  if (isCreditMode(mode)) return "Kredi";
  return "GANO ağırlığı";
}

export function isEctsMode(mode: string | null): boolean {
  return mode === "ects" || mode === "akts";
}

export function isCreditMode(mode: string | null): boolean {
  return mode === "credit" || mode === "kredi" || mode === "local_credit";
}

export function weightUnitLabel(mode: string | null): string {
  if (isEctsMode(mode)) return "AKTS";
  if (isCreditMode(mode)) return "Kredi";
  return "Ağırlık";
}

export function futureWeightFieldLabel(mode: string | null): string {
  if (isEctsMode(mode)) return "Gelecek dönem toplam AKTS";
  if (isCreditMode(mode)) return "Gelecek dönem toplam kredi";
  return "Gelecek dönem toplam GANO ağırlığı";
}

export function cx(
  ...parts: Array<string | false | null | undefined>
): string {
  return parts.filter(Boolean).join(" ");
}
