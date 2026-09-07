import { useEffect, useId, useRef, useState } from "react";

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
              <caption className="sr-only">Dönem not ortalamaları tablosu</caption>
              <thead>
                <tr className="border-b border-rule text-left text-xs text-faint">
                  <th className="py-2 pr-2 font-medium">Dönem</th>
                  <th className="py-2 pr-2 font-medium">DNO</th>
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

function pointAnnouncement(row: SemesterSummary) {
  return `${row.semester}, DNO ${formatGpa(row.gpa)}, ağırlık ${row.weight}, ${row.courseCount} ders`;
}

export function SemesterTrendChart({ semesters }: { semesters: SemesterSummary[] }) {
  const barGradientId = useId().replace(/:/g, "");
  const tooltipId = useId().replace(/:/g, "");
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(340);
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new ResizeObserver(([entry]) => {
      if (entry) setWidth(Math.max(240, entry.contentRect.width));
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);
  const [activePoint, setActivePoint] = useState<number | null>(null);
  const narrow = width < 480;
  const medium = width < 640;

  const height = narrow ? 228 : medium ? 252 : 268;
  const labelSize = narrow ? 11 : 12;
  const tickSize = narrow ? 10 : 11;
  const pad = narrow
    ? { top: 28, right: 10, bottom: 48, left: 28 }
    : medium
      ? {
          top: 24,
          right: 12,
          bottom: 46,
          left: 32,
        }
      : {
          top: 24,
          right: 14,
          bottom: 48,
          left: 34,
        };

  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const minGpa = 0;
  const maxGpa = 4;
  const slotW = plotW / Math.max(semesters.length, 1);
  const labelStride = Math.max(1, Math.ceil(68 / slotW));
  const valueStride = Math.max(1, Math.ceil(42 / slotW));

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
    <div ref={containerRef} className="gp-chart-stage min-w-0 w-full px-1 py-2 sm:px-2 sm:py-2.5">
      <div className="gp-chart-stage-glow" aria-hidden />
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className={cx(
          "relative z-[1] block w-full text-ink",
          narrow ? "h-[210px]" : medium ? "h-[240px]" : "h-[256px]",
        )}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Dönem not ortalamaları (DNO), çizgi grafik, 0 ile 4 ölçeğinde. Ayrıntılar için noktaları seçin."
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
          const valueY = Math.max(12, point.y - 12);
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
              {index % valueStride === 0 ? <text
                x={point.x}
                y={valueY}
                textAnchor="middle"
                fill="var(--ink)"
                fontSize={labelSize}
                fontWeight={600}
              >
                {formatGpa(point.row.gpa)}
              </text> : null}
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
          if (index % labelStride !== 0) return null;
          const anchor = "middle";

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
              <tspan x={point.x} dy="0">{parts.year}</tspan>
              <tspan x={point.x} dy="13">{parts.season}</tspan>
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
        DNO: yalnızca ilgili dönemin ortalaması · Ölçek: 0–4
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
        DNO {formatGpa(point.row.gpa)}
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
