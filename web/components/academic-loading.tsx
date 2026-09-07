"use client";

import type { ReactNode } from "react";

import { cx, formatGpa } from "@/lib/display";

export function AcademicSkeleton({ className }: { className?: string }) {
  return (
    <div className={cx("gp-skeleton rounded-lg", className)} aria-hidden />
  );
}

export function AcademicProcessCard({
  label,
  phrases,
  children,
  skeleton,
  className,
  embedded = false,
}: {
  label?: string;
  phrases?: readonly string[];
  children: ReactNode;
  skeleton?: ReactNode;
  className?: string;
  embedded?: boolean;
}) {
  return (
    <div
      className={cx(
        embedded
          ? "w-full"
          : "mx-auto w-full max-w-md rounded-[14px] bg-surface/90 p-4 shadow-[var(--shadow-sm)] md:p-5",
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <div className="flex justify-center">{children}</div>
      <div className="relative mt-3 min-h-10 text-center sm:min-h-5">
        {phrases && phrases.length > 0 ? (
          <RotatingPhrases phrases={phrases} />
        ) : (
          <p className="text-sm font-medium text-ink">{label}</p>
        )}
      </div>
      {skeleton ? <div className="mt-4 space-y-2">{skeleton}</div> : null}
    </div>
  );
}

function RotatingPhrases({ phrases }: { phrases: readonly string[] }) {
  return (
    <p className="gp-load-phrases text-sm font-medium text-ink">
      {phrases.map((phrase, index) => (
        <span
          key={phrase}
          className="gp-load-phrase"
          style={{ animationDelay: `${index * (9 / phrases.length)}s` }}
        >
          {phrase}
        </span>
      ))}
    </p>
  );
}

export function AcademicLoader({
  variant,
  currentGpa,
  targetGpa,
  courseCode,
  currentGrade,
  rowCount = 3,
}: {
  variant:
    | "transcript"
    | "planner"
    | "manual"
    | "future"
    | "target"
    | "impact";
  currentGpa?: number | null;
  targetGpa?: number | null;
  courseCode?: string;
  currentGrade?: string;
  rowCount?: number;
}) {
  if (variant === "transcript") return <TranscriptVisual />;
  if (variant === "planner") {
    return <PlannerVisual currentGpa={currentGpa} targetGpa={targetGpa} />;
  }
  if (variant === "manual") return <ManualVisual currentGpa={currentGpa} />;
  if (variant === "future") return <FutureVisual rows={rowCount} />;
  if (variant === "target") {
    return <TargetVisual currentGpa={currentGpa} targetGpa={targetGpa} />;
  }
  return (
    <ImpactVisual courseCode={courseCode} currentGrade={currentGrade} />
  );
}

export function TranscriptProcess() {
  return (
    <AcademicProcessCard
      label="Transkript hazırlanıyor…"
      skeleton={
        <>
          <div className="grid grid-cols-3 gap-2">
            <AcademicSkeleton className="h-12" />
            <AcademicSkeleton className="h-12" />
            <AcademicSkeleton className="h-12" />
          </div>
          <AcademicSkeleton className="h-20" />
          <AcademicSkeleton className="h-8" />
          <AcademicSkeleton className="h-8" />
        </>
      }
    >
      <AcademicLoader variant="transcript" />
    </AcademicProcessCard>
  );
}

export function PlannerProcess({
  currentGpa,
  targetGpa,
}: {
  currentGpa?: number | null;
  targetGpa?: number | null;
}) {
  return (
    <AcademicProcessCard
      label="Plan hazırlanıyor"
      skeleton={
        <div className="grid grid-cols-3 gap-2">
          <AcademicSkeleton className="h-12" />
          <AcademicSkeleton className="h-12" />
          <AcademicSkeleton className="h-12" />
        </div>
      }
    >
      <AcademicLoader
        variant="planner"
        currentGpa={currentGpa}
        targetGpa={targetGpa}
      />
    </AcademicProcessCard>
  );
}

export function ManualProcess({ currentGpa }: { currentGpa?: number | null }) {
  return (
    <AcademicProcessCard label="Sonuç hesaplanıyor">
      <AcademicLoader variant="manual" currentGpa={currentGpa} />
    </AcademicProcessCard>
  );
}

export function FutureProcess({ rowCount }: { rowCount?: number }) {
  return (
    <AcademicProcessCard
      label="Simülasyon hesaplanıyor"
      skeleton={<AcademicSkeleton className="h-24" />}
    >
      <AcademicLoader variant="future" rowCount={rowCount} />
    </AcademicProcessCard>
  );
}

export function TargetProcess({
  currentGpa,
  targetGpa,
}: {
  currentGpa?: number | null;
  targetGpa?: number | null;
}) {
  return (
    <AcademicProcessCard
      label="Gerekli ortalama hesaplanıyor"
      skeleton={<AcademicSkeleton className="h-28" />}
    >
      <AcademicLoader
        variant="target"
        currentGpa={currentGpa}
        targetGpa={targetGpa}
      />
    </AcademicProcessCard>
  );
}

export function ImpactProcess({
  courseCode,
  currentGrade,
}: {
  courseCode?: string;
  currentGrade?: string;
}) {
  return (
    <AcademicProcessCard label="Etki hesaplanıyor" embedded>
      <AcademicLoader
        variant="impact"
        courseCode={courseCode}
        currentGrade={currentGrade}
      />
    </AcademicProcessCard>
  );
}

function gpaLabel(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : formatGpa(value);
}

function TranscriptVisual() {
  return (
    <div className="w-full max-w-[16rem]" aria-hidden>
      <div className="gp-load-doc rounded-[10px] border border-rule/80 bg-bg/60 p-3">
        <div className="mb-2 h-1.5 w-16 rounded-full bg-info/35" />
        <div className="space-y-1.5">
          {["AA", "BA", "BB"].map((grade, index) => (
            <div
              key={grade}
              className="gp-load-row flex items-center justify-between gap-2"
              style={{ animationDelay: `${0.35 + index * 0.28}s` }}
            >
              <span className="h-1.5 w-20 rounded-full bg-surface-muted" />
              <span className="gp-load-chip rounded-md bg-info-soft px-1.5 py-0.5 text-[10px] font-semibold text-info">
                {grade}
              </span>
            </div>
          ))}
        </div>
        <div className="gp-load-groups mt-3 flex gap-1.5">
          <span className="h-6 flex-1 rounded-md bg-info-soft/80" />
          <span className="h-6 flex-1 rounded-md bg-accent-soft/70" />
          <span className="h-6 flex-1 rounded-md bg-surface-muted" />
        </div>
        <svg
          className="gp-load-trend mt-3 block h-8 w-full text-info"
          viewBox="0 0 120 24"
          fill="none"
        >
          <path
            className="gp-load-trend-line"
            d="M4 18 L28 14 L52 16 L76 9 L108 6"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            pathLength="1"
          />
          <circle className="gp-load-trend-dot" cx="108" cy="6" r="2.2" fill="currentColor" />
        </svg>
      </div>
    </div>
  );
}

function PlannerVisual({
  currentGpa,
  targetGpa,
}: {
  currentGpa?: number | null;
  targetGpa?: number | null;
}) {
  return (
    <div className="w-full max-w-[18rem]" aria-hidden>
      <div className="flex items-center gap-2 font-display text-sm font-semibold tabular-nums text-ink">
        <span>{gpaLabel(currentGpa)}</span>
        <span className="relative h-px flex-1 bg-rule">
          <span className="gp-load-marker absolute top-1/2 size-2 -translate-y-1/2 rounded-full bg-info" />
        </span>
        <span>{gpaLabel(targetGpa)}</span>
      </div>
      <div className="mt-3 flex justify-center gap-2">
        <span className="gp-load-chip rounded-md bg-caution-soft px-1.5 py-0.5 text-[10px] font-semibold text-caution">
          DC → BB
        </span>
        <span
          className="gp-load-chip rounded-md bg-info-soft px-1.5 py-0.5 text-[10px] font-semibold text-info"
          style={{ animationDelay: "0.35s" }}
        >
          CC → BA
        </span>
      </div>
    </div>
  );
}

function ManualVisual({ currentGpa }: { currentGpa?: number | null }) {
  return (
    <p
      className="font-display text-2xl font-semibold tabular-nums tracking-tight text-ink"
      aria-hidden
    >
      {gpaLabel(currentGpa)}
      <span className="mx-2 text-faint">→</span>
      <span className="gp-load-ellipsis text-muted">···</span>
    </p>
  );
}

function FutureVisual({ rows }: { rows: number }) {
  const count = Math.min(3, Math.max(2, rows));
  return (
    <div className="w-full max-w-[14rem]" aria-hidden>
      <div className="space-y-1.5">
        {Array.from({ length: count }, (_, index) => (
          <div
            key={index}
            className="gp-load-row flex items-center justify-between rounded-md bg-surface-muted/70 px-2 py-1.5"
            style={{ animationDelay: `${index * 0.22}s` }}
          >
            <span className="h-1.5 w-16 rounded-full bg-rule" />
            <span className="h-4 w-7 rounded bg-info-soft" />
          </div>
        ))}
      </div>
      <p className="gp-load-sink mt-2 text-center text-[11px] font-medium uppercase tracking-[0.08em] text-faint">
        Gelecek Dönem
      </p>
    </div>
  );
}

function TargetVisual({
  currentGpa,
  targetGpa,
}: {
  currentGpa?: number | null;
  targetGpa?: number | null;
}) {
  return (
    <div className="w-full max-w-[16rem]" aria-hidden>
      <div className="flex justify-between text-[11px] uppercase tracking-[0.08em] text-faint">
        <span>Mevcut</span>
        <span>Hedef</span>
      </div>
      <div className="mt-1 flex items-end justify-between font-display text-lg font-semibold tabular-nums text-ink">
        <span>{gpaLabel(currentGpa)}</span>
        <span>{gpaLabel(targetGpa)}</span>
      </div>
      <div className="relative mt-3 h-1 rounded-full bg-rule">
        <span className="absolute inset-y-0 left-0 w-1/3 rounded-full bg-info/40" />
        <span className="gp-load-target absolute top-1/2 size-2.5 -translate-y-1/2 rounded-full bg-accent" />
      </div>
    </div>
  );
}

function ImpactVisual({
  courseCode,
  currentGrade,
}: {
  courseCode?: string;
  currentGrade?: string;
}) {
  return (
    <div className="w-full max-w-[12rem] text-center" aria-hidden>
      <p className="text-sm font-semibold tracking-wide text-ink">
        {courseCode ?? "Ders"}
      </p>
      <p className="mt-1 text-xs text-muted">
        {currentGrade ?? "—"}
        <span className="mx-1.5 text-faint">→</span>
        <span className="gp-load-ellipsis">?</span>
      </p>
      <div className="mt-3 flex justify-center gap-1">
        {["CC", "CB", "BB", "BA", "AA"].map((grade, index) => (
          <span
            key={grade}
            className="gp-load-chip rounded-md bg-info-soft px-1 py-0.5 text-[10px] font-semibold text-info"
            style={{ animationDelay: `${index * 0.14}s` }}
          >
            {grade}
          </span>
        ))}
      </div>
    </div>
  );
}
