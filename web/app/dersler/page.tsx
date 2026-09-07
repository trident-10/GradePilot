"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { ImpactProcess } from "@/components/academic-loading";
import { RequireReady } from "@/components/RequireReady";
import {
  ContentFrame,
  EmptyState,
  GradeBadge,
  GradeShift,
  InlineNotice,
  OutcomeHero,
  PageHeader,
  ResultSurface,
  SecondaryButton,
  SupportStat,
  controlClass,
} from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import type { CourseImpact } from "@/lib/api/academic";
import { cx, formatGpa, weightUnitLabel } from "@/lib/display";
import { LETTER_GRADES } from "@/lib/grades";
import type { Course } from "@/lib/types";

export default function CoursesPage() {
  const {
    activeCourses,
    historicalCourses,
    selectedImpactCourse,
    courseImpactResult,
    courseImpactLoading,
    courseImpactError,
    requestCourseImpact,
    clearCourseImpact,
    weightingMode,
  } = useAppState();

  const weightLabel = weightUnitLabel(weightingMode);
  const [query, setQuery] = useState("");
  const [semesterFilter, setSemesterFilter] = useState("all");
  const [gradeFilter, setGradeFilter] = useState("all");
  const [sortKey, setSortKey] = useState<"code" | "grade" | "semester">("code");
  const [pageSize, setPageSize] = useState<10 | 20 | "all">(10);
  const impactRef = useRef<HTMLDivElement>(null);

  // The course list can be long, so bring the analysis panel into view.
  useEffect(() => {
    if (!selectedImpactCourse) return;
    const node = impactRef.current;
    if (!node) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)")
      .matches;
    node.scrollIntoView({
      behavior: reduced ? "auto" : "smooth",
      block: "nearest",
    });
  }, [selectedImpactCourse]);

  const semesters = useMemo(() => {
    const values = new Set<string>();
    for (const course of activeCourses) {
      if (course.semester) values.add(course.semester);
    }
    return [...values];
  }, [activeCourses]);

  const filteredActive = useMemo(() => {
    const q = query.trim().toLowerCase();
    const rows = activeCourses.filter((course) => {
      if (semesterFilter !== "all" && course.semester !== semesterFilter) {
        return false;
      }
      if (gradeFilter !== "all" && course.grade !== gradeFilter) {
        return false;
      }
      if (!q) return true;
      return (
        course.code.toLowerCase().includes(q) ||
        course.name.toLowerCase().includes(q)
      );
    });
    const gradeRank = (grade: string) => {
      const index = LETTER_GRADES.indexOf(
        grade as (typeof LETTER_GRADES)[number],
      );
      return index === -1 ? LETTER_GRADES.length : index;
    };
    return [...rows].sort((a, b) => {
      if (sortKey === "grade") return gradeRank(a.grade) - gradeRank(b.grade);
      if (sortKey === "semester") {
        return (a.semester ?? "").localeCompare(b.semester ?? "", "tr");
      }
      return a.code.localeCompare(b.code, "tr");
    });
  }, [activeCourses, gradeFilter, query, semesterFilter, sortKey]);

  const visibleActive =
    pageSize === "all" ? filteredActive : filteredActive.slice(0, pageSize);
  const hasMoreCourses =
    pageSize !== "all" && pageSize < filteredActive.length;

  function resetBrowsing() {
    if (selectedImpactCourse) clearCourseImpact();
  }

  return (
    <AppShell>
      <RequireReady>
        <ContentFrame width="dashboard">
          <PageHeader
            title="Dersler"
            description="Aktif derslerini incele; bir notun GANO etkisini gör."
            aside={
              <p className="text-sm text-muted">
                <span className="font-semibold tabular-nums text-ink">
                  {activeCourses.length}
                </span>{" "}
                aktif ders
              </p>
            }
          />

          <div className="xl:grid xl:grid-cols-[minmax(0,1fr)_22rem] xl:items-start xl:gap-4">
            <div className="space-y-4">
          <div className="flex flex-col gap-2 rounded-[14px] bg-surface/85 p-2.5 shadow-[var(--shadow-sm)] md:flex-row md:items-center">
            <div className="relative min-w-0 flex-1">
              <SearchIcon />
              <input
                type="search"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  resetBrowsing();
                }}
                placeholder="Ders ara…"
                className={cx(controlClass, "pl-9")}
                aria-label="Ders ara"
              />
            </div>
            <select
              value={semesterFilter}
              onChange={(event) => {
                setSemesterFilter(event.target.value);
                resetBrowsing();
              }}
              className={cx(controlClass, "md:w-52")}
              aria-label="Dönem filtresi"
            >
              <option value="all">Tüm dönemler</option>
              {semesters.map((semester) => (
                <option key={semester} value={semester}>
                  {semester}
                </option>
              ))}
            </select>
            <select
              value={gradeFilter}
              onChange={(event) => {
                setGradeFilter(event.target.value);
                resetBrowsing();
              }}
              className={cx(controlClass, "md:w-40")}
              aria-label="Not filtresi"
            >
              <option value="all">Tüm notlar</option>
              {LETTER_GRADES.filter((grade) =>
                activeCourses.some((course) => course.grade === grade),
              ).map((grade) => (
                <option key={grade} value={grade}>
                  {grade}
                </option>
              ))}
            </select>
            <select
              value={sortKey}
              onChange={(event) =>
                setSortKey(event.target.value as "code" | "grade" | "semester")
              }
              className={cx(controlClass, "md:w-36")}
              aria-label="Sıralama"
            >
              <option value="code">Koda göre</option>
              <option value="grade">Nota göre</option>
              <option value="semester">Döneme göre</option>
            </select>
          </div>

          {activeCourses.length === 0 ? (
            <EmptyState title="Henüz aktif ders verisi yok." />
          ) : filteredActive.length === 0 ? (
            <EmptyState title="Aramanla eşleşen aktif ders yok." />
          ) : (
            <>
              <div className="hidden overflow-x-auto rounded-[14px] bg-surface/90 shadow-[var(--shadow-sm)] md:block">
                <CourseTable
                  courses={visibleActive}
                  weightLabel={weightLabel}
                  selectedCode={selectedImpactCourse}
                  onImpact={(code) => {
                    if (selectedImpactCourse === code) {
                      clearCourseImpact();
                      return;
                    }
                    void requestCourseImpact(code);
                  }}
                />
              </div>
              <div className="space-y-2 md:hidden">
                {visibleActive.map((course) => {
                  const selected = selectedImpactCourse === course.code;
                  return (
                    <article
                      key={`${course.sourceOrder ?? "x"}-${course.code}`}
                      className={cx(
                        "border-b border-rule/80 py-3 gp-enter last:border-b-0",
                        selected && "-mx-2 rounded-[10px] bg-accent-soft/50 px-2",
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="font-semibold tracking-wide text-ink">
                            {course.code}
                          </p>
                          <p className="mt-0.5 truncate text-xs text-faint">
                            {course.name}
                          </p>
                        </div>
                        <GradeBadge grade={course.grade} />
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
                        <span>
                          {course.gpaCredit} {weightLabel}
                        </span>
                        <span>{course.semester ?? "—"}</span>
                        <button
                          type="button"
                          onClick={() => {
                            if (selected) {
                              clearCourseImpact();
                              return;
                            }
                            void requestCourseImpact(course.code);
                          }}
                          className="ml-auto text-sm font-medium text-info underline-offset-2 transition-colors hover:text-accent-deep hover:underline"
                        >
                          {selected ? "Kapat" : "Etkiyi Gör"}
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs tabular-nums text-faint">
                  {visibleActive.length} / {filteredActive.length} ders
                </p>
                <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto">
                  <select
                    value={pageSize === "all" ? "all" : String(pageSize)}
                    onChange={(event) => {
                      const value = event.target.value;
                      setPageSize(
                        value === "all" ? "all" : (Number(value) as 10 | 20),
                      );
                    }}
                    className={cx(
                      controlClass,
                      "h-11 w-full sm:h-9 sm:w-[7.5rem]",
                    )}
                    aria-label="Gösterilecek ders sayısı"
                  >
                    <option value="10">10</option>
                    <option value="20">20</option>
                    <option value="all">Tümü</option>
                  </select>
                  {hasMoreCourses ? (
                    <SecondaryButton
                      type="button"
                      className="w-full sm:w-auto"
                      onClick={() =>
                        setPageSize((size) => (size === 10 ? 20 : "all"))
                      }
                    >
                      Daha fazla göster
                    </SecondaryButton>
                  ) : null}
                </div>
              </div>
            </>
          )}
            </div>

            <div ref={impactRef} className="mt-4 xl:mt-0 xl:sticky xl:top-4">
              {selectedImpactCourse ? (
                <ImpactPanel
                  course={activeCourses.find(
                    (row) => row.code === selectedImpactCourse,
                  )}
                  loading={courseImpactLoading}
                  error={courseImpactError}
                  result={courseImpactResult}
                />
              ) : (
                <div className="hidden rounded-[14px] bg-surface/60 px-4 py-6 text-sm text-muted xl:block">
                  Bir ders seçip etkisini gör.
                </div>
              )}
            </div>
          </div>

          {historicalCourses.length > 0 ? (
            <details className="rounded-[14px] bg-surface/70 px-4 py-3">
              <summary className="cursor-pointer text-sm font-medium text-muted">
                Geçmiş denemeler ({historicalCourses.length})
              </summary>
              <div className="mt-3 hidden overflow-x-auto md:block">
                <CourseTable
                  courses={historicalCourses}
                  weightLabel={weightLabel}
                  muted
                />
              </div>
              <div className="mt-2 space-y-2 md:hidden">
                {historicalCourses.map((course) => (
                  <article
                    key={`h-${course.sourceOrder ?? "x"}-${course.code}`}
                    className="border-b border-dashed border-rule/80 py-2.5 last:border-b-0"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium tracking-wide text-muted">
                          {course.code}
                        </p>
                        <p className="text-xs text-faint">{course.name}</p>
                      </div>
                      <GradeBadge grade={course.grade} />
                    </div>
                  </article>
                ))}
              </div>
            </details>
          ) : null}
        </ContentFrame>
      </RequireReady>
    </AppShell>
  );
}

function CourseTable({
  courses,
  weightLabel,
  selectedCode,
  onImpact,
  muted = false,
}: {
  courses: Course[];
  weightLabel: string;
  selectedCode?: string | null;
  onImpact?: (code: string) => void;
  muted?: boolean;
}) {
  return (
    <table className="w-full min-w-[460px] border-collapse text-sm">
      <thead>
        <tr className="border-b border-rule/80 text-left text-[11px] uppercase tracking-[0.06em] text-faint">
          <th className="px-3 py-2.5 font-medium lg:px-4">Ders</th>
          <th className="px-2 py-2.5 font-medium lg:px-4">Not</th>
          <th className="px-2 py-2.5 font-medium lg:px-4">{weightLabel}</th>
          <th className="px-2 py-2.5 font-medium lg:px-4">Dönem</th>
          {onImpact ? (
            <th className="px-3 py-2.5 font-medium lg:px-4">
              <span className="sr-only">Eylem</span>
            </th>
          ) : null}
        </tr>
      </thead>
      <tbody>
        {courses.map((course) => {
          const selected = selectedCode === course.code;
          return (
            <tr
              key={`${course.sourceOrder ?? "x"}-${course.code}-${course.semester ?? ""}`}
              className={cx(
                "border-b border-rule/70 transition-colors duration-[180ms] last:border-b-0",
                selected && "bg-accent-soft/45",
                !muted && !selected && "hover:bg-info-soft/30",
              )}
            >
              <td className="px-3 py-2.5 lg:px-4">
                <p
                  className={cx(
                    "font-semibold tracking-wide",
                    muted ? "text-muted" : "text-ink",
                  )}
                >
                  {course.code}
                </p>
                <p className="mt-0.5 text-xs text-faint">{course.name}</p>
              </td>
              <td className="px-2 py-2.5 lg:px-4">
                <GradeBadge grade={course.grade} />
              </td>
              <td className="px-2 py-2.5 tabular-nums text-muted lg:px-4">
                {course.gpaCredit}
              </td>
              <td className="whitespace-nowrap px-2 py-2.5 text-muted lg:px-4">
                {course.semester ?? "—"}
              </td>
              {onImpact ? (
                <td className="px-3 py-2.5 text-right lg:px-4">
                  <button
                    type="button"
                    onClick={() => onImpact(course.code)}
                    className="whitespace-nowrap rounded-[8px] px-2 py-1 text-sm font-medium text-muted underline-offset-2 transition-colors hover:bg-accent-soft/60 hover:text-accent-deep hover:underline"
                  >
                    {selected ? "Kapat" : "Etkiyi Gör"}
                  </button>
                </td>
              ) : null}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function ImpactPanel({
  course,
  loading,
  error,
  result,
}: {
  course?: Course;
  loading: boolean;
  error: string | null;
  result: CourseImpact | null;
}) {
  const code = result?.course.code ?? course?.code;
  const name = result?.course.name ?? course?.name;
  const currentGrade = result?.course.currentGrade ?? course?.grade;
  const bestOption =
    result?.options.reduce<CourseImpact["options"][number] | null>(
      (best, option) =>
        !best || option.projectedGpa > best.projectedGpa ? option : best,
      null,
    ) ?? null;

  return (
    <ResultSurface tone="info">
      {code ? (
        <div className="border-b border-info/15 pb-4">
          <p className="font-display text-xl font-semibold tracking-[-0.03em] text-ink md:text-2xl">
            {code}
          </p>
          {name ? <p className="mt-1 text-sm text-muted">{name}</p> : null}
          {currentGrade ? (
            <p className="mt-2 flex flex-wrap items-center gap-2 text-sm">
              <GradeBadge grade={currentGrade} />
              {bestOption ? (
                <>
                  <span className="text-faint" aria-hidden>
                    →
                  </span>
                  <GradeBadge grade={bestOption.grade} />
                  <span className="text-xs text-info">potansiyeli</span>
                </>
              ) : null}
            </p>
          ) : null}
        </div>
      ) : (
        <h2 className="font-display text-lg font-semibold tracking-tight text-ink">
          Ders etkisi
        </h2>
      )}

      <div className="mt-4">
        {loading ? (
          <ImpactProcess courseCode={code} currentGrade={currentGrade} />
        ) : null}
        {error ? <InlineNotice tone="error">{error}</InlineNotice> : null}

        {result && !loading ? (
          result.options.length === 0 ? (
            <p className="text-sm leading-6 text-ink">
              Bu ders zaten en yüksek notta.
            </p>
          ) : (
            <div>
              <OutcomeHero
                label="Mevcut GANO"
                value={formatGpa(result.currentGpa)}
                supporting={
                  bestOption ? (
                    <SupportStat
                      label={`${bestOption.grade} ile`}
                      value={formatGpa(bestOption.projectedGpa)}
                    />
                  ) : null
                }
              />
              <ul className="mt-5 divide-y divide-info/15">
                {result.options.map((row) => (
                  <li
                    key={row.grade}
                    className="flex items-center justify-between gap-3 py-2.5"
                  >
                    <GradeShift
                      from={currentGrade ?? "—"}
                      to={row.grade}
                      delta={row.gpaGain}
                    />
                    <p className="font-display text-lg font-semibold tabular-nums tracking-tight text-ink">
                      {formatGpa(row.projectedGpa)}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )
        ) : null}
      </div>
    </ResultSurface>
  );
}

function SearchIcon() {
  return (
    <svg
      aria-hidden
      width="16"
      height="16"
      viewBox="0 0 20 20"
      fill="none"
      className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint"
    >
      <circle cx="8.5" cy="8.5" r="5.25" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="m12.5 12.5 4 4"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}
