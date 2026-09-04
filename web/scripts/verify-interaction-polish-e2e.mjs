import { mkdirSync, readFileSync } from "fs";
import { createRequire } from "module";

const require = createRequire(import.meta.url);
const puppeteer = require("puppeteer-core");

const [pdfArg, shotArg] = process.argv.slice(2);
const pdfPath = pdfArg ?? "C:\\Temp\\qa_transcript.pdf";
const shotDir = shotArg ?? null;
const pdfB64 = readFileSync(pdfPath).toString("base64");
if (shotDir) mkdirSync(shotDir, { recursive: true });
const report = {};

const browser = await puppeteer.launch({
  executablePath:
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  headless: true,
  args: ["--no-sandbox", "--window-size=1280,900"],
  defaultViewport: { width: 1280, height: 900 },
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
  if (!clicked) throw new Error(`Button not found/enabled: ${text}`);
}

async function clickNav(label) {
  const clicked = await page.evaluate((needle) => {
    const link = [...document.querySelectorAll("a")].find(
      (a) => a.textContent?.trim() === needle,
    );
    if (!link) return false;
    link.click();
    return true;
  }, label);
  if (!clicked) throw new Error(`Nav link not found: ${label}`);
}

async function shoot(name) {
  if (!shotDir) return;
  await new Promise((resolve) => setTimeout(resolve, 250));
  await page.screenshot({
    path: `${shotDir}\\${name}.png`,
    fullPage: true,
  });
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
  await waitForText("Dönem performansı");

  report.chartHighlights = await page.evaluate(() => {
    const text = document.body.innerText;
    return (
      text.includes("Son dönem") &&
      text.includes("En yüksek dönem") &&
      text.includes("Önceki dönem")
    );
  });
  report.chartInfoLine = await page.evaluate(() => {
    const line = document.querySelector("svg path.gp-chart-line");
    return !!line && getComputedStyle(line).stroke.includes("rgb");
  });
  report.fullDesktopLabels = await page.evaluate(() => {
    const labels = [...document.querySelectorAll("svg text")]
      .map((node) => node.textContent?.trim() ?? "")
      .filter((text) => /\d{4}.+\d{4}.+(Güz|Bahar)/i.test(text));
    return labels.length >= 4;
  });
  await shoot("01-overview-chart-1280");

  await page.setViewport({ width: 390, height: 844 });
  await new Promise((r) => setTimeout(r, 300));
  report.mobileCompactLabels = await page.evaluate(() => {
    const labels = [...document.querySelectorAll("svg text")]
      .map((node) => node.textContent?.trim() ?? "")
      .filter((text) => /^\d{2}[–-]\d{2}\s/.test(text));
    return labels.length >= 2;
  });
  report.mobileChartNoOverflow = await page.evaluate(() => {
    const svg = document.querySelector("svg[aria-label^='Dönem GANO trendi']");
    if (!svg) return false;
    const rect = svg.getBoundingClientRect();
    return rect.width <= window.innerWidth + 1 && rect.left >= -1;
  });
  await shoot("02-overview-chart-390");
  await page.setViewport({ width: 1280, height: 900 });

  await clickNav("Gelecek Dönem");
  await page.waitForFunction(() => location.pathname.includes("/gelecek-donem"));
  report.creditLabel = await page.evaluate(() =>
    document.body.innerText.includes("Kredi"),
  );
  const weightSelect = await page.$('select[aria-label="Kredi seç"]');
  if (!weightSelect) throw new Error("Weight select missing");
  await weightSelect.select("4");
  report.commonWeightNoCustomInput = await page.evaluate(
    () =>
      !document.querySelector('input[aria-label="Özel kredi değeri"]') &&
      [...document.querySelectorAll('select[aria-label="Kredi seç"]')].some(
        (select) => select.value === "4",
      ),
  );
  await weightSelect.select("other");
  report.otherRevealsInput = await page.evaluate(
    () => !!document.querySelector('input[aria-label="Özel kredi değeri"]'),
  );
  await page.type('input[aria-label="Özel kredi değeri"]', "12");
  report.customWeightValue = await page.evaluate(
    () =>
      document.querySelector('input[aria-label="Özel kredi değeri"]')?.value ===
      "12",
  );
  await shoot("03-future-weight-other");

  await page.setViewport({ width: 390, height: 844 });
  report.mobileRemoveCopy = await page.evaluate(() =>
    document.body.innerText.includes("Satırı kaldır"),
  );
  await shoot("04-future-mobile");
  await page.setViewport({ width: 1280, height: 900 });

  await clickNav("Planlayıcı");
  await page.waitForFunction(() => location.pathname.includes("/planlayici"));
  await clickButton("Kendi Planım");
  await page.click('button[aria-label="Ders seç"]');
  await page.waitForSelector("#manual-course-picker");
  report.pickerOpened = true;
  report.quickFilters = await page.evaluate(() => {
    const text = document.body.innerText;
    return (
      text.includes("Tümü") &&
      text.includes("DD/DC") &&
      text.includes("CC/CB") &&
      text.includes("BB ve üzeri")
    );
  });
  await page.evaluate(() => {
    const boxes = [
      ...document.querySelectorAll('#manual-course-picker input[type="checkbox"]'),
    ];
    boxes.slice(0, 2).forEach((box) => {
      if (!box.checked) box.click();
    });
  });
  await clickButton("Seçilenleri plana ekle");
  report.multiSelectAdded = await page.evaluate(() => {
    const match = document.body.innerText.match(
      /Seçtiğin değişiklikler · (\d+) ders/,
    );
    return match ? Number(match[1]) >= 2 : false;
  });
  report.nextGradeDefault = await page.evaluate(() => {
    const selects = [
      ...document.querySelectorAll('select[aria-label$="hedef notu"]'),
    ];
    return selects.length >= 2 && selects.every((select) => !!select.value);
  });
  await shoot("05-manual-picker");

  console.log(JSON.stringify(report, null, 2));
  await browser.close();
  process.exit(0);
} catch (error) {
  console.error("E2E_FAIL", error);
  console.log(
    "PAGE_TEXT:\n",
    await page.evaluate(() => document.body.innerText).catch(() => ""),
  );
  console.log("REPORT_PARTIAL", JSON.stringify(report, null, 2));
  await browser.close();
  process.exit(1);
}
