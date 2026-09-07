"use client";

import { useState } from "react";

import { GhostButton, PrimaryButton } from "@/components/ui";
import type { ErrorSeverity, UserFacingError } from "@/lib/errorModel";
import { cx } from "@/lib/display";

type ErrorCardProps = {
  error: UserFacingError;
  onRetry?: () => void;
  onStartOver: () => void;
};

const SEVERITY_STYLES: Record<
  ErrorSeverity,
  {
    label: string;
    card: string;
    badge: string;
    divider: string;
    marker: string;
    icon: string;
  }
> = {
  info: {
    label: "BİLGİ",
    card: "border-info/30 bg-info-soft/55",
    badge: "bg-info/12 text-info",
    divider: "border-info/20",
    marker: "marker:text-info",
    icon: "text-info",
  },
  warning: {
    label: "UYARI",
    card: "border-caution/35 bg-caution-soft/55",
    badge: "bg-caution/12 text-caution",
    divider: "border-caution/20",
    marker: "marker:text-caution",
    icon: "text-caution",
  },
  error: {
    label: "HATA",
    card: "border-danger/35 bg-danger-soft/55",
    badge: "bg-danger/12 text-danger",
    divider: "border-danger/20",
    marker: "marker:text-danger",
    icon: "text-danger",
  },
  success: {
    label: "BAŞARILI",
    card: "border-ok/30 bg-ok-soft/55",
    badge: "bg-ok/12 text-ok",
    divider: "border-ok/20",
    marker: "marker:text-ok",
    icon: "text-ok",
  },
};

function StatusIcon({ severity }: { severity: ErrorSeverity }) {
  if (severity === "warning") {
    return (
      <svg aria-hidden className="size-5" fill="none" viewBox="0 0 24 24">
        <path d="M12 3.5 21 20H3L12 3.5Z" stroke="currentColor" strokeWidth="1.7" />
        <path d="M12 9v5m0 2.75v.25" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" />
      </svg>
    );
  }

  if (severity === "success") {
    return (
      <svg aria-hidden className="size-5" fill="none" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.7" />
        <path d="m8 12 2.6 2.6L16.5 9" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" />
      </svg>
    );
  }

  return (
    <svg aria-hidden className="size-5" fill="none" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.7" />
      {severity === "info" ? (
        <path d="M12 10.5V17m0-10v.25" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" />
      ) : (
        <path d="M12 7v6m0 3.25v.25" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" />
      )}
    </svg>
  );
}

export function ErrorCard({ error, onRetry, onStartOver }: ErrorCardProps) {
  const titleId = `error-title-${error.errorCode}`;
  const copyStatusId = `copy-status-${error.errorCode}`;
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "failed">("idle");
  const styles = SEVERITY_STYLES[error.severity];

  async function copyErrorCode() {
    try {
      if (!navigator.clipboard) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(error.errorCode);
      setCopyStatus("copied");
    } catch {
      setCopyStatus("failed");
    }
  }

  return (
    <section
      aria-labelledby={titleId}
      aria-live={error.severity === "error" ? "assertive" : "polite"}
      className={cx(
        "w-full rounded-[16px] border p-5 text-left shadow-[var(--shadow-sm)] sm:p-6",
        styles.card,
      )}
      role={error.severity === "error" ? "alert" : "status"}
      tabIndex={-1}
    >
      <span
        className={cx(
          "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold tracking-[0.08em]",
          styles.badge,
        )}
      >
        <StatusIcon severity={error.severity} />
        {styles.label}
      </span>
      <h1
        id={titleId}
        className="mt-3 text-xl font-bold tracking-[-0.025em] text-ink"
      >
        {error.title}
      </h1>
      <p className="mt-2 max-w-xl text-sm leading-6 text-muted">
        {error.description}
      </p>

      <div className={cx("mt-5 border-t pt-4", styles.divider)}>
        <h2 className="text-sm font-semibold text-ink">
          Ne yapabilirsiniz?
        </h2>
        <ul className={cx("mt-2 space-y-1.5 pl-5 text-sm leading-6 text-muted", styles.marker)}>
          {error.suggestions.map((suggestion) => (
            <li key={suggestion}>{suggestion}</li>
          ))}
        </ul>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-2 text-xs font-medium text-muted">
        <span>
          Destek kodu: <span className="font-semibold text-ink">{error.errorCode}</span>
        </span>
        <button
          type="button"
          aria-describedby={copyStatusId}
          aria-label={`${error.errorCode} destek kodunu kopyala`}
          className={cx(
            "inline-flex min-h-10 items-center gap-1.5 rounded-[9px] px-2.5 font-semibold outline-none hover:bg-surface/65 focus-visible:ring-2 focus-visible:ring-current focus-visible:ring-offset-2",
            styles.icon,
          )}
          onClick={() => void copyErrorCode()}
        >
          <svg aria-hidden className="size-4" fill="none" viewBox="0 0 24 24">
            <rect x="8" y="8" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="1.7" />
            <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" stroke="currentColor" strokeWidth="1.7" />
          </svg>
          Kopyala
        </button>
        <span id={copyStatusId} aria-live="polite">
          {copyStatus === "copied" ? "Kopyalandı" : null}
          {copyStatus === "failed" ? "Kopyalanamadı" : null}
        </span>
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        {error.retryable && onRetry ? (
          <PrimaryButton
            className="w-full sm:w-auto"
            onClick={onRetry}
            type="button"
          >
            Tekrar Dene
          </PrimaryButton>
        ) : null}
        <GhostButton
          className="w-full sm:w-auto"
          onClick={onStartOver}
          type="button"
        >
          Yeni PDF Seç
        </GhostButton>
      </div>
    </section>
  );
}
