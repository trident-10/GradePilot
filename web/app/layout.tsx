import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Sora } from "next/font/google";

import { AppStateProvider } from "@/context/AppStateContext";

import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600", "700"],
});

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin", "latin-ext"],
  weight: ["500", "600", "700"],
});

const themeBootScript = `
  (() => {
    try {
      const saved = localStorage.getItem("gradepilot-theme");
      const theme = saved === "light" || saved === "dark"
        ? saved
        : (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      document.documentElement.dataset.theme = theme;
      document.documentElement.style.colorScheme = theme;
    } catch {
      const theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      document.documentElement.dataset.theme = theme;
      document.documentElement.style.colorScheme = theme;
    }
  })();
`;

export const metadata: Metadata = {
  title: {
    default: "GradePilot | Transkript analizi ve GANO planlama",
    template: "%s | GradePilot",
  },
  description:
    "Üniversite transkriptini yükle, GANO’nu incele ve hedef ortalaman için akademik senaryolar oluştur.",
  applicationName: "GradePilot",
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="tr"
      className={`${jakarta.variable} ${sora.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBootScript }} />
      </head>
      <body className="min-h-full bg-bg font-sans text-ink">
        <AppStateProvider>{children}</AppStateProvider>
      </body>
    </html>
  );
}
