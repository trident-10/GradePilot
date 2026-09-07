import type { ReactNode } from "react";
import Link from "next/link";

import { cx } from "@/lib/display";

export function Panel({
  title,
  action,
  children,
  variant = "analytics",
  className,
}: {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  variant?: "metric" | "analytics" | "table" | "action" | "note" | "result";
  className?: string;
}) {
  return (
    <section
      className={cx(
        "flex h-full flex-col rounded-[16px] p-4 md:p-5",
        variant === "metric" &&
          "border border-rule/70 bg-surface-raised shadow-[var(--shadow-sm)]",
        variant === "analytics" &&
          "border border-rule/70 bg-surface-raised shadow-[var(--shadow-sm)]",
        variant === "table" &&
          "overflow-hidden border border-rule/70 bg-surface-raised p-0 shadow-[var(--shadow-sm)]",
        variant === "action" &&
          "border border-accent/25 bg-accent-soft/55 shadow-[var(--shadow-sm)]",
        variant === "note" &&
          "border border-info/25 bg-info-soft/70 p-3.5 text-sm leading-6 text-info",
        variant === "result" &&
          "border border-ok/25 bg-ok-soft/55 shadow-[var(--shadow-sm)]",
        className,
      )}
    >
      {title || action ? (
        <div
          className={cx(
            "flex items-start justify-between gap-3",
            variant === "table" && "px-4 pt-4",
          )}
        >
          {title ? (
            <h2 className="font-display text-base font-semibold leading-snug tracking-[-0.025em] text-ink md:text-[1.05rem]">
              {title}
            </h2>
          ) : (
            <span />
          )}
          {action ? <div className="shrink-0 pt-0.5">{action}</div> : null}
        </div>
      ) : null}
      <div
        className={cx(
          "min-h-0 flex-1",
          title || action ? (variant === "table" ? "mt-3" : "mt-4") : "",
        )}
      >
        {children}
      </div>
    </section>
  );
}

export function MetricTile({
  label,
  value,
  hint,
  strong = false,
  className,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  strong?: boolean;
  className?: string;
}) {
  return (
    <div
      className={cx(
        "flex h-full min-h-[7rem] flex-col rounded-[16px] border border-rule/70 bg-surface-raised px-4 py-4 shadow-[var(--shadow-sm)]",
        strong &&
          "min-h-[7.5rem] border-accent/20 bg-[radial-gradient(120%_90%_at_0%_0%,color-mix(in_srgb,var(--accent)_16%,transparent),var(--surface-raised)_58%)]",
        className,
      )}
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-muted">
        {label}
      </p>
      <p
        className={cx(
          "mt-2 font-display font-semibold tabular-nums tracking-[-0.04em] text-ink",
          strong
            ? "text-[2.25rem] leading-none sm:text-[2.4rem] md:text-[2.6rem]"
            : "text-[1.5rem] leading-none sm:text-[1.65rem] md:text-[1.75rem]",
        )}
      >
        {value}
      </p>
      {hint ? (
        <p className="mt-auto pt-2 text-xs leading-5 text-faint">{hint}</p>
      ) : (
        <span className="mt-auto block min-h-[1.25rem]" aria-hidden />
      )}
    </div>
  );
}

export function DashboardLink({
  href,
  children,
}: {
  href: string;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className="flex items-center justify-between gap-2 rounded-[10px] px-3 py-2.5 text-sm font-medium text-ink hover:bg-surface/80"
    >
      {children}
    </Link>
  );
}
