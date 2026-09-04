import { useId, useState, useSyncExternalStore } from "react";

import { Section, SkeletonBlock } from "@/components/ui";
import { cx, formatGpa } from "@/lib/display";
import type { SemesterSummary } from "@/lib/types";

type SemesterSummaryTableProps = {
  semesters: SemesterSummary[];
  loading?: boolean;
};

export function SemesterSummaryTable({
  semesters,
  loading = false,
}: SemesterSummaryTableProps) {
  return (
    <Section
      title="Dönem performansı"
      description="Akademik performansının dönemlere göre değişimini incele."
      surface="open"
    >
      {loading ? (
        <div className="space-y-2">
          <SkeletonBlock className="h-40" />
          <SkeletonBlock className="h-10" />
        </div>
      ) : semesters.length === 0 ? (
        <p className="text-sm text-muted">Gösterilecek dönem verisi yok.</p>
      ) : (
        <div className="space-y-4">
          <SemesterHighlights semesters={semesters} />
          <SemesterTrendChart semesters={semesters} />
          <div className="-mx-1 overflow-x-auto sm:mx-0">
            <table className="w-full min-w-[400px] border-collapse text-xs sm:text-sm">
              <caption className="sr-only">Dönem GANO tablosu</caption>
              <thead>
                <tr className="border-b border-rule text-left text-xs text-faint">
                  <th className="py-2 pr-2 font-medium">Dönem</th>
                  <th className="py-2 pr-2 font-medium">GANO</th>
                  <th className="py-2 pr-2 font-medium">Ağırlık</th>
                  <th className="py-2 font-medium">Ders</th>
                </tr>
              </thead>
              <tbody>
                {semesters.map((row, index) => (
                  <tr
                    key={row.semester}
                    className={cx(
                      "border-b border-rule transition-colors last:border-b-0 hover:bg-bg/70",
                      index === semesters.length - 1 && "bg-info-soft/30",
                    )}
                  >
                    <td className="py-2.5 pr-2 text-ink">{row.semester}</td>
                    <td className="py-2.5 pr-2 font-semibold tabular-nums text-ink">
                      {formatGpa(row.gpa)}
                    </td>
                    <td className="py-2.5 pr-2 tabular-nums text-muted">
                      {row.weight}
                    </td>
                    <td className="py-2.5 tabular-nums text-muted">
                      {row.courseCount}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Section>
  );
}

function SemesterHighlights({ semesters }: { semesters: SemesterSummary[] }) {
  const latest = semesters.at(-1);
  const previous = semesters.length > 1 ? semesters.at(-2) : null;
  const highest = semesters.reduce((best, row) =>
    row.gpa > best.gpa ? row : best,
  );
  if (!latest) return null;

  return (
    <div className="flex flex-col gap-4 border-b border-rule/70 pb-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-faint">
          Son dönem
        </p>
        <p className="mt-1 font-display text-[2rem] font-semibold leading-none tabular-nums tracking-[-0.04em] text-ink">
          {formatGpa(latest.gpa)}
        </p>
        <p className="mt-1.5 text-sm text-muted">{latest.semester}</p>
      </div>
      <dl className="flex flex-wrap gap-x-8 gap-y-3">
        {previous ? (
          <div>
            <dt className="text-[11px] uppercase tracking-[0.08em] text-faint">
              Önceki
            </dt>
            <dd className="mt-0.5 font-display text-xl font-semibold tabular-nums tracking-tight text-ink">
              {formatGpa(previous.gpa)}
            </dd>
            <dd className="mt-0.5 max-w-[10rem] truncate text-xs text-muted">
              {previous.semester}
            </dd>
          </div>
        ) : null}
        <div>
          <dt className="text-[11px] uppercase tracking-[0.08em] text-faint">
            En yüksek
          </dt>
          <dd className="mt-0.5 font-display text-xl font-semibold tabular-nums tracking-tight text-ink">
            {formatGpa(highest.gpa)}
          </dd>
          <dd className="mt-0.5 max-w-[10rem] truncate text-xs text-muted">
            {highest.semester}
          </dd>
        </div>
      </dl>
    </div>
  );
}

type ChartViewport = "narrow" | "medium" | "wide";

const NARROW_QUERY = "(max-width: 639px)";
const MEDIUM_QUERY = "(min-width: 640px) and (max-width: 1023px)";

function useChartViewport(): ChartViewport {
  return useSyncExternalStore(
    (onChange) => {
      const narrow = window.matchMedia(NARROW_QUERY);
      const medium = window.matchMedia(MEDIUM_QUERY);
      narrow.addEventListener("change", onChange);
      medium.addEventListener("change", onChange);
      return () => {
        narrow.removeEventListener("change", onChange);
        medium.removeEventListener("change", onChange);
      };
    },
    () => {
      if (window.matchMedia(NARROW_QUERY).matches) return "narrow";
      if (window.matchMedia(MEDIUM_QUERY).matches) return "medium";
      return "wide";
    },
    () => "wide",
  );
}

function pointAnnouncement(row: SemesterSummary) {
  return `${row.semester}, GANO ${formatGpa(row.gpa)}, ağırlık ${row.weight}, ${row.courseCount} ders`;
}

export function SemesterTrendChart({ semesters }: { semesters: SemesterSummary[] }) {
  const barGradientId = useId().replace(/:/g, "");
  const tooltipId = useId().replace(/:/g, "");
  const viewport = useChartViewport();
  const [activePoint, setActivePoint] = useState<number | null>(null);
  const narrow = viewport === "narrow";
  const medium = viewport === "medium";
  // Full two-line labels when space allows: always for ≤4 periods on tablet+,
  // and for ≤5 periods on desktop. Mobile always uses compact labels.
  const useFullTwoLineLabels =
    !narrow && semesters.length <= (medium ? 4 : 5);

  const width = narrow ? 340 : medium ? 560 : 720;
  const height = narrow ? 228 : medium ? 252 : 268;
  const labelSize = narrow ? 11 : 12;
  const tickSize = narrow ? 10 : 11;
  const pad = narrow
    ? { top: 22, right: 10, bottom: 36, left: 28 }
    : medium
      ? {
          top: 24,
          right: 12,
          bottom: useFullTwoLineLabels ? 46 : 38,
          left: 32,
        }
      : {
          top: 24,
          right: 14,
          bottom: useFullTwoLineLabels ? 48 : 38,
          left: 34,
        };

  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const minGpa = 0;
  const maxGpa = 4;
  const useCompactLabels = narrow;
  const dense = semesters.length > 6;
  const slotW = plotW / Math.max(semesters.length, 1);

  const points = semesters.map((row, index) => {
    const x = pad.left + slotW * index + slotW / 2;
    const y =
      pad.top +
      plotH -
      Math.max(2, ((row.gpa - minGpa) / (maxGpa - minGpa)) * plotH);
    return { x, y, row };
  });

  const linePath = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");
  const ticks = [0, 1, 2, 3, 4];
  const focusedPoint =
    activePoint === null ? null : (points[activePoint] ?? null);

  return (
    <div className="gp-chart-stage w-full px-1 py-2 sm:px-2 sm:py-2.5">
      <div className="gp-chart-stage-glow" aria-hidden />
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className={cx(
          "relative z-[1] block w-full text-ink",
          narrow ? "h-[210px]" : medium ? "h-[240px]" : "h-[256px]",
        )}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Dönem GANO trendi, çizgi grafik, 0 ile 4 ölçeğinde. Değerler aşağıdaki tabloda da listelenir."
      >
        <defs>
          <linearGradient id={barGradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--info)" stopOpacity="0.22" />
            <stop offset="100%" stopColor="var(--info)" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {ticks.map((tick) => {
          const y =
            pad.top + (1 - (tick - minGpa) / (maxGpa - minGpa)) * plotH;
          return (
            <g key={tick}>
              <line
                x1={pad.left}
                y1={y}
                x2={width - pad.right}
                y2={y}
                stroke="var(--rule)"
                strokeWidth={tick === 0 ? 1.25 : 1}
                strokeOpacity={tick === 0 ? 0.75 : 0.28}
                strokeDasharray={tick === 0 ? undefined : "3 5"}
              />
              <text
                x={pad.left - 6}
                y={y + 3.5}
                textAnchor="end"
                fill="var(--faint)"
                fontSize={tickSize}
              >
                {tick}
              </text>
            </g>
          );
        })}

        {points.length > 1 ? (
          <path
            d={`${linePath} L ${points[points.length - 1].x} ${pad.top + plotH} L ${points[0].x} ${pad.top + plotH} Z`}
            fill={`url(#${barGradientId})`}
          />
        ) : null}

        {points.length > 1 ? (
          <path
            d={linePath}
            fill="none"
            stroke="var(--info)"
            strokeWidth={narrow ? 2 : 2.25}
            strokeLinejoin="round"
            strokeLinecap="round"
            strokeOpacity="0.85"
            pathLength="1"
            className="gp-chart-line"
          />
        ) : null}

        {points.map((point, index) => {
          const valueY = Math.max(pad.top + 11, point.y - 10);
          const selected = activePoint === index;
          return (
            <g
              key={point.row.semester}
              className="gp-chart-point cursor-pointer"
              style={{ animationDelay: `${100 + index * 40}ms` }}
              tabIndex={0}
              focusable="true"
              role="button"
              data-chart-point=""
              aria-label={pointAnnouncement(point.row)}
              aria-expanded={selected ? "true" : "false"}
              aria-describedby={selected ? tooltipId : undefined}
              onMouseEnter={() => setActivePoint(index)}
              onMouseLeave={(event) => {
                if (event.currentTarget !== document.activeElement) {
                  setActivePoint(null);
                }
              }}
              onFocus={() => setActivePoint(index)}
              onBlur={() => setActivePoint(null)}
              onKeyDown={(event) => {
                if (event.key === "Escape") {
                  event.preventDefault();
                  setActivePoint(null);
                  event.currentTarget.blur();
                  return;
                }
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setActivePoint(index);
                }
              }}
            >
              <circle
                className="gp-chart-hit"
                cx={point.x}
                cy={point.y}
                r={14}
                fill="transparent"
              />
              <circle
                className="gp-chart-focus-ring"
                cx={point.x}
                cy={point.y}
                r={8}
                fill="none"
                stroke="var(--accent)"
                strokeWidth={1.5}
              />
              <circle
                cx={point.x}
                cy={point.y}
                r={4.75}
                fill="var(--surface)"
                stroke="var(--info)"
                strokeWidth={2}
              />
              <text
                x={point.x}
                y={valueY}
                textAnchor="middle"
                fill="var(--ink)"
                fontSize={labelSize}
                fontWeight={600}
              >
                {formatGpa(point.row.gpa)}
              </text>
            </g>
          );
        })}

        {focusedPoint ? (
          <ChartTooltip
            point={focusedPoint}
            width={width}
            pad={pad}
            narrow={narrow}
          />
        ) : null}

        {points.map((point, index) => {
          const isLast = index === points.length - 1 && points.length > 1;
          if (
            dense &&
            useCompactLabels &&
            index % 2 !== 0 &&
            !isLast
          ) {
            return null;
          }
          const isFirst = index === 0;
          const anchor = isFirst ? "start" : isLast ? "end" : "middle";

          if (useCompactLabels) {
            return (
              <text
                key={`${point.row.semester}-label`}
                x={point.x}
                y={height - 10}
                textAnchor={anchor}
                fill="var(--muted)"
                fontSize={9.5}
              >
                {shortSemesterLabel(point.row.semester)}
              </text>
            );
          }

          if (useFullTwoLineLabels) {
            const parts = splitSemesterLabel(point.row.semester);
            return (
              <text
                key={`${point.row.semester}-label`}
                x={point.x}
                y={height - 28}
                textAnchor={anchor}
                fill="var(--muted)"
                fontSize={medium ? 10.5 : 11}
              >
                <tspan x={point.x} dy="0">
                  {parts.year}
                </tspan>
                <tspan x={point.x} dy="13">
                  {parts.season}
                </tspan>
              </text>
            );
          }

          return (
            <text
              key={`${point.row.semester}-label`}
              x={point.x}
              y={height - 12}
              textAnchor={anchor}
              fill="var(--muted)"
              fontSize={10.5}
            >
              {shortSemesterLabel(point.row.semester)}
            </text>
          );
        })}
      </svg>
      {focusedPoint ? (
        <p
          id={tooltipId}
          data-chart-tooltip=""
          role="status"
          className="sr-only"
        >
          {pointAnnouncement(focusedPoint.row)}
        </p>
      ) : null}
      <p className="relative z-[1] mt-1 px-1 text-[11px] text-faint">
        Akademik ölçek: 0.0 – 4.0 GANO
      </p>
    </div>
  );
}

function ChartTooltip({
  point,
  width,
  pad,
  narrow,
}: {
  point: { x: number; y: number; row: SemesterSummary };
  width: number;
  pad: { top: number; right: number; bottom: number; left: number };
  narrow: boolean;
}) {
  const tooltipWidth = narrow ? 168 : 188;
  const tooltipHeight = 66;
  const x = Math.min(
    width - pad.right - tooltipWidth,
    Math.max(pad.left, point.x - tooltipWidth / 2),
  );
  const y =
    point.y < pad.top + tooltipHeight + 10
      ? point.y + 12
      : point.y - tooltipHeight - 12;

  return (
    <g className="gp-fade" pointerEvents="none" aria-hidden>
      <rect
        x={x}
        y={y}
        width={tooltipWidth}
        height={tooltipHeight}
        rx="7"
        fill="var(--surface)"
        stroke="var(--info)"
        strokeOpacity="0.4"
      />
      <text
        x={x + 10}
        y={y + 16}
        fill="var(--muted)"
        fontSize={narrow ? 9 : 10.5}
      >
        {point.row.semester}
      </text>
      <text
        x={x + 10}
        y={y + 34}
        fill="var(--ink)"
        fontSize={narrow ? 12 : 13}
        fontWeight="700"
      >
        GANO {formatGpa(point.row.gpa)}
      </text>
      <text
        x={x + 10}
        y={y + 50}
        fill="var(--muted)"
        fontSize={narrow ? 9 : 10}
      >
        Ağırlık {point.row.weight} · {point.row.courseCount} ders
      </text>
    </g>
  );
}

const SEMESTER_PATTERN = /^\d{2}(\d{2})\s*[-–/]\s*\d{2}(\d{2})\s*(.*)$/;

function semesterParts(semester: string) {
  const match = SEMESTER_PATTERN.exec(semester.trim());
  if (!match) return null;
  const [, startYear, endYear, rest] = match;
  const season = rest.replace(/dönemi/i, "").trim();
  return { startYear, endYear, season };
}

/** "2024-2025 Güz" -> "24–25 Güz" */
function shortSemesterLabel(semester: string): string {
  const trimmed = semester.trim();
  const parts = semesterParts(trimmed);
  if (!parts) {
    return trimmed.length <= 12 ? trimmed : `${trimmed.slice(0, 10)}…`;
  }
  return `${parts.startYear}–${parts.endYear}${parts.season ? ` ${parts.season}` : ""}`;
}

/** Split for two-line desktop labels: year range + season. */
function splitSemesterLabel(semester: string): { year: string; season: string } {
  const trimmed = semester.trim();
  const parts = semesterParts(trimmed);
  if (!parts) {
    const tokens = trimmed.split(/\s+/);
    if (tokens.length >= 2) {
      return {
        year: tokens.slice(0, -1).join(" "),
        season: tokens.at(-1) ?? "",
      };
    }
    return { year: trimmed, season: "" };
  }
  return {
    year: `20${parts.startYear}–20${parts.endYear}`,
    season: parts.season || "",
  };
}
