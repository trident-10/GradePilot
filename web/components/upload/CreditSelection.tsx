"use client";

import { useState } from "react";

import {
  ContentFrame,
  GhostButton,
  PageHeader,
  PrimaryButton,
} from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { cx } from "@/lib/display";

export function CreditSelection() {
  const { creditOptions, isBusy, selectCreditOption, resetTranscript } =
    useAppState();
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <ContentFrame width="narrow">
      <PageHeader
        title="GANO hesabında hangi değer kullanılıyor?"
        description="Transkriptindeki Kredi veya AKTS değerlerinden uygun olanı seç."
      />

      {creditOptions.length === 0 ? (
        <p className="text-sm text-muted">
          Bu transkriptte kullanılabilecek bir kredi alanı tespit edilemedi.
          Farklı bir PDF ile tekrar dene.
        </p>
      ) : (
        <div
          className="grid gap-3 sm:grid-cols-2"
          role="listbox"
          aria-label="GANO ağırlığı"
        >
          {creditOptions.map((option) => {
            const active = selected === option.id;
            return (
              <button
                key={option.id}
                type="button"
                role="option"
                aria-selected={active}
                onClick={() => setSelected(option.id)}
                className={cx(
                  "flex w-full items-start justify-between gap-3 rounded-[12px] px-4 py-4 text-left transition-[background-color,box-shadow] duration-[180ms]",
                  active
                    ? "bg-accent-soft/80 shadow-[inset_3px_0_0_0_var(--accent)]"
                    : "bg-surface-muted/40 hover:bg-surface-muted/70",
                )}
              >
                <p className="text-base font-semibold text-ink">
                  {option.label}
                </p>
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

      <div className="flex flex-wrap gap-3">
        <PrimaryButton
          type="button"
          disabled={selected === null || isBusy}
          onClick={() => {
            if (selected !== null) {
              void selectCreditOption(selected);
            }
          }}
        >
          {isBusy ? "Hazırlanıyor…" : "Devam et"}
        </PrimaryButton>
        <GhostButton type="button" disabled={isBusy} onClick={resetTranscript}>
          İptal
        </GhostButton>
      </div>
    </ContentFrame>
  );
}
