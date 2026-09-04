"use client";

import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { FutureProcess } from "@/components/academic-loading";
import { RequireReady } from "@/components/RequireReady";
import {
  ContentFrame,
  EmptyState,
  FormField,
  InfoNote,
  InlineNotice,
  OutcomeHero,
  PageHeader,
  PrimaryButton,
  QuietDangerButton,
  ResultSurface,
  Reveal,
  SecondaryButton,
  SupportStat,
  WeightingChip,
  controlClass,
} from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { LETTER_GRADES } from "@/lib/grades";
import { formatGpa, weightUnitLabel } from "@/lib/display";

const COMMON_WEIGHTS = Array.from({ length: 10 }, (_, index) =>
  String(index + 1),
);

export default function FutureSemesterPage() {
  const {
    weightingMode,
    futureCourses,
    futureSemesterResult,
    futureSemesterLoading,
    futureSemesterError,
    addFutureCourse,
    updateFutureCourse,
    removeFutureCourse,
    requestFutureSemester,
  } = useAppState();
  const [customWeightRows, setCustomWeightRows] = useState<Set<string>>(
    () => new Set(),
  );

  const weightLabel = weightUnitLabel(weightingMode);
  const unit = weightLabel.toLowerCase();
  const filled = futureCourses.some(
    (row) => row.name.trim() !== "" && row.gpaCredit.trim() !== "",
  );

  return (
    <AppShell>
      <RequireReady>
        <ContentFrame width="dashboard">
          <PageHeader
            title="Gelecek Dönem"
            description="Önümüzdeki dönem notların nasıl olursa GANO’n nasıl değişir?"
            aside={<WeightingChip mode={weightingMode} />}
          />
          <InfoNote>Bu alan yeni dönem derslerini planlamak içindir.</InfoNote>

          <div className="grid min-w-0 gap-4 lg:grid-cols-[minmax(0,1fr)_22rem] lg:items-start">
          <section>
            <div className="flex flex-wrap items-end justify-between gap-3">
              <h2 className="font-display text-[1.08rem] font-semibold tracking-[-0.02em] text-ink md:text-lg">
                Planlanan dersler
              </h2>
            </div>

            <div className="mt-4 overflow-hidden rounded-[14px] border border-rule/80 bg-surface/90 shadow-[var(--shadow-sm)]">
              <div className="hidden grid-cols-[minmax(12rem,1fr)_8.75rem_9.5rem_2.75rem] gap-3 border-b border-rule/80 px-4 py-2.5 text-[11px] font-medium uppercase tracking-[0.06em] text-faint md:grid">
                <span>Ders</span>
                <span>{weightLabel}</span>
                <span>Beklenen not</span>
                <span />
              </div>

              <div className="divide-y divide-rule/80">
                {futureCourses.map((row) => {
                  const usesCustomWeight =
                    customWeightRows.has(row.id) ||
                    (row.gpaCredit !== "" &&
                      !COMMON_WEIGHTS.includes(row.gpaCredit));
                  return (
                    <div
                      key={row.id}
                      className="grid gap-3 px-3 py-3 gp-enter md:grid-cols-[minmax(12rem,1fr)_8.75rem_9.5rem_2.75rem] md:items-end md:px-4"
                    >
                      <FormField
                        label="Ders"
                        labelClassName="text-xs text-faint md:sr-only"
                      >
                        <input
                          value={row.name}
                          onChange={(event) =>
                            updateFutureCourse(row.id, {
                              name: event.target.value,
                            })
                          }
                          placeholder="Ders kodu veya adı"
                          className={controlClass}
                        />
                      </FormField>
                      <div className="grid grid-cols-2 gap-2 md:contents">
                        <FormField
                          label={weightLabel}
                          labelClassName="text-xs text-faint md:sr-only"
                        >
                          <select
                            value={
                              usesCustomWeight
                                ? "other"
                                : COMMON_WEIGHTS.includes(row.gpaCredit)
                                  ? row.gpaCredit
                                  : ""
                            }
                            onChange={(event) => {
                              const value = event.target.value;
                              setCustomWeightRows((current) => {
                                const next = new Set(current);
                                if (value === "other") {
                                  next.add(row.id);
                                } else {
                                  next.delete(row.id);
                                }
                                return next;
                              });
                              updateFutureCourse(row.id, {
                                gpaCredit: value === "other" ? "" : value,
                              });
                            }}
                            className={`${controlClass} tabular-nums`}
                            aria-label={`${weightLabel} seç`}
                          >
                            <option value="" disabled>
                              Seç
                            </option>
                            {COMMON_WEIGHTS.map((weight) => (
                              <option key={weight} value={weight}>
                                {weight}
                              </option>
                            ))}
                            <option value="other">Diğer…</option>
                          </select>
                          {usesCustomWeight ? (
                            <input
                              type="number"
                              min={0.01}
                              step="any"
                              inputMode="decimal"
                              value={row.gpaCredit}
                              onChange={(event) =>
                                updateFutureCourse(row.id, {
                                  gpaCredit: event.target.value,
                                })
                              }
                              placeholder="Özel değer"
                              aria-label={`Özel ${weightLabel.toLocaleLowerCase("tr")} değeri`}
                              className={`${controlClass} mt-2 tabular-nums`}
                            />
                          ) : null}
                        </FormField>
                        <FormField
                          label="Beklenen not"
                          labelClassName="text-xs text-faint md:sr-only"
                        >
                          <select
                            value={row.grade}
                            onChange={(event) =>
                              updateFutureCourse(row.id, {
                                grade: event.target.value,
                              })
                            }
                            className={controlClass}
                          >
                            {LETTER_GRADES.map((grade) => (
                              <option key={grade} value={grade}>
                                {grade}
                              </option>
                            ))}
                          </select>
                        </FormField>
                      </div>
                      <QuietDangerButton
                        type="button"
                        onClick={() => {
                          setCustomWeightRows((current) => {
                            const next = new Set(current);
                            next.delete(row.id);
                            return next;
                          });
                          removeFutureCourse(row.id);
                        }}
                        className="h-9 w-auto justify-self-start px-2 text-xs md:h-10 md:justify-self-center md:px-2"
                        aria-label="Satırı kaldır"
                      >
                        <span className="md:hidden">Kaldır</span>
                        <TrashIcon />
                      </QuietDangerButton>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              <SecondaryButton type="button" onClick={addFutureCourse}>
                <PlusIcon />
                Ders ekle
              </SecondaryButton>
              <PrimaryButton
                type="button"
                disabled={futureSemesterLoading}
                onClick={() => void requestFutureSemester()}
              >
                {futureSemesterLoading
                  ? "Hesaplanıyor"
                  : "Simülasyonu Hesapla →"}
              </PrimaryButton>
            </div>
          </section>

          <div className="space-y-3 lg:sticky lg:top-4">
          {futureSemesterError ? (
            <InlineNotice tone="error">{futureSemesterError}</InlineNotice>
          ) : null}

          {futureSemesterLoading ? (
            <FutureProcess
              rowCount={
                futureCourses.filter((row) => row.name.trim() !== "").length
              }
            />
          ) : null}

          {!filled && !futureSemesterResult && !futureSemesterLoading ? (
            <EmptyState title="Ders ekleyip simülasyonu hesapla." />
          ) : null}

          {futureSemesterResult && !futureSemesterLoading ? (
            <Reveal>
              <ResultSurface tone="ok">
                <OutcomeHero
                  label="Tahmini yeni GANO"
                  value={formatGpa(futureSemesterResult.projectedCgpa)}
                  supporting={
                    <>
                      <SupportStat
                        label="Mevcut"
                        value={formatGpa(futureSemesterResult.currentGpa)}
                      />
                      <SupportStat
                        label="Dönem ort."
                        value={formatGpa(futureSemesterResult.futureSemesterGpa)}
                      />
                    </>
                  }
                />
                <p className="mt-3 text-xs text-muted">
                  Mevcut ağırlık {futureSemesterResult.currentGpaWeight} ·
                  Planlanan {futureSemesterResult.futureGpaWeight} · Yeni toplam{" "}
                  {futureSemesterResult.projectedTotalWeight} {unit}
                </p>
              </ResultSurface>
            </Reveal>
          ) : null}
          </div>
          </div>
        </ContentFrame>
      </RequireReady>
    </AppShell>
  );
}

function PlusIcon() {
  return (
    <svg aria-hidden width="15" height="15" viewBox="0 0 20 20" fill="none">
      <path
        d="M10 4v12M4 10h12"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg
      aria-hidden
      width="15"
      height="15"
      viewBox="0 0 20 20"
      fill="none"
      className="hidden md:block"
    >
      <path
        d="M4.5 6h11M8 6V4.5h4V6M6.5 6v9.5h7V6"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
