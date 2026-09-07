import type { ButtonHTMLAttributes, ReactNode } from "react";

import { AcademicLoader, AcademicProcessCard, AcademicSkeleton } from "@/components/academic-loading";
import { cx, formatSigned, weightingChip } from "@/lib/display";
import { gradeBadgeClass } from "@/lib/gradeColors";

export function ContentFrame({
  width = "default",
  className,
  children,
}: {
  width?: "narrow" | "default" | "medium" | "wide" | "dashboard";
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={cx(
        "mx-auto w-full px-1 sm:px-0",
        width === "dashboard" ? "space-y-6 sm:space-y-7" : "space-y-7",
        width === "narrow" && "max-w-xl",
        width === "default" && "max-w-3xl",
        width === "medium" && "max-w-5xl",
        width === "wide" && "max-w-6xl",
        width === "dashboard" && "max-w-[1440px]",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  aside,
  asideClassName,
}: {
  title: string;
  description?: string;
  aside?: ReactNode;
  asideClassName?: string;
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4 pb-1">
      <div className="max-w-2xl">
        <h1 className="font-display text-[1.55rem] font-semibold leading-[1.1] tracking-[-0.04em] text-ink sm:text-[1.8rem] md:text-[2rem]">
          {title}
        </h1>
        {description ? (
          <p className="mt-2 max-w-xl text-[0.9375rem] leading-6 text-muted">
            {description}
          </p>
        ) : null}
      </div>
      {aside ? (
        <div className={cx("shrink-0", asideClassName)}>{aside}</div>
      ) : null}
    </header>
  );
}

type SurfaceLevel = "open" | "functional" | "result";

export function Section({
  title,
  description,
  children,
  className,
  bordered,
  surface = "functional",
}: {
  title?: string;
  description?: string;
  children: ReactNode;
  className?: string;
  /** @deprecated Prefer `surface`. */
  bordered?: boolean;
  surface?: SurfaceLevel;
}) {
  const level =
    bordered === false ? "open" : bordered === true ? "functional" : surface;

  return (
    <section
      className={cx(
        level === "open" && "py-1",
        level === "functional" &&
          "rounded-[14px] border border-rule/80 bg-surface/90 p-5 shadow-[var(--shadow-sm)] md:p-6",
        level === "result" &&
          "rounded-[16px] border border-info/20 bg-info-soft/55 p-5 shadow-[var(--shadow-sm)] md:p-6",
        className,
      )}
    >
      {title ? (
        <h2 className="font-display text-[1.08rem] font-semibold tracking-[-0.02em] text-ink md:text-lg">
          {title}
        </h2>
      ) : null}
      {description ? (
        <p className={cx("text-sm leading-6 text-muted", title ? "mt-1" : "")}>
          {description}
        </p>
      ) : null}
      <div className={title || description ? "mt-5" : ""}>{children}</div>
    </section>
  );
}

/** Stronger outcome treatment for calculated results. */
export function ResultSurface({
  children,
  className,
  tone = "info",
}: {
  children: ReactNode;
  className?: string;
  tone?: "info" | "accent" | "ok" | "caution";
}) {
  return (
    <div
      className={cx(
        "rounded-[16px] border p-5 shadow-[var(--shadow-sm)] gp-enter md:p-6",
        tone === "info" && "border-info/25 bg-info-soft/60",
        tone === "accent" && "border-accent/25 bg-accent-soft/55",
        tone === "ok" && "border-ok/25 bg-ok-soft/55",
        tone === "caution" && "border-caution/25 bg-caution-soft/55",
        className,
      )}
    >
      {children}
    </div>
  );
}

/** Primary calculated number with supporting stats — not a row of equal KPI cards. */
export function OutcomeHero({
  label,
  value,
  delta,
  supporting,
}: {
  label: string;
  value: ReactNode;
  delta?: ReactNode;
  supporting?: ReactNode;
}) {
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-faint">
        {label}
      </p>
      <div className="mt-2 flex flex-wrap items-end gap-x-4 gap-y-1">
        <p className="font-display text-[2.85rem] font-semibold leading-none tabular-nums tracking-[-0.05em] text-ink sm:text-[3.15rem]">
          {value}
        </p>
        {delta ? (
          <p className="pb-1 font-display text-xl font-semibold tabular-nums tracking-tight text-ok">
            {delta}
          </p>
        ) : null}
      </div>
      {supporting ? (
        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 border-t border-current/10 pt-3 text-sm text-muted">
          {supporting}
        </div>
      ) : null}
    </div>
  );
}

export function Reveal({
  children,
  className,
  delay = false,
}: {
  children: ReactNode;
  className?: string;
  delay?: boolean;
}) {
  return (
    <div className={cx(delay ? "gp-enter-delay" : "gp-enter", className)}>
      {children}
    </div>
  );
}

export function InfoNote({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-[10px] border border-info/20 bg-info-soft/80 px-3.5 py-2.5 text-sm leading-6 text-info">
      {children}
    </p>
  );
}

export function DomainStatus({
  outcome,
  children,
}: {
  outcome: "reachable" | "unreachable" | "sufficient" | "neutral";
  children: ReactNode;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        outcome === "reachable" && "bg-ok-soft text-ok",
        outcome === "sufficient" && "bg-ok-soft text-ok",
        outcome === "unreachable" && "bg-caution-soft text-caution",
        outcome === "neutral" && "bg-info-soft text-info",
      )}
    >
      <span
        className={cx(
          "size-1.5 rounded-full",
          outcome === "reachable" && "bg-ok",
          outcome === "sufficient" && "bg-ok",
          outcome === "unreachable" && "bg-caution",
          outcome === "neutral" && "bg-info",
        )}
        aria-hidden
      />
      {children}
    </span>
  );
}

export function GradeBadge({ grade }: { grade: string }) {
  return (
    <span
      className={cx(
        "inline-flex min-w-[2.25rem] shrink-0 items-center justify-center rounded-md px-1.5 py-0.5 text-xs font-semibold tabular-nums",
        gradeBadgeClass(grade),
      )}
    >
      {grade}
    </span>
  );
}

export function GradeShift({
  from,
  to,
  delta,
}: {
  from: string;
  to: string;
  delta?: number | null;
}) {
  return (
    <span className="inline-flex flex-wrap items-center gap-1.5">
      <GradeBadge grade={from} />
      <span className="text-faint" aria-hidden>
        →
      </span>
      <GradeBadge grade={to} />
      {delta === undefined || delta === null ? null : (
        <span
          className={cx(
            "pl-1 font-medium tabular-nums",
            delta > 0 && "text-ok",
            delta < 0 && "text-danger",
            delta === 0 && "text-muted",
          )}
        >
          {formatSigned(delta)}
        </span>
      )}
    </span>
  );
}

export function Metric({
  label,
  value,
  hint,
  emphasis = false,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  emphasis?: boolean;
}) {
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-faint">
        {label}
      </p>
      <p
        className={cx(
          "mt-1.5 font-display font-semibold tabular-nums tracking-[-0.04em]",
          emphasis
            ? "text-[2.1rem] leading-none text-accent-deep md:text-[2.4rem]"
            : "text-[1.65rem] leading-none text-ink md:text-2xl",
        )}
      >
        {value}
      </p>
      {hint ? <p className="mt-1.5 text-xs leading-5 text-muted">{hint}</p> : null}
    </div>
  );
}

export function StatusBadge({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "ok" | "caution" | "error" | "info";
  children: ReactNode;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        tone === "ok" && "bg-ok-soft text-ok",
        tone === "caution" && "bg-caution-soft text-caution",
        tone === "error" && "bg-danger-soft text-danger",
        tone === "info" && "bg-info-soft text-info",
        tone === "neutral" && "bg-surface-muted text-muted",
      )}
    >
      {children}
    </span>
  );
}

export function WeightingChip({ mode }: { mode: string | null }) {
  return <StatusBadge tone="info">{weightingChip(mode)}</StatusBadge>;
}

export function SupportStat({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <span>
      {label}{" "}
      <span className="font-semibold tabular-nums text-ink">{value}</span>
    </span>
  );
}

const buttonBase =
  "inline-flex h-11 items-center justify-center gap-1.5 rounded-[11px] px-4 text-sm font-semibold tracking-[-0.01em] gp-lift gp-press sm:h-10 disabled:cursor-not-allowed disabled:opacity-55 disabled:shadow-none disabled:transform-none";

export function PrimaryButton({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cx(
        buttonBase,
        "bg-accent text-on-accent shadow-[var(--shadow-sm)] hover:bg-[var(--accent-hover)]",
        className,
      )}
      {...props}
    />
  );
}

export function SecondaryButton({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cx(
        buttonBase,
        "border border-rule/90 bg-surface/90 text-ink hover:border-accent/35 hover:bg-accent-soft/40 hover:text-accent-deep",
        className,
      )}
      {...props}
    />
  );
}

export function GhostButton({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cx(
        buttonBase,
        "text-muted shadow-none hover:bg-surface-muted/80 hover:text-ink hover:shadow-none",
        className,
      )}
      {...props}
    />
  );
}

export function QuietDangerButton({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cx(
        buttonBase,
        "text-faint shadow-none hover:bg-danger-soft hover:text-danger hover:shadow-none",
        className,
      )}
      {...props}
    />
  );
}

export function FormField({
  label,
  hint,
  children,
  labelClassName,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
  labelClassName?: string;
}) {
  return (
    <label className="block">
      <span className={cx("text-sm font-medium text-ink", labelClassName)}>
        {label}
      </span>
      <span className="mt-1.5 block">{children}</span>
      {hint ? (
        <span className="mt-1 block text-xs leading-5 text-faint">{hint}</span>
      ) : null}
    </label>
  );
}

export const controlClass =
  "h-11 w-full rounded-[11px] border border-rule/90 bg-surface/95 px-3 text-base text-ink outline-none transition-[background-color,border-color,box-shadow] duration-[180ms] placeholder:text-faint hover:border-accent/30 focus-visible:border-accent focus-visible:shadow-[0_0_0_3px_color-mix(in_srgb,var(--accent)_18%,transparent)] sm:h-10 sm:text-sm";

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="rounded-[12px] bg-surface/70 px-3 py-4 text-center">
      <p className="text-sm font-medium text-ink">{title}</p>
      {description ? (
        <p className="mx-auto mt-1 max-w-sm text-xs leading-5 text-muted">
          {description}
        </p>
      ) : null}
    </div>
  );
}

export function InlineNotice({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "error" | "caution" | "info";
  children: ReactNode;
}) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cx(
        "rounded-[12px] border px-4 py-3 text-sm leading-6 gp-enter",
        tone === "error" && "border-danger/30 bg-danger-soft text-danger",
        tone === "caution" && "border-caution/25 bg-caution-soft text-caution",
        tone === "info" && "border-info/20 bg-info-soft text-info",
        tone === "neutral" && "border-rule bg-surface/90 text-muted",
      )}
    >
      {children}
    </div>
  );
}

export function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div className={cx("gp-skeleton rounded-lg", className)} aria-hidden />
  );
}

export function LoadingBlock({ label }: { label: string }) {
  return (
    <AcademicProcessCard
      label={label}
      skeleton={
        <>
          <AcademicSkeleton className="h-8 w-40" />
          <AcademicSkeleton className="h-16 w-full" />
        </>
      }
    >
      <AcademicLoader variant="planner" />
    </AcademicProcessCard>
  );
}
