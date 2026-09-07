"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";

import { AppShell } from "@/components/AppShell";
import { PlannerProcess, ManualProcess } from "@/components/academic-loading";
import { MetricTile } from "@/components/dashboard";
import { RequireReady } from "@/components/RequireReady";
import {
  ContentFrame,
  DomainStatus,
  EmptyState,
  FormField,
  GradeBadge,
  GradeShift,
  InlineNotice,
  OutcomeHero,
  PageHeader,
  PrimaryButton,
  QuietDangerButton,
  ResultSurface,
  Reveal,
  SecondaryButton,
  Section,
  SupportStat,
  controlClass,
} from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import type { ManualScenario, TargetPlan } from "@/lib/api/academic";
import { cx, formatGpa, formatSigned } from "@/lib/display";
import { LETTER_GRADES } from "@/lib/grades";
import { PLANNER_STRATEGIES, type PlannerStrategyId } from "@/lib/planner";

function parseTargetGpa(value: string): number | null {
  const trimmed = value.trim().replace(",", ".");
  if (trimmed === "") return null;
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed)) return null;
  if (parsed < 0 || parsed > 4) return null;
  return parsed;
}

function subscribePlannerMode(onChange: () => void) {
  window.addEventListener("popstate", onChange);
  return () => window.removeEventListener("popstate", onChange);
}

function plannerModeFromLocation(): "automatic" | "manual" {
  return new URLSearchParams(window.location.search).get("mode") === "manual"
    ? "manual"
    : "automatic";
}

export default function PlannerPage() {
  const {
    academicSummary,
    courses,
    plannerResult,
    plannerLoading,
    plannerError,
    requestTargetPlan,
    clearPlanner,
  } = useAppState();

  const [targetInput, setTargetInput] = useState("");
  const [maxGrade, setMaxGrade] = useState("AA");
  const [strategy, setStrategy] = useState<PlannerStrategyId>("min_courses");
  const urlMode = useSyncExternalStore(
    subscribePlannerMode,
    plannerModeFromLocation,
    () => "automatic" as const,
  );
  const [modeOverride, setModeOverride] = useState<
    "automatic" | "manual" | null
  >(null);
  const mode = modeOverride ?? urlMode;

  const parsedTarget = parseTargetGpa(targetInput);
  const currentGpa = academicSummary?.currentGpa ?? null;
  const selectedStrategy = PLANNER_STRATEGIES.find((item) => item.id === strategy);
  const canSubmit =
    parsedTarget !== null && courses.length > 0 && !plannerLoading;
  const autoResultRef = useRef<HTMLDivElement>(null);
  const shouldScrollToAutoResultRef = useRef(false);

  function markInputsChanged() {
    if (plannerResult || plannerError) {
      clearPlanner();
    }
  }

  useEffect(() => {
    if (plannerError) {
      shouldScrollToAutoResultRef.current = false;
    }
  }, [plannerError]);

  useEffect(() => {
    if (!shouldScrollToAutoResultRef.current) return;
    if (plannerLoading || !plannerResult) return;

    shouldScrollToAutoResultRef.current = false;
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    const frame = window.requestAnimationFrame(() => {
      autoResultRef.current?.scrollIntoView({
        behavior: reduceMotion ? "auto" : "smooth",
        block: "start",
      });
    });

    return () => window.cancelAnimationFrame(frame);
  }, [plannerLoading, plannerResult]);

  return (
    <AppShell>
      <RequireReady>
        <ContentFrame width="dashboard">
          <PageHeader
            title="Planlayıcı"
            description="Otomatik öneri al veya kendi not senaryonu oluştur."
            asideClassName="w-full sm:w-auto"
            aside={
              <div className="flex w-full items-center justify-between rounded-[12px] bg-info-soft/70 px-4 py-3 text-left sm:block sm:w-auto sm:px-3.5 sm:py-2.5 sm:text-right">
                <p className="text-[11px] uppercase tracking-[0.08em] text-info">
                  Mevcut GANO
                </p>
                <p className="font-display text-2xl font-semibold tabular-nums tracking-tight text-ink sm:mt-0.5 sm:text-xl">
                  {currentGpa === null ? "—" : formatGpa(currentGpa)}
                </p>
              </div>
            }
          />

          <div
            className="relative grid w-full max-w-md grid-cols-2 rounded-[14px] bg-surface-muted/70 p-1.5"
            role="tablist"
            aria-label="Planlayıcı modu"
          >
            <span
              aria-hidden
              className="pointer-events-none absolute inset-y-1.5 w-[calc(50%-0.375rem)] rounded-[10px] bg-surface shadow-[var(--shadow-sm)] transition-transform duration-[200ms] ease-[var(--ease)]"
              style={{
                left: "0.375rem",
                transform:
                  mode === "manual" ? "translateX(100%)" : "translateX(0)",
              }}
            />
            <button
              type="button"
              role="tab"
              aria-selected={mode === "automatic"}
              aria-controls="automatic-plan-panel"
              onClick={() => setModeOverride("automatic")}
              className={cx(
                "relative z-[1] min-h-11 rounded-[10px] px-3 py-2.5 text-sm font-semibold transition-colors duration-[180ms]",
                mode === "automatic"
                  ? "text-accent-deep"
                  : "text-muted hover:text-ink",
              )}
            >
              Otomatik Plan
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === "manual"}
              aria-controls="manual-plan-panel"
              onClick={() => setModeOverride("manual")}
              className={cx(
                "relative z-[1] min-h-11 rounded-[10px] px-3 py-2.5 text-sm font-semibold transition-colors duration-[180ms]",
                mode === "manual" ? "text-info" : "text-muted hover:text-ink",
              )}
            >
              Kendi Planım
            </button>
          </div>

          {mode === "automatic" ? (
            <div id="automatic-plan-panel" role="tabpanel" className="space-y-5 gp-enter">
          <div className="min-w-0">
          <Section title="Hedef ve strateji" surface="functional">
            <form
              className="space-y-5"
              onSubmit={(event) => {
                event.preventDefault();
                if (parsedTarget === null) return;
                shouldScrollToAutoResultRef.current = true;
                void requestTargetPlan({
                  targetGpa: parsedTarget,
                  maxGrade,
                  strategy,
                });
              }}
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField label="Hedef GANO">
                  <input
                    type="number"
                    inputMode="decimal"
                    min={0}
                    max={4}
                    step="0.01"
                    placeholder="3.00"
                    value={targetInput}
                    onChange={(event) => {
                      setTargetInput(event.target.value);
                      markInputsChanged();
                    }}
                    className={cx(controlClass, "tabular-nums")}
                  />
                </FormField>
                <FormField label="Maksimum not">
                  <select
                    value={maxGrade}
                    onChange={(event) => {
                      setMaxGrade(event.target.value);
                      markInputsChanged();
                    }}
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

              <fieldset>
                <legend className="text-sm font-medium text-ink">Strateji</legend>
                <div className="mt-2 grid gap-2">
                  {PLANNER_STRATEGIES.map((item) => {
                    const selected = item.id === strategy;
                    return (
                      <label
                        key={item.id}
                        className={cx(
                          "flex cursor-pointer gap-3 rounded-[12px] px-3.5 py-3",
                          selected
                            ? "bg-accent-soft/80 shadow-[inset_3px_0_0_0_var(--accent)]"
                            : "bg-surface-muted/40 hover:bg-surface-muted/70",
                        )}
                      >
                        <input
                          type="radio"
                          name="strategy"
                          value={item.id}
                          checked={selected}
                          onChange={() => {
                            setStrategy(item.id);
                            markInputsChanged();
                          }}
                          className="mt-1 accent-[var(--accent)]"
                        />
                        <span>
                          <span className="block text-sm font-semibold text-ink">
                            {item.label}
                          </span>
                          <span className="mt-0.5 block text-xs leading-5 text-muted">
                            {item.description}
                          </span>
                        </span>
                      </label>
                    );
                  })}
                </div>
              </fieldset>

              <PrimaryButton
                type="submit"
                disabled={!canSubmit}
                className="w-full sm:w-auto"
              >
                {plannerLoading ? "Plan hazırlanıyor" : "Planı Oluştur"}
              </PrimaryButton>
            </form>
          </Section>
          </div>

          {plannerError ? (
            <InlineNotice tone="error">{plannerError}</InlineNotice>
          ) : null}

          {plannerLoading ? (
            <PlannerProcess currentGpa={currentGpa} targetGpa={parsedTarget} />
          ) : null}

          {!plannerResult && !plannerLoading && !plannerError ? (
            <EmptyState title="Hedefini belirleyip planını oluştur." />
          ) : null}

          {plannerResult && !plannerLoading ? (
            <div
              ref={autoResultRef}
              tabIndex={-1}
              className="scroll-mt-[4.75rem] outline-none sm:scroll-mt-6"
            >
              <Reveal>
                <PlannerResult
                  plan={plannerResult}
                  strategyLabel={selectedStrategy?.label ?? plannerResult.strategy}
                />
              </Reveal>
            </div>
          ) : null}
            </div>
          ) : (
            <div id="manual-plan-panel" role="tabpanel">
              <ManualPlanner />
            </div>
          )}
        </ContentFrame>
      </RequireReady>
    </AppShell>
  );
}

function ManualPlanner() {
  const {
    academicSummary,
    activeCourses,
    manualScenarioChanges,
    manualScenarioResult,
    manualScenarioLoading,
    manualScenarioError,
    addManualScenarioChange,
    updateManualScenarioChange,
    removeManualScenarioChange,
    requestManualScenario,
  } = useAppState();
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerIsModal, setPickerIsModal] = useState(false);
  const [pickerQuery, setPickerQuery] = useState("");
  const [courseFilter, setCourseFilter] = useState<
    "all" | "low" | "middle" | "high"
  >("all");
  const [pendingCodes, setPendingCodes] = useState<Set<string>>(
    () => new Set(),
  );
  const pickerTriggerRef = useRef<HTMLButtonElement>(null);
  const pickerDialogRef = useRef<HTMLDivElement>(null);
  const pickerSearchRef = useRef<HTMLInputElement>(null);

  const selectedCodes = useMemo(
    () => new Set(manualScenarioChanges.map((change) => change.courseCode)),
    [manualScenarioChanges],
  );
  const eligibleCourses = useMemo(
    () =>
      activeCourses.filter(
        (course) =>
          !selectedCodes.has(course.code) &&
          getHigherGrades(course.grade).length > 0,
      ),
    [activeCourses, selectedCodes],
  );
  const visiblePickerCourses = useMemo(() => {
    const normalized = pickerQuery.trim().toLocaleLowerCase("tr");
    return eligibleCourses.filter((course) => {
      const matchesQuery =
        !normalized ||
        course.code.toLocaleLowerCase("tr").includes(normalized) ||
        course.name.toLocaleLowerCase("tr").includes(normalized);
      if (!matchesQuery) return false;
      if (courseFilter === "low") {
        return course.grade === "DD" || course.grade === "DC";
      }
      if (courseFilter === "middle") {
        return course.grade === "CC" || course.grade === "CB";
      }
      if (courseFilter === "high") {
        return course.grade === "BB" || course.grade === "BA";
      }
      return true;
    });
  }, [courseFilter, eligibleCourses, pickerQuery]);

  const pendingCount = pendingCodes.size;
  const plannedCount = manualScenarioChanges.length;
  const resultRef = useRef<HTMLDivElement>(null);
  const shouldScrollToResultRef = useRef(false);
  const courseByCode = useMemo(() => {
    const map = new Map(activeCourses.map((course) => [course.code, course]));
    return map;
  }, [activeCourses]);

  const closePicker = useCallback(() => {
    setPickerOpen(false);
    window.requestAnimationFrame(() => pickerTriggerRef.current?.focus());
  }, []);

  const togglePendingCode = useCallback((code: string) => {
    setPendingCodes((current) => {
      const next = new Set(current);
      if (next.has(code)) {
        next.delete(code);
      } else {
        next.add(code);
      }
      return next;
    });
  }, []);

  useEffect(() => {
    if (manualScenarioError) {
      shouldScrollToResultRef.current = false;
    }
  }, [manualScenarioError]);

  useEffect(() => {
    if (!shouldScrollToResultRef.current) return;
    if (manualScenarioLoading || !manualScenarioResult) return;

    shouldScrollToResultRef.current = false;
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    const frame = window.requestAnimationFrame(() => {
      resultRef.current?.scrollIntoView({
        behavior: reduceMotion ? "auto" : "smooth",
        block: "start",
      });
    });

    return () => window.cancelAnimationFrame(frame);
  }, [manualScenarioLoading, manualScenarioResult]);

  useEffect(() => {
    if (!pickerOpen) return;
    const mq = window.matchMedia("(max-width: 767px)");
    const syncModal = () => setPickerIsModal(mq.matches);
    syncModal();
    mq.addEventListener("change", syncModal);
    return () => mq.removeEventListener("change", syncModal);
  }, [pickerOpen]);

  useEffect(() => {
    if (!pickerOpen) return;

    const isMobile = window.matchMedia("(max-width: 767px)").matches;

    function handleDialogKeyboard(event: KeyboardEvent) {
      if (event.key === "Escape") {
        closePicker();
        return;
      }
      if (!isMobile || event.key !== "Tab") return;

      const focusableElements = Array.from(
        pickerDialogRef.current?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), select:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      );
      const firstElement = focusableElements[0];
      const lastElement = focusableElements.at(-1);
      if (!firstElement || !lastElement) {
        event.preventDefault();
        return;
      }

      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }

    window.addEventListener("keydown", handleDialogKeyboard);
    if (!isMobile) {
      return () => window.removeEventListener("keydown", handleDialogKeyboard);
    }

    const previousOverflow = document.body.style.overflow;
    const focusFrame = window.requestAnimationFrame(() => {
      pickerSearchRef.current?.focus({ preventScroll: true });
    });
    document.body.style.overflow = "hidden";

    return () => {
      window.cancelAnimationFrame(focusFrame);
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleDialogKeyboard);
    };
  }, [closePicker, pickerOpen]);

  function addPendingCourses() {
    eligibleCourses.forEach((course) => {
      if (!pendingCodes.has(course.code)) return;
      const nextGrade = getHigherGrades(course.grade)[0];
      if (!nextGrade) return;
      addManualScenarioChange({
        courseCode: course.code,
        newGrade: nextGrade,
      });
    });
    setPendingCodes(new Set());
    setPickerQuery("");
    closePicker();
  }

  return (
    <div
      className={cx(
        "grid min-w-0 gap-4 lg:grid-cols-2 lg:items-start",
        plannedCount > 0 &&
          "pb-[calc(5.75rem+env(safe-area-inset-bottom))] sm:pb-0",
      )}
    >
      <Section title="Kendi not senaryonu oluştur" surface="functional">
        <div className="min-w-0">
          <button
            ref={pickerTriggerRef}
            type="button"
            aria-label="Ders seç"
            aria-haspopup="dialog"
            aria-expanded={pickerOpen}
            aria-controls="manual-course-picker"
            onClick={() => {
              if (pickerOpen) {
                closePicker();
                return;
              }
              setPickerIsModal(window.matchMedia("(max-width: 767px)").matches);
              setPickerOpen(true);
            }}
            className="flex min-h-12 w-full items-center justify-between rounded-[10px] border border-rule bg-surface px-3 text-left text-sm font-semibold text-ink hover:border-accent/40 hover:bg-accent-soft/35 sm:min-h-11"
          >
            <span>Ders seç</span>
            <span className="flex items-center gap-2 text-xs font-medium text-muted">
              {eligibleCourses.length} uygun ders
              <svg
                aria-hidden
                width="15"
                height="15"
                viewBox="0 0 20 20"
                fill="none"
                className={pickerOpen ? "rotate-180" : undefined}
              >
                <path
                  d="m5 7.5 5 5 5-5"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
          </button>

          {pickerOpen ? (
            <ManualCoursePickerSurface
              modal={pickerIsModal}
              dialogRef={pickerDialogRef}
              searchRef={pickerSearchRef}
              pendingCount={pendingCount}
              visibleCourses={visiblePickerCourses}
              pendingCodes={pendingCodes}
              courseFilter={courseFilter}
              pickerQuery={pickerQuery}
              onClose={closePicker}
              onQueryChange={setPickerQuery}
              onFilterChange={setCourseFilter}
              onToggleCode={togglePendingCode}
              onAddSelected={addPendingCourses}
            />
          ) : null}
        </div>
      </Section>

      <div className="min-w-0 space-y-4">
      {plannedCount > 0 ? (
        <Section title="Seçtiğin değişiklikler" surface="functional">
          <div
            className="mb-3 flex items-center justify-between gap-3 rounded-[10px] border border-rule/80 bg-surface-muted px-3 py-2.5"
            aria-live="polite"
          >
            <p className="text-sm font-semibold tabular-nums text-ink">
              {plannedCount} ders seçildi
            </p>
            <p className="text-xs text-muted">Hedef notları ayarla</p>
          </div>
          <ul className="divide-y divide-rule">
            {manualScenarioChanges.map((change) => {
              const course = courseByCode.get(change.courseCode);
              if (!course) return null;
              return (
                <li
                  key={change.courseCode}
                  className="flex min-w-0 flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
                >
                  <div className="min-w-0 flex-1 basis-[12rem]">
                    <p className="truncate font-semibold tracking-wide text-ink">
                      {course.code}
                    </p>
                    <p className="truncate text-sm text-muted">{course.name}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <div className="flex items-center gap-1.5">
                      <GradeBadge grade={course.grade} />
                      <span className="text-faint" aria-hidden>
                        →
                      </span>
                      <div className="w-20">
                        <select
                          value={change.newGrade}
                          onChange={(event) =>
                            updateManualScenarioChange(
                              change.courseCode,
                              event.target.value,
                            )
                          }
                          className={cx(
                            controlClass,
                            "h-11 rounded-md py-0 pl-2 pr-6 text-sm font-semibold md:h-8 md:text-xs",
                          )}
                          aria-label={`${course.code} hedef notu`}
                        >
                          {getHigherGrades(course.grade).map((grade) => (
                            <option key={grade} value={grade}>
                              {grade}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <QuietDangerButton
                      type="button"
                      onClick={() =>
                        removeManualScenarioChange(change.courseCode)
                      }
                      className="h-11 px-3 text-sm md:h-8 md:px-2 md:text-xs"
                    >
                      Kaldır
                    </QuietDangerButton>
                  </div>
                </li>
              );
            })}
          </ul>
          <PrimaryButton
            type="button"
            disabled={plannedCount === 0 || manualScenarioLoading}
            onClick={() => {
              shouldScrollToResultRef.current = true;
              void requestManualScenario();
            }}
            className="mt-5 hidden w-full sm:inline-flex sm:w-auto"
          >
            {manualScenarioLoading
              ? "Sonuç hesaplanıyor"
              : "Planımı Hesapla"}
          </PrimaryButton>
        </Section>
      ) : (
        <EmptyState
          title="Planına henüz ders eklemedin."
          description="Yukarıdan ders seç, hedef notunu ayarla ve planını hesapla."
        />
      )}

      {manualScenarioError ? (
        <InlineNotice tone="error">{manualScenarioError}</InlineNotice>
      ) : null}
      {manualScenarioLoading ? (
        <ManualProcess currentGpa={academicSummary?.currentGpa ?? null} />
      ) : null}
      {manualScenarioResult && !manualScenarioLoading ? (
        <div
          ref={resultRef}
          tabIndex={-1}
          className="scroll-mt-[4.75rem] outline-none sm:scroll-mt-6"
        >
          <Reveal>
            <ManualScenarioResult result={manualScenarioResult} />
          </Reveal>
        </div>
      ) : null}
      </div>

      {plannedCount > 0 ? (
        <div className="fixed inset-x-0 bottom-0 z-40 border-t border-rule bg-surface px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 shadow-[var(--shadow-md)] sm:hidden">
          <div className="mx-auto flex max-w-lg items-center gap-3">
            <p
              className="shrink-0 text-sm font-semibold tabular-nums text-ink"
              aria-live="polite"
            >
              {plannedCount} ders seçildi
            </p>
            <PrimaryButton
              type="button"
              disabled={manualScenarioLoading}
              onClick={() => {
                shouldScrollToResultRef.current = true;
                void requestManualScenario();
              }}
              className="min-h-12 flex-1"
            >
              {manualScenarioLoading
                ? "Hesaplanıyor…"
                : "Planımı Hesapla"}
            </PrimaryButton>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function getHigherGrades(currentGrade: string): string[] {
  const currentIndex = LETTER_GRADES.findIndex(
    (grade) => grade === currentGrade,
  );
  if (currentIndex <= 0) return [];
  return [...LETTER_GRADES.slice(0, currentIndex)].reverse();
}

function ManualCoursePickerSurface({
  modal,
  dialogRef,
  searchRef,
  pendingCount,
  visibleCourses,
  pendingCodes,
  courseFilter,
  pickerQuery,
  onClose,
  onQueryChange,
  onFilterChange,
  onToggleCode,
  onAddSelected,
}: {
  modal: boolean;
  dialogRef: RefObject<HTMLDivElement | null>;
  searchRef: RefObject<HTMLInputElement | null>;
  pendingCount: number;
  visibleCourses: Array<{ code: string; name: string; grade: string }>;
  pendingCodes: Set<string>;
  courseFilter: "all" | "low" | "middle" | "high";
  pickerQuery: string;
  onClose: () => void;
  onQueryChange: (value: string) => void;
  onFilterChange: (value: "all" | "low" | "middle" | "high") => void;
  onToggleCode: (code: string) => void;
  onAddSelected: () => void;
}) {
  const panel = (
    <div
      ref={dialogRef}
      id="manual-course-picker"
      aria-labelledby="manual-course-picker-title"
      aria-modal={modal || undefined}
      className={cx(
        "flex w-full flex-col border border-rule bg-surface shadow-[var(--shadow-md)]",
        modal
          ? "fixed inset-x-0 bottom-0 z-[70] h-[min(85dvh,100dvh)] max-h-[85dvh] overflow-hidden rounded-t-[20px]"
          : "mt-3 overflow-hidden rounded-[12px]",
      )}
      role="dialog"
    >
      <h2 id="manual-course-picker-title" className="sr-only">
        Ders seç
      </h2>

      <div className="flex shrink-0 flex-col border-b border-rule bg-surface">
        {modal ? (
          <div className="flex items-center justify-between px-4 pb-2 pt-3">
            <div>
              <span className="mx-auto mb-2 block h-1 w-10 rounded-full bg-rule" />
              <p className="font-display text-base font-semibold text-ink">
                Ders seç
              </p>
            </div>
            <button
              type="button"
              className="inline-flex size-11 items-center justify-center rounded-[10px] text-muted hover:bg-surface-muted hover:text-ink"
              aria-label="Kapat"
              onClick={onClose}
            >
              <svg
                aria-hidden
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
              >
                <path
                  d="m6 6 12 12M18 6 6 18"
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeWidth="1.7"
                />
              </svg>
            </button>
          </div>
        ) : null}

        <div className={cx("space-y-2.5 p-3", !modal && "pt-3")}>
          <label className="block">
            <span className="sr-only">Ders ara</span>
            <span className="relative block">
              <svg
                aria-hidden
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
              >
                <circle
                  cx="11"
                  cy="11"
                  r="6.25"
                  stroke="currentColor"
                  strokeWidth="1.7"
                />
                <path
                  d="m16 16 3.5 3.5"
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeWidth="1.7"
                />
              </svg>
              <input
                ref={searchRef}
                type="search"
                value={pickerQuery}
                onChange={(event) => onQueryChange(event.target.value)}
                placeholder="Kod veya ders adı…"
                aria-label="Ders ara"
                className={cx(controlClass, "border-rule bg-surface pl-10")}
                autoComplete="off"
              />
            </span>
          </label>
          <div
            className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-0.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            role="group"
            aria-label="Not filtresi"
          >
            {(
              [
                ["all", "Tümü"],
                ["low", "DD/DC"],
                ["middle", "CC/CB"],
                ["high", "BB ve üzeri"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                aria-pressed={courseFilter === value}
                onClick={() => onFilterChange(value)}
                className={cx(
                  "inline-flex h-9 shrink-0 items-center rounded-full border px-3 text-xs font-medium",
                  courseFilter === value
                    ? "border-info/30 bg-info-soft text-info"
                    : "border-rule bg-surface text-muted hover:bg-surface-muted hover:text-ink",
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div
        className="flex shrink-0 items-center justify-between gap-3 border-b border-rule bg-surface-muted/50 px-4 py-2"
        aria-live="polite"
      >
        <p className="text-xs font-medium tabular-nums text-muted">
          {visibleCourses.length} ders listeleniyor
        </p>
        {pendingCount > 0 ? (
          <p className="text-xs font-semibold tabular-nums text-ink">
            {pendingCount} seçili
          </p>
        ) : null}
      </div>

      <div
        className={cx(
          "min-h-0",
          modal
            ? "flex-1 overflow-y-auto overscroll-contain"
            : "overflow-visible",
        )}
      >
        {visibleCourses.length > 0 ? (
          <ul
            className={cx(
              "divide-y divide-rule",
              !modal && "max-h-72 overflow-y-auto overscroll-contain",
            )}
          >
            {visibleCourses.map((course) => {
              const checked = pendingCodes.has(course.code);
              return (
                <li key={course.code} className="min-w-0">
                  <label
                    className={cx(
                      "flex min-h-14 min-w-0 cursor-pointer items-center gap-3 px-4 py-3 hover:bg-info-soft/40",
                      checked && "bg-info-soft/45",
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => onToggleCode(course.code)}
                      className="size-5 shrink-0 accent-[var(--accent)]"
                    />
                    <span className="min-w-0 flex-1 overflow-hidden">
                      <span className="block truncate text-sm font-semibold text-ink">
                        {course.code}
                      </span>
                      <span className="mt-0.5 block truncate text-xs leading-5 text-muted">
                        {course.name}
                      </span>
                    </span>
                    <GradeBadge grade={course.grade} />
                  </label>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="px-3 py-8 text-center text-sm text-muted">
            Bu filtreye uyan ders yok.
          </p>
        )}
      </div>

      <div className="relative z-10 shrink-0 border-t border-rule bg-surface px-4 pb-[max(0.85rem,env(safe-area-inset-bottom))] pt-3 shadow-[0_-8px_20px_rgb(0_0_0_/0.12)]">
        <SecondaryButton
          type="button"
          disabled={pendingCount === 0}
          onClick={onAddSelected}
          className="min-h-12 w-full"
        >
          {pendingCount > 0
            ? `Seçilenleri plana ekle (${pendingCount})`
            : "Seçilenleri plana ekle"}
        </SecondaryButton>
      </div>
    </div>
  );

  if (!modal) return panel;

  return createPortal(
    <>
      <button
        type="button"
        aria-label="Ders seçiciyi kapat"
        className="fixed inset-0 z-[60] bg-ink/45"
        onClick={onClose}
      />
      {panel}
    </>,
    document.body,
  );
}

function ManualScenarioResult({ result }: { result: ManualScenario }) {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <MetricTile label="Mevcut" value={formatGpa(result.currentGpa)} />
        <MetricTile
          strong
          label="Tahmini GANO"
          value={formatGpa(result.projectedGpa)}
        />
        <MetricTile label="Değişim" value={formatSigned(result.gpaChange)} />
      </div>

      <div>
        <h3 className="text-[11px] font-medium uppercase tracking-[0.08em] text-faint">
          Hesaplanan değişiklikler
        </h3>
        <ul className="mt-2 divide-y divide-rule/80">
          {result.changes.map((change) => (
            <li
              key={change.code}
              className="flex flex-wrap items-center justify-between gap-3 py-3"
            >
              <div>
                <p className="font-semibold tracking-wide text-ink">
                  {change.code}
                </p>
                <p className="text-sm text-muted">{change.name}</p>
              </div>
              <div className="flex min-w-0 items-center gap-1.5">
                <GradeShift from={change.fromGrade} to={change.toGrade} />
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function PlannerResult({
  plan,
  strategyLabel,
}: {
  plan: TargetPlan;
  strategyLabel: string;
}) {
  const showImpact = useMemo(
    () => plan.changes.some((row) => row.gpaGain !== null),
    [plan.changes],
  );

  if (plan.alreadyReached) {
    return (
      <ResultSurface tone="ok">
        <DomainStatus outcome="sufficient">Hedef karşılandı</DomainStatus>
        <OutcomeHero
          label="Mevcut GANO"
          value={formatGpa(plan.currentGpa)}
          supporting={
            <SupportStat label="Hedef" value={formatGpa(plan.targetGpa)} />
          }
        />
      </ResultSurface>
    );
  }

  if (!plan.reachable) {
    return (
      <div className="space-y-5">
        <ResultSurface tone="caution">
          <DomainStatus outcome="unreachable">
            Hedef bu koşullarla ulaşılamıyor
          </DomainStatus>
          <div className="mt-4">
            <OutcomeHero
              label="Ulaşılabilecek en yüksek"
              value={formatGpa(plan.maximumPossibleGpa ?? plan.estimatedGpa)}
              supporting={
                <>
                  <SupportStat
                    label="Hedef"
                    value={formatGpa(plan.targetGpa)}
                  />
                  <SupportStat
                    label="Mevcut"
                    value={formatGpa(plan.currentGpa)}
                  />
                  <span>Maks. not {plan.maxGrade}</span>
                </>
              }
            />
          </div>
        </ResultSurface>
        {plan.changes.length > 0 ? (
          <ChangeList
            changes={plan.changes}
            showImpact={showImpact}
            title="Bu koşullarda en yüksek sonucu sağlayan değişiklikler"
          />
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ResultMetrics plan={plan} strategyLabel={strategyLabel} />
      {plan.changes.length === 0 ? (
        <InlineNotice>Not değişikliği önerilmedi.</InlineNotice>
      ) : (
        <ChangeList
          changes={plan.changes}
          showImpact={showImpact}
          title="Önerilen değişiklikler"
        />
      )}
    </div>
  );
}

function ResultMetrics({
  plan,
  strategyLabel,
}: {
  plan: TargetPlan;
  strategyLabel: string;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-ink">Plan sonucu</p>
        <DomainStatus outcome={plan.reachable ? "reachable" : "unreachable"}>
          {plan.reachable ? "Ulaşılabilir" : strategyLabel}
        </DomainStatus>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <MetricTile label="Mevcut" value={formatGpa(plan.currentGpa)} />
        <MetricTile label="Hedef" value={formatGpa(plan.targetGpa)} />
        <MetricTile
          strong
          label="Tahmini GANO"
          value={formatGpa(plan.estimatedGpa)}
        />
      </div>
    </div>
  );
}

function ChangeList({
  changes,
  showImpact,
  title,
}: {
  changes: TargetPlan["changes"];
  showImpact: boolean;
  title: string;
}) {
  const [visible, setVisible] = useState(8);
  const rows = changes.slice(0, visible);
  return (
    <div>
      <h3 className="text-[11px] font-medium uppercase tracking-[0.08em] text-faint">
        {title}
      </h3>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full min-w-[320px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-rule/80 text-left text-[11px] uppercase tracking-[0.06em] text-faint">
              <th className="py-2 pr-3 font-medium">Ders</th>
              <th className="py-2 font-medium">Not değişimi</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={`${row.code}-${row.fromGrade}-${row.toGrade}`}
                className="border-b border-rule/70 last:border-b-0"
              >
                <td className="py-2.5 pr-3">
                  <p className="font-semibold tracking-wide text-ink">{row.code}</p>
                  <p className="text-xs text-muted">{row.name}</p>
                </td>
                <td className="py-2.5 pr-3">
                  <GradeShift
                    from={row.fromGrade}
                    to={row.toGrade}
                    delta={showImpact ? row.gpaGain : undefined}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {changes.length > visible ? (
        <SecondaryButton
          type="button"
          className="mt-3 w-full sm:w-auto"
          onClick={() => setVisible((count) => count + 8)}
        >
          Daha fazla göster
        </SecondaryButton>
      ) : null}
    </div>
  );
}
