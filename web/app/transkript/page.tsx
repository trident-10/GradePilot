"use client";

import { AppShell, EntryShell } from "@/components/AppShell";
import { MetricTile, Panel } from "@/components/dashboard";
import { CourseConfirmation } from "@/components/upload/CourseConfirmation";
import { CreditSelection } from "@/components/upload/CreditSelection";
import { ManualCreditMapping } from "@/components/upload/ManualCreditMapping";
import { UploadError } from "@/components/upload/UploadError";
import { UploadStart } from "@/components/upload/UploadStart";
import { UploadingState } from "@/components/upload/UploadingState";
import {
  ContentFrame,
  GhostButton,
  GradeBadge,
  PageHeader,
  SecondaryButton,
  WeightingChip,
} from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { formatGpa, weightUnitLabel } from "@/lib/display";

export default function TranscriptPage() {
  const { phase, isReady } = useAppState();

  if (!isReady) {
    return (
      <EntryShell>
        {phase === "empty" ? <UploadStart key="empty" /> : null}
        {phase === "uploading" ? <UploadingState key="uploading" /> : null}
        {phase === "manual_mapping" ? (
          <ManualCreditMapping key="manual_mapping" />
        ) : null}
        {phase === "credit_selection" ? (
          <CreditSelection key="credit_selection" />
        ) : null}
        {phase === "confirmation" ? (
          <CourseConfirmation key="confirmation" />
        ) : null}
        {phase === "error" ? <UploadError key="error" /> : null}
      </EntryShell>
    );
  }

  return (
    <AppShell>
      <TranscriptReady />
    </AppShell>
  );
}

function TranscriptReady() {
  const {
    academicSummary,
    summaryLoading,
    weightingMode,
    resetTranscript,
    activeCourses,
  } = useAppState();

  const gpa = academicSummary?.currentGpa ?? null;
  const weight = academicSummary?.totalGpaWeight ?? null;
  const active = academicSummary?.activeCourseCount ?? null;
  const semesters = academicSummary?.semesters.length ?? null;
  const preview = activeCourses.slice(0, 8);

  return (
    <ContentFrame width="medium" className="space-y-5">
      <PageHeader
        title="Transkript"
        description="Yüklü transkriptine ait özet."
        aside={<WeightingChip mode={weightingMode} />}
      />

      <div className="flex items-center gap-2 text-sm">
        <span className="size-1.5 rounded-full bg-ok" aria-hidden />
        <span className="font-medium text-ink">Transkript hazır</span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricTile
          strong
          label="GANO"
          value={summaryLoading ? "…" : gpa === null ? "—" : formatGpa(gpa)}
        />
        <MetricTile
          label={`Toplam ${weightUnitLabel(weightingMode)}`}
          value={summaryLoading ? "…" : weight === null ? "—" : weight}
        />
        <MetricTile
          label="Aktif ders"
          value={summaryLoading ? "…" : active === null ? "—" : active}
        />
        <MetricTile
          label="Dönem"
          value={summaryLoading ? "…" : semesters === null ? "—" : semesters}
        />
      </div>

      <div className="flex flex-wrap gap-3">
        <SecondaryButton type="button" onClick={resetTranscript}>
          Yeni transkript yükle
        </SecondaryButton>
        <GhostButton type="button" onClick={resetTranscript}>
          Transkripti sıfırla
        </GhostButton>
      </div>

      {preview.length > 0 ? (
        <Panel title="Onaylı ders önizlemesi" variant="table">
          <ul className="divide-y divide-rule/80">
            {preview.map((course) => (
              <li
                key={`${course.sourceOrder ?? "x"}-${course.code}`}
                className="flex items-center justify-between gap-3 px-4 py-2.5"
              >
                <div className="min-w-0">
                  <p className="font-semibold tracking-wide text-ink">
                    {course.code}
                  </p>
                  <p className="truncate text-xs text-faint">{course.name}</p>
                </div>
                <GradeBadge grade={course.grade} />
              </li>
            ))}
          </ul>
        </Panel>
      ) : null}
    </ContentFrame>
  );
}
