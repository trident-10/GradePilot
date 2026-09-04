import { mkdirSync, readFileSync } from "fs";
import { createRequire } from "module";

const require = createRequire(import.meta.url);
const puppeteer = require("puppeteer-core");

const [pdfArg, shotArg] = process.argv.slice(2);
const pdfPath = pdfArg ?? "C:\\Temp\\qa_transcript.pdf";
const shotDir = shotArg ?? null;
const pdfB64 = readFileSync(pdfPath).toString("base64");
if (shotDir) mkdirSync(shotDir, { recursive: true });
const report = { labels: {}, breakpoints: {} };

const SAMPLE = [
  { semester: "2024-2025 Güz", gpa: 2.37 },
  { semester: "2024-2025 Bahar", gpa: 2.5 },
  { semester: "2025-2026 Güz", gpa: 2.62 },
  { semester: "2025-2026 Bahar", gpa: 2.48 },
];

function shortSemesterLabel(semester) {
  const match = /^(\d{2})(\d{2})\s*[-–/]\s*(\d{2})(\d{2})\s*(.*)$/.exec(
    semester.trim(),
  );
  if (!match) return semester;
  const season = match[5].replace(/dönemi/i, "").trim();
  return `${match[2]}–${match[4]}${season ? ` ${season}` : ""}`;
}

function splitSemesterLabel(semester) {
  const match = /^(\d{2})(\d{2})\s*[-–/]\s*(\d{2})(\d{2})\s*(.*)$/.exec(
    semester.trim(),
  );
  if (!match) return { year: semester, season: "" };
  return {
    year: `${match[1]}${match[2]}–${match[3]}${match[4]}`,
    season: match[5].replace(/dönemi/i, "").trim(),
  };
}

report.labels.mobileCompact = SAMPLE.map((row) =>
  shortSemesterLabel(row.semester),
);
report.labels.desktopTwoLine = SAMPLE.map((row) =>
  splitSemesterLabel(row.semester),
);
report.labels.mobileMatchesSpec =
  report.labels.mobileCompact.join("|") ===
  "24–25 Güz|24–25 Bahar|25–26 Güz|25–26 Bahar";
report.labels.desktopNoTruncation = report.labels.desktopTwoLine.every(
  (parts) =>
    /^\d{4}–\d{4}$/.test(parts.year) &&
    (parts.season === "Güz" || parts.season === "Bahar"),
);

const browser = await puppeteer.launch({
  executablePath:
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  headless: true,
  args: ["--no-sandbox", "--window-size=1440,900"],
  defaultViewport: { width: 1440, height: 900 },
});
const page = await browser.newPage();
await page.emulateMediaFeatures([
  { name: "prefers-color-scheme", value: "light" },
]);

async function waitForText(text, timeout = 20000) {
  await page.waitForFunction(
    (needle) => document.body.innerText.includes(needle),
    { timeout },
    text,
  );
}

async function clickButton(text) {
  const clicked = await page.evaluate((needle) => {
    const btn = [...document.querySelectorAll("button")].find((b) =>
      (b.textContent || "").includes(needle),
    );
    if (!btn || btn.disabled) return false;
    btn.click();
    return true;
  }, text);
  if (!clicked) throw new Error(`Button not found: ${text}`);
}

try {
  await page.goto("http://localhost:3000/transkript", {
    waitUntil: "networkidle0",
  });
  await page.waitForFunction(
    () => typeof window.__gradePilotUploadFile === "function",
  );
  await page.evaluate(async (b64) => {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    window.__gradePilotUploadFile(
      new File([bytes], "qa_transcript.pdf", { type: "application/pdf" }),
    );
  }, pdfB64);

  await waitForText("GANO hesabında hangi değer kullanılıyor?");
  await page.evaluate(() => {
    const btn = [...document.querySelectorAll('button[role="option"]')].find(
      (b) => (b.textContent || "").includes("Kredi"),
    );
    btn?.click();
  });
  await clickButton("Devam et");
  await page.waitForFunction(
    () =>
      document.body.innerText.includes("Derslerini kontrol et") ||
      location.pathname.includes("genel-bakis"),
    { timeout: 25000 },
  );
  if (
    await page.evaluate(() =>
      document.body.innerText.includes("Derslerini kontrol et"),
    )
  ) {
    await clickButton("Bilgiler doğru, devam et");
  }
  await page.waitForFunction(() => location.pathname.includes("genel-bakis"));
  await waitForText("Dönemlere göre GANO");
  await page.waitForSelector("svg[aria-label^='Dönem GANO trendi']");

  for (const width of [390, 768, 1024, 1366, 1440, 1920]) {
    await page.setViewport({ width, height: 900 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await new Promise((r) => setTimeout(r, 350));
    const state = await page.evaluate(() => {
      const section = [...document.querySelectorAll("section")].find((node) =>
        node.textContent?.includes("Dönemlere göre GANO"),
      );
      const svg = document.querySelector(
        "svg[aria-label^='Dönem GANO trendi']",
      );
      const nestedChartBorder = section
        ? [...section.querySelectorAll("div")].some((div) => {
            if (!div.querySelector("svg[aria-label^='Dönem GANO trendi']")) {
              return false;
            }
            const style = getComputedStyle(div);
            return (
              style.borderTopWidth !== "0px" &&
              style.borderTopStyle !== "none" &&
              div !== section
            );
          })
        : true;
      const svgRect = svg?.getBoundingClientRect();
      const stage = svg?.closest(".gp-chart-stage");
      const stageRect = stage?.getBoundingClientRect();
      const sectionRect = section?.getBoundingClientRect();
      const texts = [...(svg?.querySelectorAll("text, tspan") ?? [])].map(
        (node) => node.textContent?.trim() ?? "",
      );
      const line = svg?.querySelector("path.gp-chart-line");
      return {
        hasSvg: !!svg,
        nestedChartBorder,
        fillsWidth:
          !!svgRect &&
          !!stageRect &&
          svgRect.width >= stageRect.width * 0.92,
        noOverflow:
          !!svgRect &&
          svgRect.left >= -1 &&
          svgRect.right <= window.innerWidth + 1,
        hasCompactLabels: texts.some((text) =>
          /^\d{2}[–-]\d{2}\s(Güz|Bahar)$/.test(text),
        ),
        hasFullYearLabels: texts.some((text) =>
          /^\d{4}[–-]\d{4}$/.test(text),
        ),
        hasSeasonLabels: texts.some(
          (text) => text === "Güz" || text === "Bahar",
        ),
        hasValueLabels: texts.some((text) => /^\d\.\d{2}$/.test(text)),
        yTicks: [0, 1, 2, 3, 4].every((tick) =>
          texts.includes(String(tick)),
        ),
        infoStroke: !!line && getComputedStyle(line).stroke.includes("rgb"),
        svgHeight: svgRect?.height ?? 0,
      };
    });
    report.breakpoints[width] = state;
    if (shotDir) {
      await page.screenshot({
        path: `${shotDir}\\chart-${width}.png`,
        fullPage: false,
      });
    }
  }

  report.ok =
    report.labels.mobileMatchesSpec &&
    report.labels.desktopNoTruncation &&
    report.breakpoints[390].noOverflow &&
    report.breakpoints[390].hasCompactLabels &&
    report.breakpoints[390].yTicks &&
    !report.breakpoints[1440].nestedChartBorder &&
    report.breakpoints[1440].fillsWidth &&
    report.breakpoints[1440].hasFullYearLabels &&
    report.breakpoints[1440].hasSeasonLabels &&
    report.breakpoints[1440].hasValueLabels &&
    report.breakpoints[1024].hasFullYearLabels;

  console.log(JSON.stringify(report, null, 2));
  await browser.close();
  process.exit(report.ok ? 0 : 1);
} catch (error) {
  console.error("CHART_E2E_FAIL", error);
  console.log("REPORT_PARTIAL", JSON.stringify(report, null, 2));
  await browser.close();
  process.exit(1);
}
