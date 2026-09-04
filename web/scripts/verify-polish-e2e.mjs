import { mkdirSync, readFileSync } from "fs";
import { createRequire } from "module";

const require = createRequire(import.meta.url);
const puppeteer = require("puppeteer-core");

const [pdfArg, shotArg] = process.argv.slice(2);
const pdfPath = pdfArg ?? "C:\\Temp\\sample_cankaya.pdf";
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

async function shoot(name, fullPage = true) {
  if (!shotDir) return;
  await new Promise((resolve) => setTimeout(resolve, 350));
  await page.screenshot({
    path: `${shotDir}\\${name}.png`,
    fullPage,
  });
}

/** Sidebar group labels are CSS-uppercased, so compare case-insensitively. */
async function hasSidebarNav() {
  return page.evaluate(() =>
    Boolean(document.querySelector('nav[aria-label="Ana menü"]')),
  );
}

async function menuButtonVisible() {
  return page.evaluate(() =>
    [...document.querySelectorAll("button")].some(
      (b) => b.textContent?.trim() === "Menü" && b.offsetParent !== null,
    ),
  );
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

try {
  await page.goto("http://localhost:3000/transkript", {
    waitUntil: "networkidle0",
  });
  await waitForText("Transkriptini yükle, akademik durumunu planla.");
  report.onboardingHeadline = true;
  report.noSidebarOnEntry = !(await hasSidebarNav());
  report.termsGate = await page.evaluate(() => {
    const text = document.body.innerText;
    return (
      text.includes("Devam etmeden önce") &&
      text.includes("Gizlilik Bildirimi") &&
      text.includes("Kullanım Koşulları")
    );
  });
  await page.evaluate(() => {
    document.getElementById("transcript-terms-ack")?.click();
  });
  await clickButton("Devam Et");
  await waitForText("Transkript Yükle");
  report.uploadCta = await page.evaluate(() =>
    document.body.innerText.includes("Transkript Yükle"),
  );
  report.dragDropCopy = await page.evaluate(() =>
    document.body.innerText.includes("Dosyanı buraya sürükle"),
  );
  report.entryLimitsCopy = await page.evaluate(() =>
    document.body.innerText.includes("Maks. 10 MB"),
  );
  await shoot("01-onboarding-1280");
  await page.setViewport({ width: 390, height: 844 });
  await shoot("02-onboarding-390");
  await page.setViewport({ width: 1280, height: 900 });

  await page.waitForFunction(
    () => typeof window.__gradePilotUploadFile === "function",
    { timeout: 10000 },
  );
  await page.setRequestInterception(true);
  let delayedInitialAnalyze = false;
  page.on("request", (request) => {
    if (
      !delayedInitialAnalyze &&
      request.url().includes("/api/transcripts/analyze")
    ) {
      delayedInitialAnalyze = true;
      setTimeout(() => void request.continue().catch(() => undefined), 900);
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
  report.lightLoadingState = true;
  await shoot("02b-loading-light");

  await waitForText("GANO hesabında hangi değer kullanılıyor?");
  report.creditScreen = true;
  report.creditNoCautionBanner = await page.evaluate(() => {
    const t = document.body.innerText;
    return !t.includes("dikkat") && !t.includes("uyarı");
  });

  await page.evaluate(() => {
    const btn = [...document.querySelectorAll('button[role="option"]')].find(
      (b) => (b.textContent || "").includes("Kredi"),
    );
    btn?.click();
  });
  await shoot("03-weighting");
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
    report.confirmation = true;
    await shoot("04-confirmation");
    await clickButton("Bilgiler doğru, devam et");
  }

  await page.waitForFunction(
    () => location.pathname.includes("genel-bakis"),
    { timeout: 20000 },
  );
  report.autoNavOverview = true;
  await waitForText("GANO");
  report.statusSurface = await page.evaluate(() =>
    document.body.innerText.toLocaleUpperCase("tr").includes("AKADEMİK DURUM"),
  );
  report.hasTrendSvg = await page.evaluate(
    () => !!document.querySelector("svg[aria-label^='Dönem GANO trendi']"),
  );
  report.sidebarReady = await page.evaluate(() =>
    document.body.innerText.includes("Hazır"),
  );
  report.sidebarAfterReady = await hasSidebarNav();
  report.semesterLabelsFull = await page.evaluate(() => {
    const labels = [...document.querySelectorAll("svg text")]
      .map((s) => s.textContent?.trim() ?? "")
      .filter((t) => /^\d{4}-\d{4}\s\S+$/.test(t));
    return labels.length;
  });
  await page.waitForSelector("[data-chart-point]");
  await page.evaluate(() => {
    document.querySelector("[data-chart-point]")?.focus();
  });
  await page.keyboard.press("Enter");
  await page.waitForSelector("[data-chart-tooltip]", { timeout: 4000 });
  report.chartPointKeyboardTooltip = await page.evaluate(() => {
    const tooltip = document.querySelector("[data-chart-tooltip]");
    const copy = tooltip?.textContent ?? "";
    const focused = document.activeElement?.hasAttribute("data-chart-point");
    return Boolean(
      focused &&
        copy.includes("GANO") &&
        /ağırlık/i.test(copy) &&
        /ders/i.test(copy),
    );
  });
  await page.keyboard.press("Escape");
  await page.waitForFunction(
    () => !document.querySelector("[data-chart-tooltip]"),
    { timeout: 4000 },
  );
  await shoot("05-overview-1280");

  await clickNav("Dersler");
  await page.waitForFunction(() => location.pathname.includes("/dersler"));
  await waitForText("Etkiyi Gör");
  report.gradeBadgeCount = await page.evaluate(
    () =>
      [...document.querySelectorAll("table span")].filter((s) =>
        /^(AA|BA|BB|CB|CC|DC|DD|FD|FF)$/.test(s.textContent?.trim() ?? ""),
      ).length,
  );
  await shoot("06-dersler-1280");

  const rowsBefore = await page.evaluate(
    () => document.querySelector("table")?.querySelectorAll("tbody tr").length ?? 0,
  );
  report.initialCoursePageSize = rowsBefore;
  report.hasShowMore = await page.evaluate(() =>
    document.body.innerText.includes("Daha fazla göster"),
  );
  await clickButton("Daha fazla göster");
  const rowsExpanded = await page.evaluate(
    () => document.querySelector("table")?.querySelectorAll("tbody tr").length ?? 0,
  );
  report.progressiveCourseList =
    rowsBefore === 10 && rowsExpanded > rowsBefore;

  await page.type('input[type="search"]', "PHYS");
  await new Promise((r) => setTimeout(r, 400));
  const rowsAfter = await page.evaluate(
    () => document.querySelector("table")?.querySelectorAll("tbody tr").length ?? 0,
  );
  report.searchFilters = rowsAfter > 0 && rowsAfter < rowsBefore;
  await shoot("07-dersler-search");
  await page.click('input[type="search"]', { clickCount: 3 });
  await page.keyboard.press("Backspace");
  await new Promise((r) => setTimeout(r, 300));
  await page.select('select[aria-label="Not filtresi"]', "AA");
  await new Promise((r) => setTimeout(r, 300));
  report.gradeFilter = await page.evaluate(() => {
    const rows = [
      ...(document.querySelector("table")?.querySelectorAll("tbody tr") ?? []),
    ];
    return (
      rows.length > 0 &&
      rows.every((row) =>
        [...row.querySelectorAll("span")].some(
          (span) => span.textContent?.trim() === "AA",
        ),
      )
    );
  });
  await page.select('select[aria-label="Not filtresi"]', "all");
  await new Promise((r) => setTimeout(r, 300));

  report.impactOpened = await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find((b) =>
      (b.textContent || "").includes("Etkiyi Gör"),
    );
    if (!btn) return false;
    btn.click();
    return true;
  });
  if (report.impactOpened) {
    await waitForText("potansiyeli");
    report.impactPanel = true;
    await shoot("08-course-impact");
  }

  await clickNav("Planlayıcı");
  await page.waitForFunction(() => location.pathname.includes("/planlayici"));
  await page.waitForSelector('input[placeholder="3.00"]');
  await page.type('input[placeholder="3.00"]', "3.00");
  await clickButton("Planı Oluştur");
  await page.waitForFunction(
    () => {
      const text = document.body.innerText.toLocaleUpperCase("tr");
      return (
        text.includes("TAHMİNİ GANO") ||
        text.includes("HEDEF KARŞILANDI") ||
        text.includes("ULAŞILAMIYOR")
      );
    },
    { timeout: 20000 },
  );
  report.plannerResult = true;
  await shoot("09-planner-result");

  await clickNav("Gelecek Dönem");
  await page.waitForFunction(() => location.pathname.includes("/gelecek-donem"));
  await page.waitForSelector('input[placeholder="Ders kodu veya adı"]');
  await page.type('input[placeholder="Ders kodu veya adı"]', "SENG301");
  await page.select('select[aria-label="Kredi seç"]', "3");
  report.commonWeightSelection = await page.$eval(
    'select[aria-label="Kredi seç"]',
    (select) =>
      select.value === "3" &&
      !document.querySelector('input[aria-label="Özel kredi değeri"]'),
  );
  await page.select('select[aria-label="Kredi seç"]', "other");
  const customWeightInput = await page.waitForSelector(
    'input[aria-label="Özel kredi değeri"]',
  );
  await customWeightInput.type("2.5");
  report.customWeightSelection = await page.$eval(
    'input[aria-label="Özel kredi değeri"]',
    (input) => input.value === "2.5",
  );
  await page.select('select[aria-label="Kredi seç"]', "3");
  await clickButton("Simülasyonu Hesapla");
  await waitForText("Tahmini yeni GANO");
  report.futureResult = true;
  report.futureWeightLabels = await page.evaluate(() => {
    const t = document.body.innerText;
    return t.includes("Mevcut ağırlık") && t.includes("Planlanan dönem");
  });
  await shoot("10-future-result");

  await clickNav("Hedef GANO");
  await page.waitForFunction(() => location.pathname.includes("/hedef-gano"));
  await page.waitForSelector('input[type="number"]');
  const inputs = await page.$$('input[type="number"]');
  await inputs[0].click({ clickCount: 3 });
  await inputs[0].type("3.0");
  await inputs[1].click({ clickCount: 3 });
  await inputs[1].type("20");
  await clickButton("Gerekli Ortalamayı Hesapla");
  await waitForText("Gerekli dönem ortalaması");
  report.requiredResult = true;
  await shoot("11-hedef-gano-result");

  await clickNav("Transkript");
  await page.waitForFunction(() => location.pathname.includes("/transkript"));
  await waitForText("Transkripti sıfırla");
  report.transcriptManageInApp = await hasSidebarNav();
  await shoot("12-transkript");

  await clickNav("Dersler");
  await page.waitForFunction(() => location.pathname.includes("/dersler"));
  await waitForText("Etkiyi Gör");

  for (const width of [390, 430, 768, 1024, 1440]) {
    await page.setViewport({ width, height: 900 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await new Promise((r) => setTimeout(r, 400));
    const state = await page.evaluate(() => {
      const table = document.querySelector("table");
      const cards = document.querySelectorAll("article");
      const sidebar = [...document.querySelectorAll("aside")].some(
        (a) => a.getBoundingClientRect().left >= 0,
      );
      const wrap = table?.parentElement ?? null;
      return {
        desktopTable: !!table && table.getBoundingClientRect().width > 0,
        mobileCards: cards.length,
        sidebar,
        tableFitsNoClip:
          !wrap || wrap.scrollWidth <= wrap.clientWidth + 1,
        actionColumnReachable: (() => {
          if (!wrap) return null;
          const btn = [...table.querySelectorAll("button")].find((b) =>
            (b.textContent || "").includes("Etkiyi Gör"),
          );
          if (!btn) return null;
          return (
            btn.getBoundingClientRect().right <=
            wrap.getBoundingClientRect().right + 1
          );
        })(),
        overflowX:
          document.documentElement.scrollWidth >
          document.documentElement.clientWidth + 1,
      };
    });
    report[`bp_${width}`] = { ...state, menuButton: await menuButtonVisible() };
    await shoot(`13-dersler-${width}`, false);
  }

  await page.setViewport({ width: 390, height: 844 });
  await new Promise((r) => setTimeout(r, 300));
  report.mobileMenuFocusable = await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find(
      (b) => b.textContent?.trim() === "Menü",
    );
    if (!btn) return false;
    btn.focus();
    return document.activeElement === btn;
  });
  await page.keyboard.press("Enter");
  await new Promise((r) => setTimeout(r, 300));
  report.mobileDrawerOpensByKeyboard = await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find(
      (b) => b.textContent?.trim() === "Menü",
    );
    const aside = document.querySelector("aside");
    return (
      btn?.getAttribute("aria-expanded") === "true" &&
      !!aside &&
      aside.getBoundingClientRect().left >= 0
    );
  });
  report.mobileDrawerMovesFocusInside = await page.evaluate(() => {
    const aside = document.querySelector("aside");
    return !!aside && aside.contains(document.activeElement);
  });
  await shoot("14-mobile-drawer");
  await page.keyboard.press("Escape");
  await new Promise((r) => setTimeout(r, 250));
  report.mobileDrawerEscapeRestoresFocus = await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find(
      (b) => b.textContent?.trim() === "Menü",
    );
    return (
      document.activeElement === btn &&
      btn?.getAttribute("aria-expanded") === "false"
    );
  });

  await clickNav("Genel Bakış");
  await page.waitForFunction(() => location.pathname.includes("/genel-bakis"));
  await waitForText("GANO");
  for (const width of [390, 768, 1024, 1440]) {
    await page.setViewport({ width, height: 900 });
    await shoot(`15-overview-${width}`, false);
  }

  await clickNav("Gelecek Dönem");
  await page.waitForFunction(() => location.pathname.includes("/gelecek-donem"));
  for (const width of [390, 1280]) {
    await page.setViewport({ width, height: 900 });
    await shoot(`16-future-${width}`, false);
  }

  await clickNav("Hedef GANO");
  await page.waitForFunction(() => location.pathname.includes("/hedef-gano"));
  for (const width of [390, 1280]) {
    await page.setViewport({ width, height: 900 });
    await shoot(`17-hedef-${width}`, false);
  }

  await clickNav("Planlayıcı");
  await page.waitForFunction(() => location.pathname.includes("/planlayici"));
  await page.setViewport({ width: 390, height: 900 });
  await shoot("18-planner-390", false);

  await page.setViewport({ width: 1280, height: 900 });
  const themeChanged = await page.evaluate(() => {
    const button = [...document.querySelectorAll("button")].find(
      (item) =>
        item.getAttribute("aria-label") === "Koyu temaya geç" &&
        item.offsetParent !== null,
    );
    button?.click();
    return !!button;
  });
  if (!themeChanged) throw new Error("Visible theme toggle not found");
  await page.waitForFunction(
    () => document.documentElement.dataset.theme === "dark",
  );
  report.darkThemeTokens = await page.evaluate(() => {
    const styles = getComputedStyle(document.documentElement);
    return {
      theme: document.documentElement.dataset.theme,
      background: styles.getPropertyValue("--bg").trim(),
      surface: styles.getPropertyValue("--surface").trim(),
      text: styles.getPropertyValue("--ink").trim(),
      stored: localStorage.getItem("gradepilot-theme"),
    };
  });

  const darkRoutes = [
    ["Genel Bakış", "/genel-bakis", "overview"],
    ["Dersler", "/dersler", "courses"],
    ["Planlayıcı", "/planlayici", "planner"],
    ["Gelecek Dönem", "/gelecek-donem", "future"],
    ["Hedef GANO", "/hedef-gano", "target"],
    ["Transkript", "/transkript", "transcript"],
  ];
  for (const [label, path, slug] of darkRoutes) {
    await clickNav(label);
    await page.waitForFunction(
      (expectedPath) => location.pathname.includes(expectedPath),
      {},
      path,
    );
    if (label === "Planlayıcı") {
      await clickButton("Kendi Planım");
    }
    for (const width of [390, 768, 1280]) {
      await page.setViewport({ width, height: 900 });
      await page.evaluate(() => window.scrollTo(0, 0));
      await shoot(`19-dark-${slug}-${width}`, false);
    }
  }
  report.darkRoutes = darkRoutes.map(([, , slug]) => slug);

  const darkEntry = await browser.newPage();
  await darkEntry.setViewport({ width: 1280, height: 900 });
  await darkEntry.goto("http://localhost:3000/transkript", {
    waitUntil: "networkidle0",
  });
  await darkEntry.waitForFunction(
    () =>
      document.documentElement.dataset.theme === "dark" &&
      document.body.innerText.includes("Transkriptini yükle, akademik durumunu planla."),
  );
  report.darkOnboarding = true;
  if (shotDir) {
    await darkEntry.screenshot({
      path: `${shotDir}\\20-dark-onboarding-1280.png`,
      fullPage: true,
    });
  }
  await darkEntry.setViewport({ width: 390, height: 844 });
  if (shotDir) {
    await darkEntry.screenshot({
      path: `${shotDir}\\20-dark-onboarding-390.png`,
      fullPage: true,
    });
  }

  await darkEntry.setRequestInterception(true);
  let delayedDarkAnalyze = false;
  darkEntry.on("request", (request) => {
    if (
      !delayedDarkAnalyze &&
      request.url().includes("/api/transcripts/analyze")
    ) {
      delayedDarkAnalyze = true;
      setTimeout(() => void request.continue().catch(() => undefined), 900);
      return;
    }
    void request.continue();
  });
  await darkEntry.waitForFunction(
    () => typeof window.__gradePilotUploadFile === "function",
  );
  await darkEntry.evaluate(async (b64) => {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    window.__gradePilotUploadFile(
      new File([bytes], "qa_transcript.pdf", { type: "application/pdf" }),
    );
  }, pdfB64);
  await darkEntry.waitForFunction(() =>
    document.body.innerText.includes("Transkript hazırlanıyor"),
  );
  report.darkLoadingState = true;
  if (shotDir) {
    await darkEntry.screenshot({
      path: `${shotDir}\\21-dark-loading-390.png`,
      fullPage: true,
    });
  }
  await new Promise((resolve) => setTimeout(resolve, 950));
  await darkEntry.close();

  const ectsPage = await browser.newPage();
  await ectsPage.setViewport({ width: 390, height: 844 });
  await ectsPage.goto("http://localhost:3000/transkript", {
    waitUntil: "networkidle0",
  });
  await ectsPage.waitForFunction(
    () => typeof window.__gradePilotUploadFile === "function",
  );
  await ectsPage.evaluate((b64) => {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    window.__gradePilotUploadFile(
      new File([bytes], "qa_transcript.pdf", { type: "application/pdf" }),
    );
  }, pdfB64);
  await ectsPage.waitForFunction(() =>
    document.body.innerText.includes("GANO hesabında hangi değer kullanılıyor?"),
  );
  await ectsPage.evaluate(() => {
    const option = [...document.querySelectorAll('button[role="option"]')].find(
      (button) => button.textContent?.includes("AKTS"),
    );
    option?.click();
  });
  await ectsPage.waitForFunction(() => {
    const next = [...document.querySelectorAll("button")].find(
      (button) => button.textContent?.trim() === "Devam et",
    );
    return !!next && !next.disabled;
  });
  await ectsPage.evaluate(() => {
    const next = [...document.querySelectorAll("button")].find(
      (button) => button.textContent?.trim() === "Devam et",
    );
    next?.click();
  });
  await ectsPage.waitForFunction(
    () => location.pathname.includes("/genel-bakis"),
    { timeout: 30000 },
  );
  await ectsPage.evaluate(() => {
    const link = [...document.querySelectorAll("a")].find(
      (item) => item.textContent?.trim() === "Gelecek Dönem",
    );
    link?.click();
  });
  await ectsPage.waitForFunction(() =>
    location.pathname.includes("/gelecek-donem"),
  );
  await ectsPage.waitForSelector('select[aria-label="AKTS seç"]');
  await ectsPage.select('select[aria-label="AKTS seç"]', "10");
  const ectsCommonSelection = await ectsPage.$eval(
    'select[aria-label="AKTS seç"]',
    (select) => select.value === "10",
  );
  await ectsPage.select('select[aria-label="AKTS seç"]', "other");
  const ectsCustomInput = await ectsPage.waitForSelector(
    'input[aria-label="Özel akts değeri" i]',
  );
  await ectsCustomInput.type("12.5");
  report.ectsWeightSelection = await ectsPage.$eval(
    'input[aria-label="Özel akts değeri" i]',
    (input, commonWorked) =>
      commonWorked && input.value === "12.5" && input.inputMode === "decimal",
    ectsCommonSelection,
  );
  if (shotDir) {
    await ectsPage.screenshot({
      path: `${shotDir}\\22-ects-custom-mobile.png`,
      fullPage: true,
    });
  }
  await ectsPage.close();

  report.themePersistence = await page.evaluate(
    () => localStorage.getItem("gradepilot-theme") === "dark",
  );
  await page.reload({ waitUntil: "networkidle0" });
  report.persistedThemeAfterReload = await page.evaluate(
    () => document.documentElement.dataset.theme === "dark",
  );

  await page.evaluate(() => localStorage.removeItem("gradepilot-theme"));
  await page.emulateMediaFeatures([
    { name: "prefers-color-scheme", value: "dark" },
    { name: "prefers-reduced-motion", value: "reduce" },
  ]);
  await page.reload({ waitUntil: "networkidle0" });
  report.systemPreferenceDark = await page.evaluate(
    () => document.documentElement.dataset.theme === "dark",
  );
  report.reducedMotionNoAnimation = await page.evaluate(() => {
    const animated = [...document.querySelectorAll(".gp-enter, .gp-fade")];
    return animated.every(
      (el) => getComputedStyle(el).animationName === "none",
    );
  });

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
