"use client";

import { useState } from "react";

import {
  GhostButton,
  InlineNotice,
  PrimaryButton,
  Section,
} from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { cx } from "@/lib/display";
import { TranscriptValidationFrame } from "@/components/upload/TranscriptValidationFrame";

function optionLabel(optionId: string) {
  if (optionId === "credit") return "Kredi sistemi";
  if (optionId === "ects") return "AKTS sistemi";
  return "Diğer sistem";
}

export function CreditSelection() {
  const { creditOptions, isBusy, error, selectCreditOption, resetTranscript } =
    useAppState();
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <TranscriptValidationFrame>
      <Section
        title="Okulun GANO'su hangi sistemle hesaplanıyor?"
        description="Bir seçim yaparak devam edin."
      >
        <div className="space-y-5">
          {error ? <div role="alert"><InlineNotice tone="caution">{error.description}</InlineNotice></div> : null}
          {creditOptions.length === 0 ? (
            <p className="text-sm leading-6 text-muted">
              GANO hesabında kullanılacak kredi sütunu bulunamadı. Farklı
              bir PDF ile tekrar deneyebilirsiniz.
            </p>
          ) : (
            <div
              className="grid gap-3 sm:grid-cols-2"
              role="group"
              aria-label="GANO hesaplama sistemi"
            >
              {creditOptions.map((option) => {
                const active = selected === option.id;
                const label = optionLabel(option.id);
                return (
                  <button
                    key={option.id}
                    type="button"
                    aria-pressed={active}
                    onClick={() => setSelected(option.id)}
                    className={cx(
                      "flex min-h-20 w-full items-center justify-between gap-3 rounded-[12px] border px-4 py-4 text-left transition-[background-color,border-color,box-shadow] duration-[180ms]",
                      active
                        ? "border-accent/45 bg-accent-soft/80 shadow-[inset_3px_0_0_0_var(--accent)]"
                        : "border-rule/80 bg-surface-muted/40 hover:border-accent/25 hover:bg-surface-muted/70",
                    )}
                  >
                    <span className="min-w-0">
                      <span className="block text-base font-semibold text-ink">
                        {label}
                      </span>
                    </span>
                    <span
                      className={cx(
                        "mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border text-[11px] font-bold",
                        active
                          ? "border-accent bg-accent text-on-accent"
                          : "border-rule text-transparent",
                      )}
                      aria-hidden
                    >
                      ✓
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          <p className="text-sm text-muted">
            Emin değilseniz üniversitenizin not yönetmeliğine bakın.
          </p>
        </div>
      </Section>

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <PrimaryButton
          type="button"
          className="w-full sm:w-auto"
          disabled={selected === null || isBusy}
          onClick={() => {
            if (selected !== null) {
              void selectCreditOption(selected);
            }
          }}
        >
          {isBusy ? "Hazırlanıyor…" : "Analize Devam Et"}
        </PrimaryButton>
        <GhostButton
          type="button"
          className="w-full sm:w-auto"
          disabled={isBusy}
          onClick={resetTranscript}
        >
          Yeni PDF Seç
        </GhostButton>
      </div>
    </TranscriptValidationFrame>
  );
}
