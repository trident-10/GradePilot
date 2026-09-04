import Link from "next/link";

import { cx } from "@/lib/display";

const legalLinkClass =
  "text-[11px] text-faint transition-colors duration-[180ms] hover:text-ink";

export function ProductSignature({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={cx(
        "flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[11px] leading-4 text-faint",
        compact ? "justify-start" : "justify-center sm:justify-between",
      )}
    >
      <p>Mete Artun Altay · © 2026 GradePilot</p>
      <span className="inline-flex flex-wrap items-center gap-x-2.5 gap-y-1">
        <Link href="/gizlilik" className={legalLinkClass}>
          Gizlilik
        </Link>
        <Link href="/kullanim-kosullari" className={legalLinkClass}>
          Kullanım Koşulları
        </Link>
        <a
          href="https://github.com/trident-10"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="GitHub"
          className="inline-flex size-7 items-center justify-center rounded-md text-muted transition-colors duration-[180ms] hover:bg-surface-muted hover:text-ink"
        >
          <GitHubIcon />
        </a>
        <a
          href="https://www.linkedin.com/in/mete-artun-altay-243a7a289"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="LinkedIn"
          className="inline-flex size-7 items-center justify-center rounded-md text-muted transition-colors duration-[180ms] hover:bg-surface-muted hover:text-ink"
        >
          <LinkedInIcon />
        </a>
      </span>
    </div>
  );
}

function GitHubIcon() {
  return (
    <svg aria-hidden width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.46-1.16-1.12-1.47-1.12-1.47-.92-.63.07-.62.07-.62 1 .07 1.54 1.04 1.54 1.04.9 1.54 2.36 1.1 2.94.84.09-.65.35-1.1.64-1.35-2.22-.25-4.56-1.11-4.56-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.56 9.56 0 0 1 5 0c1.9-1.29 2.74-1.02 2.74-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.94.36.31.68.92.68 1.86v2.76c0 .26.18.58.69.48A10 10 0 0 0 12 2Z" />
    </svg>
  );
}

function LinkedInIcon() {
  return (
    <svg aria-hidden width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M4.98 3.5A2.5 2.5 0 1 1 5 8.5a2.5 2.5 0 0 1-.02-5ZM5 9.75H1.98V21H5V9.75ZM9.25 9.75H6.3V21h2.95v-5.7c0-1.5.28-2.96 2.15-2.96 1.84 0 1.87 1.72 1.87 3.06V21H16.2v-6.26c0-3.08-.66-5.45-4.27-5.45-1.73 0-2.9.95-3.37 1.85h-.05V9.75Z" />
    </svg>
  );
}
