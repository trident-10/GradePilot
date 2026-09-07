import type { ReactNode } from "react";

import { ContentFrame, PageHeader } from "@/components/ui";

const STEPS = [
  { label: "Transkript", state: "complete" },
  { label: "Doğrulama", state: "current" },
  { label: "Analiz", state: "upcoming" },
  { label: "Sonuçlar", state: "upcoming" },
] as const;

export function TranscriptValidationFrame({ children }: { children: ReactNode }) {
  return (
    <ContentFrame
      width="narrow"
      className="gp-upload-enter space-y-6 sm:space-y-7"
    >
      <PageHeader
        title="Transkript Doğrulama"
        description="Kredi seçimini tamamlayıp derslerini kontrol et."
      />

      <ol
        className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4"
        aria-label="Analiz ilerlemesi"
      >
        {STEPS.map((step, index) => (
          <li
            key={step.label}
            aria-current={step.state === "current" ? "step" : undefined}
            className="flex min-w-0 items-center gap-2 rounded-[10px] bg-surface/70 px-2.5 py-2 text-muted"
          >
            <span
              className={
                step.state === "complete"
                  ? "flex size-5 shrink-0 items-center justify-center rounded-full bg-ok-soft text-[11px] font-bold text-ok"
                  : step.state === "current"
                    ? "flex size-5 shrink-0 items-center justify-center rounded-full bg-accent text-[10px] text-on-accent"
                    : "flex size-5 shrink-0 items-center justify-center rounded-full border border-rule text-[10px] text-faint"
              }
              aria-hidden
            >
              {step.state === "complete" ? "✓" : step.state === "current" ? "●" : "○"}
            </span>
            <span className="min-w-0 truncate">
              {index + 1}. {step.label}
            </span>
          </li>
        ))}
      </ol>

      {children}

      <p className="flex items-start gap-2 border-t border-rule/80 pt-4 text-xs leading-5 text-faint">
        <span aria-hidden>🔒</span>
        <span>
          Transkript yalnızca analiz amacıyla işlenir ve işlem tamamlandıktan
          sonra sistemden kaldırılır.
        </span>
      </p>
    </ContentFrame>
  );
}
