"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";

import { AmbientBackground } from "@/components/AmbientBackground";
import { ProductSignature } from "@/components/ProductSignature";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAppState } from "@/context/AppStateContext";
import { cx } from "@/lib/display";

const PAGE_TITLES: Record<string, string> = {
  "/genel-bakis": "Genel Bakış",
  "/dersler": "Dersler",
  "/planlayici": "Planlayıcı",
  "/gelecek-donem": "Gelecek Dönem",
  "/hedef-gano": "Hedef GANO",
  "/transkript": "Transkript",
};

const NAV_GROUPS = [
  {
    label: "Akademik Durum",
    items: [
      { href: "/genel-bakis", label: "Genel Bakış" },
      { href: "/dersler", label: "Dersler" },
    ],
  },
  {
    label: "Planlama",
    items: [
      { href: "/planlayici", label: "Planlayıcı" },
      { href: "/gelecek-donem", label: "Gelecek Dönem" },
      { href: "/hedef-gano", label: "Hedef GANO" },
    ],
  },
  {
    label: "Veriler",
    items: [{ href: "/transkript", label: "Transkript" }],
  },
] as const;

/** Full application chrome — only after a transcript is ready. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { resetTranscript } = useAppState();
  const [navOpen, setNavOpen] = useState(false);
  const [desktop, setDesktop] = useState(true);
  const navId = useId();
  const drawerRef = useRef<HTMLElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const drawerHidden = !desktop && !navOpen;

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)");
    const apply = () => setDesktop(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  function closeNav() {
    setNavOpen(false);
  }

  useEffect(() => {
    if (!navOpen || desktop) return;
    const drawer = drawerRef.current;
    const focusable = drawer
      ? [
          ...drawer.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled])',
          ),
        ]
      : [];
    const first = focusable[0];
    const last = focusable.at(-1);
    const focusFrame = window.requestAnimationFrame(() => first?.focus());

    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        menuButtonRef.current?.focus();
        setNavOpen(false);
        return;
      }
      if (event.key !== "Tab" || !first || !last) return;
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => {
      window.cancelAnimationFrame(focusFrame);
      window.removeEventListener("keydown", onKey);
    };
  }, [desktop, navOpen]);

  const nav = (
    <nav aria-label="Ana menü" className="flex flex-col gap-5">
      {NAV_GROUPS.map((group) => (
        <div key={group.label}>
          <p className="px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
            {group.label}
          </p>
          <div className="mt-1.5 space-y-0.5">
            {group.items.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={closeNav}
                  aria-current={active ? "page" : undefined}
                  className={cx(
                    "relative block rounded-[8px] px-3 py-1.5 text-sm transition-[background-color,color,box-shadow] duration-[180ms] ease-out",
                    active
                      ? "bg-info-soft/80 font-semibold text-ink before:absolute before:inset-y-1.5 before:left-0 before:w-[3px] before:rounded-full before:bg-accent"
                      : "font-medium text-muted hover:bg-bg hover:text-ink",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );

  return (
    <div className="relative min-h-dvh bg-bg">
      <AmbientBackground />
      <div className="relative z-[1] mx-auto flex min-h-dvh w-full max-w-[1600px]">
        {navOpen ? (
          <button
            type="button"
            className="fixed inset-0 z-40 bg-ink/35 backdrop-blur-[1px] md:hidden"
            aria-label="Menüyü kapat"
            onClick={() => {
              menuButtonRef.current?.focus();
              setNavOpen(false);
            }}
          />
        ) : null}

        <aside
          ref={drawerRef}
          id={navId}
          className={cx(
            "fixed inset-y-0 left-0 z-50 flex w-56 flex-col border-r border-rule/80 bg-surface/92 px-2.5 pb-[max(1rem,env(safe-area-inset-bottom))] pt-[max(1rem,env(safe-area-inset-top))] shadow-[var(--shadow-sm)] backdrop-blur-md transition-transform duration-200 ease-out md:static md:z-0 md:flex md:w-48 md:shrink-0 md:translate-x-0 md:py-4 md:shadow-none",
            navOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          )}
          aria-hidden={drawerHidden}
          inert={drawerHidden || undefined}
        >
          <div className="flex items-center px-3">
            <Link
              href="/genel-bakis"
              onClick={closeNav}
              className="inline-flex items-center gap-2 font-display text-[1.08rem] font-semibold tracking-[-0.04em] text-ink"
            >
              <span className="size-2 rounded-[3px] bg-accent" aria-hidden />
              GradePilot
            </Link>
          </div>
          <div className="mt-6 min-h-0 flex-1 overflow-y-auto">{nav}</div>
          <div className="mt-4 space-y-3 border-t border-rule px-2.5 pt-3">
            <div className="flex items-center gap-2 px-0.5 text-xs">
              <span className="size-1.5 rounded-full bg-ok" aria-hidden />
              <p className="font-medium text-ink">Transkript hazır</p>
            </div>
            <button
              type="button"
              onClick={() => {
                resetTranscript();
                router.push("/transkript");
              }}
              className="px-0.5 text-xs font-medium text-muted underline-offset-2 transition-colors hover:text-accent-deep hover:underline"
            >
              Yeni transkript yükle
            </button>
            <ProductSignature compact />
          </div>
        </aside>

        <div className="flex min-h-dvh min-w-0 flex-1 flex-col">
          <div className="flex shrink-0 items-center justify-between border-b border-rule/80 bg-surface/90 px-4 pb-2.5 pt-[max(0.625rem,env(safe-area-inset-top))] backdrop-blur-md md:hidden">
            <Link
              href="/genel-bakis"
              onClick={closeNav}
              className="inline-flex items-center gap-2 font-display text-base font-semibold tracking-[-0.04em] text-ink"
            >
              <span className="size-2 rounded-[3px] bg-accent" aria-hidden />
              GradePilot
            </Link>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <button
                ref={menuButtonRef}
                type="button"
                className="inline-flex size-11 items-center justify-center rounded-[9px] border border-rule bg-surface text-ink transition-[transform,background-color,border-color] duration-[180ms] hover:-translate-y-px hover:bg-surface-muted active:translate-y-0"
                aria-expanded={navOpen}
                aria-controls={navId}
                aria-label={navOpen ? "Menüyü kapat" : "Menüyü aç"}
                title={navOpen ? "Menüyü kapat" : "Menüyü aç"}
                onClick={() => setNavOpen((open) => !open)}
              >
                <span className="sr-only">Menü</span>
                <svg
                  aria-hidden
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d={
                      navOpen
                        ? "M6 6l12 12M18 6 6 18"
                        : "M4 7h16M4 12h16M4 17h16"
                    }
                    stroke="currentColor"
                    strokeWidth="1.7"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>
          </div>
          <header className="hidden h-12 shrink-0 items-center justify-between border-b border-rule/80 bg-surface/80 px-6 backdrop-blur-md md:flex">
            <p className="text-sm font-medium text-ink">
              {PAGE_TITLES[pathname] ?? "GradePilot"}
            </p>
            <div className="flex items-center gap-3">
              <p className="flex items-center gap-1.5 text-xs text-muted">
                <span className="size-1.5 rounded-full bg-ok" aria-hidden />
                Transkript hazır
              </p>
              <ThemeToggle />
            </div>
          </header>
          {/*
            Avoid overflow-x-clip here: with a non-visible overflow-x it can force
            overflow-y to auto and trap vertical scrolling inside main.
            min-w-0 already contains flex overflow; pages scroll with the document.
          */}
          <main
            key={pathname}
            className="gp-page-enter min-w-0 flex-1 px-4 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-4 sm:px-5 md:px-6 md:py-5"
          >
            {children}
          </main>
          <footer className="shrink-0 border-t border-rule/70 px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 md:hidden">
            <ProductSignature />
          </footer>
        </div>
      </div>
    </div>
  );
}

/** First-run / onboarding chrome — no app sidebar. */
export function EntryShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-dvh bg-bg">
      <AmbientBackground />
      <div className="relative z-[1] mx-auto flex min-h-dvh w-full max-w-3xl flex-col px-4 pb-[max(2rem,env(safe-area-inset-bottom))] pt-[max(2rem,env(safe-area-inset-top))] sm:px-6 md:py-14">
        <div className="mb-8 flex items-center justify-between md:mb-10">
          <p className="inline-flex items-center gap-2 font-display text-lg font-semibold tracking-[-0.04em] text-ink">
            <span className="size-2.5 rounded-[3px] bg-accent" aria-hidden />
            GradePilot
          </p>
          <ThemeToggle />
        </div>
        <div className="gp-page-enter flex flex-1 flex-col">{children}</div>
        <div className="mt-10">
          <ProductSignature />
        </div>
      </div>
    </div>
  );
}
