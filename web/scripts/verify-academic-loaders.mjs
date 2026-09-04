import { mkdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { createRequire } from "module";

const require = createRequire(import.meta.url);
const puppeteer = require("puppeteer-core");

const pdfPath = process.argv[2] ?? "C:\\Temp\\qa_transcript.pdf";
const shotDir = process.argv[3] ?? join(process.cwd(), "tmp-loaders");
const pdfB64 = readFileSync(pdfPath).toString("base64");
mkdirSync(shotDir, { recursive: true });

const DELAY_MS = 1800;
const delayUrls = [
  "/api/transcripts/analyze",
  "/api/academic/target-plan",
  "/api/academic/manual-scenario",
  "/api/academic/future-semester",
  "/api/academic/required-semester-gpa",
  "/api/academic/course-impact",
];

const browser = await puppeteer.launch({
  executablePath:
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  headless: true,
  args: ["--no-sandbox", "--window-size=1280,900"],
  defaultViewport: { width: 1280, height: 900 },
});

const page = await browser.newPage();
const report = {};

async function waitForText(text, timeout = 25000) {
  await page.waitForFunction(
    (needle) =>
      document.body.innerText
        .toLocaleUpperCase("tr")
        .includes(needle.toLocaleUpperCase("tr")),
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
  await new Promise((resolve) => setTimeout(resolve, 250));
  await page.screenshot({ path: join(shotDir, `${name}.png`), fullPage: false });
}

function hasLoaderCopy(copy) {
  return page.evaluate(
    (needle) =>
      document.body.innerText
        .toLocaleUpperCase("tr")
        .includes(needle.toLocaleUpperCase("tr")),
    copy,
  );
}

try {
  await page.goto("http://localhost:3000/transkript", {
    waitUntil: "networkidle0",
  });
  await page.waitForFunction(
    () => typeof window.__gradePilotUploadFile === "function",
    { timeout: 10000 },
  );
  await page.setRequestInterception(true);
  page.on("request", (request) => {
    const hit = delayUrls.some((part) => request.url().includes(part));
    if (hit) {
      setTimeout(() => void request.continue().catch(() => undefined), DELAY_MS);
      return;
    }
    void request.continue();
  });

  await page.evaluate(async (b64) => {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    const file = new File([bytes], "sample_cankaya.pdf", {
      type: "application/pdf",
    });
    window.__gradePilotUploadFile(file);
  }, pdfB64);

  await waitForText("Transkript hazırlanıyor");
  report.transcriptTitle = true;
  report.transcriptPhrases =
    (await hasLoaderCopy("Transkript hazırlanıyor")) ||
    (await hasLoaderCopy("Dersler işleniyor")) ||
    (await hasLoaderCopy("Akademik görünüm hazırlanıyor"));
  report.noFakePercent = !(await page.evaluate(() =>
    /\d+\s*%/.test(document.body.innerText),
  ));
  report.transcriptVisual = await page.evaluate(() =>
    Boolean(document.querySelector(".gp-load-doc")),
  );
  await shoot("01-transcript-1280");

  await page.setViewport({ width: 390, height: 844 });
  await shoot("01b-transcript-390");
  await page.setViewport({ width: 1280, height: 900 });

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
  await page.waitForFunction(
    () => location.pathname.includes("genel-bakis"),
    { timeout: 20000 },
  );

  await clickNav("Planlayıcı");
  await page.waitForFunction(
    () => location.pathname.includes("planlayici"),
    { timeout: 15000 },
  );
  await waitForText("Planı Oluştur");
  await page.evaluate(() => {
    const target = document.querySelector('input[type="number"]');
    if (!target) throw new Error("target input missing");
    const proto = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      "value",
    );
    proto?.set?.call(target, "3.00");
    target.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await clickButton("Planı Oluştur");
  await waitForText("Plan hazırlanıyor");
  report.plannerLoader = true;
  report.plannerVisual = await page.evaluate(() =>
    Boolean(document.querySelector(".gp-load-marker")),
  );
  await shoot("02-planner");
  await waitForText("Tahmini GANO");

  await page.click('button[aria-controls="manual-plan-panel"]');
  await waitForText("Ders seç");
  await page.evaluate(() => {
    const open = [...document.querySelectorAll("button")].find((b) =>
      (b.getAttribute("aria-label") || "") === "Ders seç",
    );
    open?.click();
  });
  await page.waitForSelector("#manual-course-picker", { timeout: 5000 }).catch(() => null);
  await page.evaluate(() => {
    const box = document.querySelector("#manual-course-picker input[type='checkbox']");
    box?.click();
    const confirm = [...document.querySelectorAll("button")].find((b) =>
      (b.textContent || "").includes("Seçilenleri plana ekle"),
    );
    confirm?.click();
  });
  await clickButton("Planımı Hesapla");
  await waitForText("Sonuç hesaplanıyor");
  report.manualLoader = true;
  report.manualEllipsis = await page.evaluate(() =>
    Boolean(document.querySelector(".gp-load-ellipsis")),
  );
  await shoot("03-manual");
  await waitForText("Tahmini GANO");

  await clickNav("Gelecek Dönem");
  await waitForText("Simülasyonu Hesapla");
  await page.evaluate(() => {
    const name = document.querySelector('input[placeholder="Ders kodu veya adı"]');
    const proto = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      "value",
    );
    if (name) {
      proto?.set?.call(name, "Ders");
      name.dispatchEvent(new Event("input", { bubbles: true }));
    }
    const weight = document.querySelector("select[aria-label$='seç']");
    if (weight) {
      weight.value = "3";
      weight.dispatchEvent(new Event("change", { bubbles: true }));
    }
    const grade = [...document.querySelectorAll("select")].find(
      (el) => [...el.options].some((opt) => opt.value === "BB"),
    );
    if (grade) {
      grade.value = "BB";
      grade.dispatchEvent(new Event("change", { bubbles: true }));
    }
  });
  await clickButton("Simülasyonu Hesapla");
  await waitForText("Simülasyon hesaplanıyor");
  report.futureLoader = true;
  report.futurePlaceholders = await page.evaluate(() =>
    Boolean(document.querySelector(".gp-load-sink")),
  );
  await shoot("04-future");

  await clickNav("Hedef GANO");
  await waitForText("Gerekli Ortalamayı Hesapla");
  await page.evaluate(() => {
    const inputs = [...document.querySelectorAll('input[type="number"]')];
    const proto = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      "value",
    );
    if (inputs[0]) {
      proto?.set?.call(inputs[0], "3.00");
      inputs[0].dispatchEvent(new Event("input", { bubbles: true }));
    }
    if (inputs[1]) {
      proto?.set?.call(inputs[1], "20");
      inputs[1].dispatchEvent(new Event("input", { bubbles: true }));
    }
  });
  await clickButton("Gerekli Ortalamayı Hesapla");
  await waitForText("Gerekli ortalama hesaplanıyor");
  report.targetLoader = true;
  report.targetMarker = await page.evaluate(() =>
    Boolean(document.querySelector(".gp-load-target")),
  );
  await shoot("05-target");

  await clickNav("Dersler");
  await waitForText("Aktif ders");
  await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find((b) =>
      (b.textContent || "").includes("Etkiyi Gör"),
    );
    btn?.click();
  });
  await waitForText("Etki hesaplanıyor");
  report.impactLoader = true;
  await shoot("06-impact");

  await page.emulateMediaFeatures([
    { name: "prefers-color-scheme", value: "dark" },
    { name: "prefers-reduced-motion", value: "reduce" },
  ]);
  await page.evaluate(() => {
    document.documentElement.dataset.theme = "dark";
  });
  await page.goto("http://localhost:3000/transkript", {
    waitUntil: "networkidle0",
  });

  writeFileSync(
    join(shotDir, "report.json"),
    JSON.stringify(report, null, 2),
  );
  console.log(JSON.stringify(report, null, 2));
} finally {
  await browser.close();
}
