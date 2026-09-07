"use client";

import { useState } from "react";
import { GhostButton, InlineNotice, PrimaryButton, Section } from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { TranscriptValidationFrame } from "@/components/upload/TranscriptValidationFrame";
import { cx } from "@/lib/display";

const systems = [
  { id: "credit", label: "Kredi / Ulusal Kredi (UK)" },
  { id: "ects", label: "AKTS / ECTS" },
] as const;

export function ManualCreditMapping() {
  const { mappingCandidates, isBusy, error, submitManualMapping, resetTranscript } = useAppState();
  const [system, setSystem] = useState<"credit" | "ects" | null>(null);
  const [selectedColumn, setSelectedColumn] = useState("");
  const candidates = mappingCandidates.map((candidate, index) => ({
    ...candidate,
    label: candidate.label.trim() || `Sütun ${String.fromCharCode(65 + index)}`,
  }));
  const canContinue = system !== null && candidates.some((candidate) => candidate.id === selectedColumn) && !isBusy;

  return (
    <TranscriptValidationFrame>
      <Section
        title="Kredi bilgisini doğrulayalım"
        description="Derslerinizi okuduk, ancak kredi başlığını kesinleştiremedik. Yalnızca GANO’da kullanılan bilgiyi doğrulamanız yeterli."
      >
        <div className="space-y-6">
          {error ? (
            <div role="alert">
              <InlineNotice tone="caution">{error.description} Seçiminizi buradan düzeltebilirsiniz.</InlineNotice>
            </div>
          ) : null}
          {candidates.length === 0 ? (
            <InlineNotice tone="caution">Kredi sütunu bulunamadı. Yeni bir PDF seçin.</InlineNotice>
          ) : (
            <>
              <fieldset disabled={isBusy} className="min-w-0" aria-describedby="credit-system-help">
                <legend className="mb-3 text-base font-semibold text-ink">GANO hesabında hangi sistem kullanılıyor?</legend>
                <div className="grid gap-3 sm:grid-cols-2">
                  {systems.map((option) => (
                    <label key={option.id} className={cx(
                      "flex min-h-16 min-w-0 cursor-pointer items-center gap-3 rounded-xl border p-4 focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-accent",
                      system === option.id ? "border-accent bg-accent-soft" : "border-rule bg-surface-muted/40",
                    )}>
                      <input type="radio" name="gano-credit-system" value={option.id}
                        checked={system === option.id}
                        onChange={() => { setSystem(option.id); setSelectedColumn(""); }}
                        className="size-5 shrink-0 accent-[var(--accent)]" />
                      <span className="text-sm font-semibold text-ink">{option.label}</span>
                    </label>
                  ))}
                </div>
                <p id="credit-system-help" className="mt-3 text-sm leading-6 text-muted">
                  Emin değilseniz transkriptinizdeki açıklamayı veya üniversitenizin not yönetmeliğini kontrol edin.
                </p>
              </fieldset>
              {system !== null ? (
                <fieldset disabled={isBusy} className="min-w-0" aria-describedby="credit-column-help">
                  <legend className="mb-2 text-base font-semibold text-ink">
                    PDF’deki {system === "credit" ? "Kredi / UK" : "AKTS / ECTS"} değerleri hangi kartla aynı?
                  </legend>
                  <p id="credit-column-help" className="mb-4 text-sm leading-6 text-muted">
                    İlk derslerin değerlerini PDF’nizle karşılaştırıp tek bir kart seçin. Diğer sütunları seçmenize gerek yok.
                  </p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {candidates.map((candidate) => {
                      const active = candidate.id === selectedColumn;
                      return (
                        <label key={candidate.id} className={cx(
                          "min-w-0 cursor-pointer rounded-xl border p-4 focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-accent",
                          active ? "border-accent bg-accent-soft shadow-[inset_3px_0_0_0_var(--accent)]" : "border-rule bg-surface-muted/40",
                        )}>
                          <span className="flex items-center gap-3">
                            <input type="radio" name="gano-credit-column" value={candidate.id}
                              checked={active} onChange={() => setSelectedColumn(candidate.id)}
                              className="size-5 shrink-0 accent-[var(--accent)]" />
                            <span className="min-w-0 break-words text-base font-semibold text-ink">{candidate.label}</span>
                            {active ? <span aria-hidden className="ml-auto shrink-0 text-xs font-semibold text-accent">Seçildi</span> : null}
                          </span>
                          <span className="mt-3 block text-xs text-muted">İlk derslerden örnekler</span>
                          <span className="mt-2 flex flex-wrap gap-2">
                            {candidate.sampleValues.slice(0, 4).map((value, index) => (
                              <span key={index} className="min-w-10 rounded-lg border border-rule bg-surface px-3 py-2 text-center text-lg font-semibold tabular-nums text-ink">{value}</span>
                            ))}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                </fieldset>
              ) : null}
            </>
          )}
        </div>
      </Section>
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <PrimaryButton type="button" className="w-full sm:w-auto" disabled={!canContinue} onClick={() => {
          if (canContinue && system !== null) {
            void submitManualMapping(system === "credit" ? selectedColumn : null, system === "ects" ? selectedColumn : null, system);
          }
        }}>{isBusy ? "Hazırlanıyor…" : "Analize Devam Et"}</PrimaryButton>
        <GhostButton type="button" className="w-full sm:w-auto" disabled={isBusy} onClick={resetTranscript}>Yeni PDF Seç</GhostButton>
      </div>
    </TranscriptValidationFrame>
  );
}
