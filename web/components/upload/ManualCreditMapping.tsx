"use client";

import { useState } from "react";
import { GhostButton, InlineNotice, PrimaryButton, Section } from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { TranscriptValidationFrame } from "@/components/upload/TranscriptValidationFrame";

export function ManualCreditMapping() {
  const { mappingCandidates, isBusy, error, submitManualMapping, resetTranscript } = useAppState();
  const [localCreditField, setLocalCreditField] = useState("");
  const [ectsField, setEctsField] = useState("");
  const duplicate = localCreditField !== "" && localCreditField === ectsField;
  const canContinue = mappingCandidates.length > 0 &&
    (localCreditField !== "" || ectsField !== "") && !duplicate && !isBusy;
  const candidates = mappingCandidates.map((candidate, index) => ({
    ...candidate,
    label: candidate.label.trim() || `Sütun ${String.fromCharCode(65 + index)}`,
  }));

  return (
    <TranscriptValidationFrame>
      <Section
        title="Kredi sütunlarını eşleştir"
        description="Bazı başlıklar okunamadı. PDF’deki kredi ve AKTS sütunlarını aşağıdaki örneklerle karşılaştırın."
      >
        <div className="space-y-5">
          {error ? (
            <div role="alert">
              <InlineNotice tone="caution">{error.description} Seçiminizi buradan düzeltebilirsiniz.</InlineNotice>
            </div>
          ) : null}
          {candidates.length === 0 ? (
            <InlineNotice tone="caution">Kredi sütunu bulunamadı. Yeni bir PDF seçin.</InlineNotice>
          ) : (
            <>
              <div className="overflow-hidden rounded-xl border border-rule">
                <table className="w-full text-left text-sm">
                  <caption className="sr-only">Okunan sütunlar ve ilk derslerden örnek değerler</caption>
                  <thead className="bg-surface-muted text-muted">
                    <tr><th scope="col" className="px-3 py-2.5 font-medium">Sütun</th><th scope="col" className="px-3 py-2.5 font-medium">Örnek değerler</th></tr>
                  </thead>
                  <tbody className="divide-y divide-rule">
                    {candidates.map((candidate) => (
                      <tr key={candidate.id}>
                        <th scope="row" className="px-3 py-2.5 font-medium text-ink">{candidate.label}</th>
                        <td className="px-3 py-2.5 tabular-nums text-muted">{candidate.sampleValues.slice(0, 4).join(" · ") || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                {[
                  { id: "local-credit-column", label: "Kredi / Ulusal kredi", value: localCreditField, setValue: setLocalCreditField, other: ectsField },
                  { id: "ects-column", label: "AKTS / ECTS", value: ectsField, setValue: setEctsField, other: localCreditField },
                ].map((field) => (
                  <div key={field.id} className="min-w-0">
                    <label htmlFor={field.id} className="mb-2 block text-sm font-semibold text-ink">{field.label}</label>
                    <select id={field.id} value={field.value} disabled={isBusy}
                      onChange={(event) => field.setValue(event.target.value)}
                      className="min-h-11 w-full rounded-xl border border-rule bg-surface px-3 text-sm text-ink focus-visible:outline-2 focus-visible:outline-accent">
                      <option value="">Seçilmedi</option>
                      {candidates.map((candidate) => (
                        <option key={candidate.id} value={candidate.id} disabled={candidate.id === field.other}>{candidate.label}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
              <p className="text-sm leading-6 text-muted">En az bir alan seçin. PDF’de bulunmayan alanı boş bırakın. T ve U ders saatlerini, Puan ise not puanını gösterir; kredi için bu alanları seçmeyin.</p>
              {duplicate ? <InlineNotice tone="caution">Kredi ve AKTS için farklı sütunlar seçin.</InlineNotice> : null}
            </>
          )}
        </div>
      </Section>
      <div className="flex flex-col gap-3 sm:flex-row">
        <PrimaryButton type="button" disabled={!canContinue} onClick={() => {
          if (canContinue) void submitManualMapping(localCreditField || null, ectsField || null);
        }}>{isBusy ? "Hazırlanıyor…" : "Devam Et"}</PrimaryButton>
        <GhostButton type="button" disabled={isBusy} onClick={resetTranscript}>Yeni PDF Seç</GhostButton>
      </div>
    </TranscriptValidationFrame>
  );
}
