"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { AcademicSkeleton } from "@/components/academic-loading";
import { AppShell } from "@/components/AppShell";
import { DashboardLink, Panel } from "@/components/dashboard";
import { GpaSummary } from "@/components/GpaSummary";
import { RequireReady } from "@/components/RequireReady";
import { SemesterTrendChart } from "@/components/SemesterSummaryTable";
import {
  ContentFrame,
  GhostButton,
  GradeBadge,
  InlineNotice,
  PageHeader,
  Reveal,
  controlClass,
} from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { cx, formatGpa, weightUnitLabel } from "@/lib/display";
import { gradeBarClass } from "@/lib/gradeColors";
import { gpaPresentation } from "@/lib/gpaPresentation";
import {
  countActiveGrades,
  highestSemesterSummary,
} from "@/lib/gradeDistribution";

const PREVIEW_SIZE = 8;

export default function OverviewPage() {
  const {
    academicSummary,
    summaryLoading,
    summaryError,
    weightingMode,
    refreshAcademicSummary,
    activeCourses,
    transcript,
  } = useAppState();

  const derivedCgpa = academicSummary?.derivedCgpa ?? academicSummary?.currentGpa ?? null;
  const officialCgpa = academicSummary?.officialCgpa ?? transcript?.officialCgpa ?? null;
  const gano = gpaPresentation(officialCgpa, derivedCgpa);
  const totalGpaWeight = academicSummary?.totalGpaWeight ?? null;
  const activeCount = academicSummary?.activeCourseCount ?? null;
  const semesterCount = academicSummary
    ? academicSummary.semesters.length
    : null;
  const highest = academicSummary
    ? highestSemesterSummary(academicSummary.semesters)
    : null;
  const gradeCounts = useMemo(
    () => countActiveGrades(activeCourses),
    [activeCourses],
  );
  const maxGradeCount = Math.max(1, ...gradeCounts.map((row) => row.count));

  return (
    <AppShell>
      <RequireReady>
        <ContentFrame width="dashboard">
          <PageHeader
            title="Akademik Genel Bakış"
            description="Not ortalaman, ders dağılımın ve dönem performansın tek bakışta."
          />

          {summaryError ? (
            <InlineNotice tone="error">
              <p>{summaryError}</p>
              <GhostButton
                type="button"
                className="mt-2 h-auto px-0 text-danger hover:bg-transparent"
                onClick={() => void refreshAcademicSummary()}
              >
                Tekrar dene
              </GhostButton>
            </InlineNotice>
          ) : null}

          <Reveal>
            <GpaSummary
              derivedCgpa={derivedCgpa}
              officialCgpa={officialCgpa}
              totalGpaWeight={totalGpaWeight}
              activeCourses={activeCount}
              semesterCount={semesterCount}
              highestSemesterGpa={highest?.gpa ?? null}
              weightingMode={weightingMode}
              loading={summaryLoading}
            />
            {gano.hasDiscrepancy && officialCgpa !== null && derivedCgpa !== null ? (
              <p className="mt-3 text-sm leading-relaxed text-muted">
                Transkriptteki resmî GANO ({formatGpa(officialCgpa)}) ile derslerden
                hesaplanan değer ({formatGpa(derivedCgpa)}) belirgin şekilde farklı.
                Ana kartta resmî GANO gösterilir; planlar ve senaryolar ders verileriyle
                hesaplanır — not veya krediler otomatik değiştirilmez.
              </p>
            ) : null}
          </Reveal>

          <div className="grid items-stretch gap-4 sm:gap-5 xl:grid-cols-2">
            <Panel title="Not dağılımı" variant="analytics">
              {activeCourses.length === 0 ? (
                <p className="text-sm text-muted">Aktif ders notu yok.</p>
              ) : (
                <ul className="space-y-2" aria-label="Aktif ders not dağılımı">
                  {gradeCounts.map((row) => (
                    <li
                      key={row.grade}
                      className="grid grid-cols-[2.75rem_1fr_1.75rem] items-center gap-2.5"
                    >
                      <GradeBadge grade={row.grade} />
                      <div className="h-2.5 overflow-hidden rounded-full bg-surface-muted">
                        <div
                          className={cx(
                            "h-full rounded-full",
                            gradeBarClass(row.grade),
                          )}
                          style={{
                            width: `${(row.count / maxGradeCount) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-right text-xs font-medium tabular-nums text-ink">
                        {row.count}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>

            <Panel title="Dönem not ortalamaları (DNO)" variant="analytics">
              {summaryLoading ? (
                <AcademicSkeleton className="h-40" />
              ) : !academicSummary || academicSummary.semesters.length === 0 ? (
                <p className="text-sm text-muted">Gösterilecek dönem verisi yok.</p>
              ) : (
                <SemesterTrendChart semesters={academicSummary.semesters} />
              )}
            </Panel>
          </div>

          <div className="grid items-stretch gap-4 sm:gap-5 xl:grid-cols-[minmax(0,1fr)_18.5rem]">
            <CoursePreview
              weightLabel={weightUnitLabel(weightingMode)}
            />
            <Panel title="Hızlı planlama" variant="action" className="xl:sticky xl:top-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-muted">
                Planlamada kullanılan GANO
              </p>
              <p className="mt-2 font-display text-[2rem] font-semibold leading-none tabular-nums tracking-[-0.04em] text-ink">
                {derivedCgpa === null ? "—" : formatGpa(derivedCgpa)}
              </p>
              <p className="mt-2 text-xs leading-5 text-muted">Ders ve kredi verilerinden hesaplanır.</p>
              <div className="mt-4 divide-y divide-accent/20 border-t border-accent/15 pt-1">
                <DashboardLink href="/planlayici">
                  Plan oluştur
                </DashboardLink>
                <DashboardLink href="/planlayici?mode=manual">
                  Kendi planımı yap
                </DashboardLink>
                <DashboardLink href="/gelecek-donem">
                  Gelecek dönemi simüle et
                </DashboardLink>
                <DashboardLink href="/hedef-gano">
                  Hedef GANO hesapla
                </DashboardLink>
              </div>
            </Panel>
          </div>
        </ContentFrame>
      </RequireReady>
    </AppShell>
  );
}

function CoursePreview({ weightLabel }: { weightLabel: string }) {
  const { activeCourses } = useAppState();
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return activeCourses;
    return activeCourses.filter(
      (course) =>
        course.code.toLowerCase().includes(q) ||
        course.name.toLowerCase().includes(q),
    );
  }, [activeCourses, query]);
  const rows = filtered.slice(0, PREVIEW_SIZE);

  return (
    <Panel
      title="Aktif dersler"
      variant="table"
      action={
        <Link
          href="/dersler"
          className="text-sm font-medium text-info underline-offset-2 hover:text-accent-deep hover:underline"
        >
          Tüm dersleri gör
        </Link>
      }
    >
      <div className="px-4 pb-3">
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ders ara…"
          className={cx(controlClass, "h-11 sm:h-9")}
          aria-label="Ders ara"
        />
      </div>
      {rows.length === 0 ? (
        <p className="px-4 pb-4 text-sm text-muted">Eşleşen ders yok.</p>
      ) : (
        <>
          <div className="hidden overflow-x-auto md:block">
            <table className="w-full min-w-[420px] border-collapse text-sm">
              <thead>
                <tr className="border-y border-rule/80 text-left text-[11px] uppercase tracking-[0.06em] text-faint">
                  <th className="px-4 py-2 font-medium">Ders</th>
                  <th className="px-3 py-2 font-medium">Not</th>
                  <th className="px-3 py-2 font-medium">{weightLabel}</th>
                  <th className="px-3 py-2 font-medium">Dönem</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((course) => (
                  <tr
                    key={`${course.sourceOrder ?? "x"}-${course.code}`}
                    className="border-b border-rule/70 last:border-b-0"
                  >
                    <td className="px-4 py-2">
                      <p className="font-semibold tracking-wide text-ink">
                        {course.code}
                      </p>
                      <p className="truncate text-xs text-faint">{course.name}</p>
                    </td>
                    <td className="px-3 py-2">
                      <GradeBadge grade={course.grade} />
                    </td>
                    <td className="px-3 py-2 tabular-nums text-muted">
                      {course.gpaCredit}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-muted">
                      {course.semester ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ul className="divide-y divide-rule/80 px-4 pb-3 md:hidden">
            {rows.map((course) => (
              <li
                key={`${course.sourceOrder ?? "x"}-${course.code}`}
                className="flex items-center justify-between gap-3 py-2.5"
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
        </>
      )}
    </Panel>
  );
}
