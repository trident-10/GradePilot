"use client";

import { useMemo, useState, useSyncExternalStore } from "react";

import { AppShell } from "@/components/AppShell";
import { PlannerProcess, ManualProcess } from "@/components/academic-loading";
import { MetricTile, Panel } from "@/components/dashboard";
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

  function markInputsChanged() {
    if (plannerResult || plannerError) {
      clearPlanner();
    }
  }

  return (
    <AppShell>
      <RequireReady>
        <ContentFrame width="dashboard">
          <PageHeader
            title="Planlayıcı"
            description="Otomatik öneri al veya kendi not senaryonu oluştur."
            aside={
              <div className="rounded-[12px] bg-info-soft/70 px-3.5 py-2.5 text-right">
                <p className="text-[11px] uppercase tracking-[0.08em] text-info">
                  Mevcut GANO
                </p>
                <p className="mt-0.5 font-display text-xl font-semibold tabular-nums tracking-tight text-ink">
                  {currentGpa === null ? "—" : formatGpa(currentGpa)}
                </p>
              </div>
            }
          />

          <div
            className="relative grid max-w-md grid-cols-2 rounded-[14px] bg-surface-muted/70 p-1.5"
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
                "relative z-[1] rounded-[10px] px-3 py-2.5 text-sm font-semibold transition-colors duration-[180ms]",
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
                "relative z-[1] rounded-[10px] px-3 py-2.5 text-sm font-semibold transition-colors duration-[180ms]",
                mode === "manual" ? "text-info" : "text-muted hover:text-ink",
              )}
            >
              Kendi Planım
            </button>
          </div>

          {mode === "automatic" ? (
            <div id="automatic-plan-panel" role="tabpanel" className="space-y-5 gp-enter">
          <div className="grid min-w-0 gap-4 lg:grid-cols-[minmax(0,1fr)_17rem] lg:items-start">
          <Section title="Hedef ve strateji" surface="functional">
            <form
              className="space-y-5"
              onSubmit={(event) => {
                event.preventDefault();
                if (parsedTarget === null) return;
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
                          "flex cursor-pointer gap-3 rounded-[12px] px-3.5 py-3 transition-[background-color,box-shadow,transform] duration-[180ms]",
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

              <PrimaryButton type="submit" disabled={!canSubmit}>
                {plannerLoading ? "Plan hazırlanıyor" : "Planı Oluştur →"}
              </PrimaryButton>
            </form>
          </Section>
          <Panel title="Bağlam" variant="analytics">
            <p className="text-[11px] uppercase tracking-[0.08em] text-faint">
              Mevcut GANO
            </p>
            <p className="mt-1 font-display text-[2rem] font-semibold tabular-nums tracking-[-0.04em] text-ink">
              {currentGpa === null ? "—" : formatGpa(currentGpa)}
            </p>
            <p className="mt-4 text-sm font-medium text-ink">
              {selectedStrategy?.label}
            </p>
            <p className="mt-1 text-xs leading-5 text-muted">
              {selectedStrategy?.description}
            </p>
          </Panel>
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
            <Reveal>
              <PlannerResult
                plan={plannerResult}
                strategyLabel={selectedStrategy?.label ?? plannerResult.strategy}
              />
            </Reveal>
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
  const [pickerQuery, setPickerQuery] = useState("");
  const [courseFilter, setCourseFilter] = useState<
    "all" | "low" | "middle" | "high"
  >("all");
  const [pendingCodes, setPendingCodes] = useState<Set<string>>(
    () => new Set(),
  );

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
    setPickerOpen(false);
  }

  return (
    <div className="grid min-w-0 gap-4 lg:grid-cols-2 lg:items-start">
      <Section title="Kendi not senaryonu oluştur" surface="functional">
        <div>
          <button
            type="button"
            aria-label="Ders seç"
            aria-expanded={pickerOpen}
            aria-controls="manual-course-picker"
            onClick={() => setPickerOpen((open) => !open)}
            className="flex h-11 w-full items-center justify-between rounded-[10px] border border-rule bg-surface px-3 text-left text-sm font-semibold text-ink gp-lift gp-press hover:border-accent/40 hover:bg-accent-soft/35"
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
                className={cx(
                  "transition-transform duration-[180ms]",
                  pickerOpen && "rotate-180",
                )}
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
            <div id="manual-course-picker">
              <Reveal className="mt-3 overflow-hidden rounded-[12px] border border-rule bg-surface shadow-[var(--shadow-md)]">
              <div className="space-y-3 border-b border-rule p-3">
                <input
                  type="search"
                  value={pickerQuery}
                  onChange={(event) => setPickerQuery(event.target.value)}
                  placeholder="Ders kodu veya adıyla ara…"
                  aria-label="Ders ara"
                  className={controlClass}
                  autoComplete="off"
                />
                <div
                  className="flex flex-wrap gap-1.5"
                  role="group"
                  aria-label="Not filtresi"
                >
                  {[
                    ["all", "Tümü"],
                    ["low", "DD/DC"],
                    ["middle", "CC/CB"],
                    ["high", "BB ve üzeri"],
                  ].map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      aria-pressed={courseFilter === value}
                      onClick={() =>
                        setCourseFilter(
                          value as "all" | "low" | "middle" | "high",
                        )
                      }
                      className={cx(
                        "rounded-full border px-2.5 py-1 text-xs font-medium transition-[background-color,border-color,color] duration-[180ms]",
                        courseFilter === value
                          ? "border-info/30 bg-info-soft text-info"
                          : "border-rule text-muted hover:bg-surface-muted hover:text-ink",
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              {visiblePickerCourses.length > 0 ? (
                <ul className="max-h-72 divide-y divide-rule overflow-y-auto">
                  {visiblePickerCourses.map((course) => (
                    <li key={course.code}>
                      <label className="flex cursor-pointer items-center gap-3 px-3 py-2.5 transition-colors duration-[180ms] hover:bg-info-soft/45">
                        <input
                          type="checkbox"
                          checked={pendingCodes.has(course.code)}
                          onChange={() =>
                            setPendingCodes((current) => {
                              const next = new Set(current);
                              if (next.has(course.code)) {
                                next.delete(course.code);
                              } else {
                                next.add(course.code);
                              }
                              return next;
                            })
                          }
                          className="size-4 shrink-0 accent-[var(--accent)]"
                        />
                        <span className="min-w-0 flex-1">
                          <span className="block text-sm font-semibold text-ink">
                            {course.code}
                          </span>
                          <span className="block truncate text-xs text-muted">
                            {course.name}
                          </span>
                        </span>
                        <GradeBadge grade={course.grade} />
                      </label>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="px-3 py-6 text-center text-sm text-muted">
                  Bu filtreye uyan ders yok.
                </p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-rule bg-bg/55 p-3">
                <p className="text-xs text-muted">
                  {pendingCodes.size} ders seçildi
                </p>
                <SecondaryButton
                  type="button"
                  disabled={pendingCodes.size === 0}
                  onClick={addPendingCourses}
                  className="h-9"
                >
                  Seçilenleri plana ekle
                </SecondaryButton>
              </div>
              </Reveal>
            </div>
          ) : null}
        </div>
      </Section>

      <div className="space-y-4">
      {manualScenarioChanges.length > 0 ? (
        <Section
          title={`Seçtiğin değişiklikler · ${manualScenarioChanges.length} ders`}
          surface="functional"
        >
          <ul className="divide-y divide-rule">
            {manualScenarioChanges.map((change) => {
              const course = activeCourses.find(
                (row) => row.code === change.courseCode,
              );
              if (!course) return null;
              return (
                <li
                  key={change.courseCode}
                  className="flex flex-wrap items-center justify-between gap-3 py-3 gp-enter first:pt-0 last:pb-0"
                >
                  <div className="min-w-0">
                    <p className="font-semibold tracking-wide text-ink">
                      {course.code}
                    </p>
                    <p className="text-sm text-muted">{course.name}</p>
                  </div>
                  <div className="flex items-center gap-3">
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
                            "h-8 rounded-md py-0 pl-2 pr-6 text-xs font-semibold",
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
                      className="h-8 px-2 text-xs"
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
            disabled={
              manualScenarioChanges.length === 0 || manualScenarioLoading
            }
            onClick={() => void requestManualScenario()}
            className="mt-5"
          >
            {manualScenarioLoading
              ? "Sonuç hesaplanıyor"
              : "Planımı Hesapla →"}
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
        <Reveal>
          <ManualScenarioResult result={manualScenarioResult} />
        </Reveal>
      ) : null}
      </div>
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
          className="mt-3 h-9"
          onClick={() => setVisible((count) => count + 8)}
        >
          Daha fazla göster
        </SecondaryButton>
      ) : null}
    </div>
  );
}
