"use client";

import { useSyncExternalStore } from "react";

type Theme = "light" | "dark";

function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  window.dispatchEvent(new Event("gradepilot-theme-change"));
}

function currentTheme(): Theme {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

function subscribe(onChange: () => void) {
  window.addEventListener("gradepilot-theme-change", onChange);
  return () => window.removeEventListener("gradepilot-theme-change", onChange);
}

export function ThemeToggle() {
  const activeTheme = useSyncExternalStore(subscribe, currentTheme, () => "light");

  const nextTheme: Theme = activeTheme === "light" ? "dark" : "light";
  const label =
    nextTheme === "dark" ? "Koyu temaya geç" : "Açık temaya geç";

  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={() => {
        applyTheme(nextTheme);
      }}
      className="group inline-flex size-11 shrink-0 items-center justify-center rounded-[9px] border border-rule bg-surface text-muted shadow-[var(--shadow-sm)] transition-[transform,background-color,border-color,color,box-shadow] duration-[180ms] hover:-translate-y-px hover:border-accent/35 hover:bg-accent-soft/50 hover:text-accent-deep hover:shadow-[var(--shadow-md)] active:translate-y-0 active:shadow-[var(--shadow-sm)] sm:size-9"
    >
      <span className="sr-only">{label}</span>
      {activeTheme === "light" ? (
        <MoonIcon />
      ) : (
        <SunIcon />
      )}
    </button>
  );
}

function MoonIcon() {
  return (
    <svg
      aria-hidden
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      className="transition-transform duration-[180ms] group-hover:-rotate-6"
    >
      <path
        d="M20 15.2A8.3 8.3 0 0 1 8.8 4a8.5 8.5 0 1 0 11.2 11.2Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg
      aria-hidden
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      className="transition-transform duration-[180ms] group-hover:rotate-12"
    >
      <circle cx="12" cy="12" r="3.5" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M12 2.5v2M12 19.5v2M21.5 12h-2M4.5 12h-2M18.72 5.28l-1.42 1.42M6.7 17.3l-1.42 1.42M18.72 18.72l-1.42-1.42M6.7 6.7 5.28 5.28"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}
