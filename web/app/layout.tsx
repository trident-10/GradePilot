import type { Metadata, Viewport } from "next";
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
    document.documentElement.dataset.theme = "light";
    document.documentElement.style.colorScheme = "light";
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

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  interactiveWidget: "resizes-content",
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
