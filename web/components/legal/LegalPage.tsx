"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { EntryShell } from "@/components/AppShell";
import { ContentFrame } from "@/components/ui";

export function LegalPage({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <EntryShell>
      <ContentFrame width="default" className="space-y-6">
        <p className="text-xs text-faint">
          <Link
            href="/transkript"
            className="transition-colors duration-[180ms] hover:text-ink"
          >
            ← GradePilot
          </Link>
        </p>
        <h1 className="font-display text-[1.6rem] font-semibold leading-[1.15] tracking-[-0.035em] text-ink sm:text-[1.85rem]">
          {title}
        </h1>
        <div className="space-y-5 text-[15px] leading-7 text-muted">{children}</div>
      </ContentFrame>
    </EntryShell>
  );
}

export function LegalHeading({ children }: { children: ReactNode }) {
  return (
    <h2 className="pt-3 font-display text-base font-semibold tracking-[-0.02em] text-ink">
      {children}
    </h2>
  );
}

export function LegalList({ children }: { children: ReactNode }) {
  return <ul className="list-disc space-y-1.5 pl-5">{children}</ul>;
}
