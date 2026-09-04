import { mkdirSync, readFileSync } from "fs";
import { createRequire } from "module";

const require = createRequire(import.meta.url);
const puppeteer = require("puppeteer-core");

const pdfPath = process.argv[2] ?? "C:\\Temp\\qa_transcript.pdf";
const screenshotDir = process.argv[3] ?? null;
const pdfB64 = readFileSync(pdfPath).toString("base64");
if (screenshotDir) mkdirSync(screenshotDir, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  headless: true,
  args: ["--no-sandbox", "--window-size=1280,900"],
  defaultViewport: { width: 1280, height: 900 },
});
const page = await browser.newPage();

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

async function clickByText(selector, text) {
  const clicked = await page.evaluate(
    ({ css, needle }) => {
      const element = [...document.querySelectorAll(css)].find(
        (item) => item.textContent?.trim() === needle,
      );
      if (!element) return false;
      element.click();
      return true;
    },
    { css: selector, needle: text },
  );
  if (!clicked) throw new Error(`${selector} not found: ${text}`);
}

try {
  await page.goto("http://localhost:3000/transkript", {
    waitUntil: "networkidle0",
  });
  await waitForText("Transkriptini yükle, akademik durumunu planla.");
  await page.waitForFunction(
    () => typeof window.__gradePilotUploadFile === "function",
  );
  await page.evaluate((b64) => {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    window.__gradePilotUploadFile(
      new File([bytes], "qa_transcript.pdf", {
        type: "application/pdf",
      }),
    );
  }, pdfB64);

  await waitForText("GANO hesabında hangi değer kullanılıyor?");
  await page.evaluate(() => {
    const option = [...document.querySelectorAll('button[role="option"]')].find(
      (button) => button.textContent?.includes("Kredi"),
    );
    option?.click();
  });
  await clickByText("button", "Devam et");
  await page.waitForFunction(
    () => location.pathname.includes("/genel-bakis"),
    { timeout: 30000 },
  );

  await clickByText("a", "Planlayıcı");
  await page.waitForFunction(() => location.pathname.includes("/planlayici"));
  await clickByText("button", "Kendi Planım");
  await waitForText("Kendi not senaryonu oluştur");

  async function toggleCourse(code) {
    const selected = await page.evaluate((courseCode) => {
      const label = [...document.querySelectorAll("label")].find((item) =>
        item.textContent?.includes(courseCode),
      );
      const checkbox = label?.querySelector('input[type="checkbox"]');
      if (!checkbox) return false;
      checkbox.click();
      return true;
    }, code);
    if (!selected) throw new Error(`Course not found in picker: ${code}`);
  }

  async function calculate() {
    const responsePromise = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/academic/manual-scenario") &&
        response.request().method() === "POST",
    );
    await clickByText("button", "Planımı Hesapla →");
    const response = await responsePromise;
    if (!response.ok()) {
      throw new Error(`manual-scenario returned ${response.status()}`);
    }
    const request = JSON.parse(response.request().postData() ?? "{}");
    const result = await response.json();
    await waitForText("Tahmini GANO");
    return { request, response, result };
  }

  await page.click('button[aria-label="Ders seç"]');
  await clickByText("button", "DD/DC");
  const quickFilterWorked = await page.evaluate(() => {
    const panel = document.querySelector("#manual-course-picker");
    const grades = [...(panel?.querySelectorAll("ul label span") ?? [])]
      .map((item) => item.textContent?.trim())
      .filter((text) => text === "DD" || text === "DC");
    const rows = panel?.querySelectorAll('input[type="checkbox"]').length ?? 0;
    return rows > 0 && grades.length === rows;
  });
  // Active DD/DC courses in the QA transcript (CENG218 was repeated to BB).
  await toggleCourse("CENG241");
  await toggleCourse("CENG384");
  await toggleCourse("PHYS102");
  await clickByText("button", "Seçilenleri plana ekle");
  await waitForText("Seçtiğin değişiklikler · 3 ders");

  const defaults = await page.evaluate(() => ({
    ceng241: document.querySelector(
      'select[aria-label="CENG241 hedef notu"]',
    )?.value,
    ceng384: document.querySelector(
      'select[aria-label="CENG384 hedef notu"]',
    )?.value,
    phys102: document.querySelector(
      'select[aria-label="PHYS102 hedef notu"]',
    )?.value,
  }));
  await page.select('select[aria-label="CENG241 hedef notu"]', "BB");
  await page.select('select[aria-label="CENG384 hedef notu"]', "BA");
  await page.select('select[aria-label="PHYS102 hedef notu"]', "AA");
  const initial = await calculate();

  const targetSelect = 'select[aria-label="CENG241 hedef notu"]';
  await page.select(targetSelect, "AA");
  await new Promise((resolve) => setTimeout(resolve, 150));
  const stateAfterEdit = await page.$eval(targetSelect, (select) => ({
    value: select.value,
    staleResultVisible: document.body.innerText
      .toLocaleUpperCase("tr")
      .includes("TAHMİNİ GANO"),
  }));
  const recalculated = await calculate();

  const displayed = await page.evaluate(() => document.body.innerText);
  const format = (value) => Number(value).toFixed(2);
  const initialByCode = Object.fromEntries(
    initial.request.changes.map((change) => [change.course_code, change]),
  );
  const recalculatedByCode = Object.fromEntries(
    recalculated.request.changes.map((change) => [
      change.course_code,
      change,
    ]),
  );
  const assertions = {
    automaticModeStillPresent: displayed.includes("Otomatik Plan"),
    manualModeSelected: displayed.includes("Kendi Planım"),
    quickFilterWorked,
    multiSelectAddedThreeCourses:
      initial.request.changes?.length === 3 &&
      displayed.includes("Seçtiğin değişiklikler · 3 ders"),
    nextGradeDefaults:
      defaults.ceng241 === "DC" &&
      defaults.ceng384 === "CC" &&
      defaults.phys102 === "CC",
    editableTargetUpdatedState:
      stateAfterEdit.value === "AA" && !stateAfterEdit.staleResultVisible,
    independentTargetsSent:
      initialByCode.CENG241?.new_grade === "BB" &&
      initialByCode.CENG384?.new_grade === "BA" &&
      initialByCode.PHYS102?.new_grade === "AA",
    recalculationSentEditedTarget:
      recalculatedByCode.CENG241?.new_grade === "AA",
    recalculatedAfterEdit:
      recalculated.result.projected_gpa > initial.result.projected_gpa,
    currentGpaFromBackend: displayed.includes(
      format(recalculated.result.current_gpa),
    ),
    projectedGpaFromBackend: displayed.includes(
      format(recalculated.result.projected_gpa),
    ),
    changeFromBackend: displayed.includes(
      `${recalculated.result.gpa_change >= 0 ? "+" : ""}${format(recalculated.result.gpa_change)}`,
    ),
  };
  if (Object.values(assertions).some((value) => !value)) {
    throw new Error(`Assertion failed: ${JSON.stringify(assertions)}`);
  }

  if (screenshotDir) {
    await page.screenshot({
      path: `${screenshotDir}\\manual-scenario-desktop.png`,
      fullPage: true,
    });
    await page.setViewport({ width: 390, height: 844 });
    await new Promise((resolve) => setTimeout(resolve, 300));
    await page.screenshot({
      path: `${screenshotDir}\\manual-scenario-mobile.png`,
      fullPage: true,
    });
  }

  await clickByText("button", "Kaldır");
  await new Promise((resolve) => setTimeout(resolve, 150));
  const removalWorked = await page.evaluate(
    () =>
      document.body.innerText.includes("Seçtiğin değişiklikler · 2 ders") &&
      !document.body.innerText.toLocaleUpperCase("tr").includes("TAHMİNİ GANO"),
  );
  if (!removalWorked) {
    throw new Error("Removing the edited course did not clear the plan.");
  }

  console.log(
    JSON.stringify(
      {
        ...assertions,
        endpointStatus: recalculated.response.status(),
        currentGpa: recalculated.result.current_gpa,
        initialProjectedGpa: initial.result.projected_gpa,
        recalculatedProjectedGpa: recalculated.result.projected_gpa,
        gpaChange: recalculated.result.gpa_change,
        removalWorked,
      },
      null,
      2,
    ),
  );
  await browser.close();
} catch (error) {
  console.error("MANUAL_SCENARIO_E2E_FAIL", error);
  console.error(
    await page.evaluate(() => document.body.innerText).catch(() => ""),
  );
  await browser.close();
  process.exit(1);
}
