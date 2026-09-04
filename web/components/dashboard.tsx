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
        "rounded-[14px] p-4 md:p-5",
        variant === "metric" &&
          "bg-surface/80 shadow-[var(--shadow-sm)]",
        variant === "analytics" &&
          "bg-surface/85 shadow-[var(--shadow-sm)]",
        variant === "table" &&
          "overflow-hidden bg-surface/90 p-0 shadow-[var(--shadow-sm)]",
        variant === "action" &&
          "bg-accent-soft/40 shadow-[var(--shadow-sm)]",
        variant === "note" &&
          "border border-info/20 bg-info-soft/70 p-3.5 text-sm leading-6 text-info",
        variant === "result" &&
          "border border-ok/20 bg-ok-soft/50 shadow-[var(--shadow-sm)]",
        className,
      )}
    >
      {title || action ? (
        <div
          className={cx(
            "flex items-center justify-between gap-3",
            variant === "table" && "px-4 pt-4",
          )}
        >
          {title ? (
            <h2 className="font-display text-[0.95rem] font-semibold tracking-[-0.02em] text-ink md:text-base">
              {title}
            </h2>
          ) : (
            <span />
          )}
          {action}
        </div>
      ) : null}
      <div
        className={cx(
          title || action ? (variant === "table" ? "mt-3" : "mt-3.5") : "",
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
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  strong?: boolean;
}) {
  return (
    <div
      className={cx(
        "rounded-[14px] bg-surface/80 px-4 py-3.5 shadow-[var(--shadow-sm)]",
        strong &&
          "bg-[radial-gradient(120%_90%_at_0%_0%,color-mix(in_srgb,var(--accent)_14%,transparent),transparent_55%)]",
      )}
    >
      <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-faint">
        {label}
      </p>
      <p
        className={cx(
          "mt-1.5 font-display font-semibold tabular-nums tracking-[-0.04em] text-ink",
          strong
            ? "text-[2.15rem] leading-none md:text-[2.55rem]"
            : "text-xl leading-none md:text-[1.65rem]",
        )}
      >
        {value}
      </p>
      {hint ? <p className="mt-1.5 text-xs text-muted">{hint}</p> : null}
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
      className="flex items-center justify-between gap-2 rounded-[10px] px-3 py-2.5 text-sm font-medium text-ink transition-colors duration-[180ms] hover:bg-surface/80"
    >
      {children}
    </Link>
  );
}
