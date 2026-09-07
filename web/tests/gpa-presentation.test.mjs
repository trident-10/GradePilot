// node --test tests/gpa-presentation.test.mjs (Node 24+)
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { registerHooks } from "node:module";
import { fileURLToPath } from "node:url";
import test from "node:test";
import ts from "typescript";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

const root = new URL("../", import.meta.url).href;
const hooks = registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === "next/link") return nextResolve("next/link.js", context);
    if (specifier.startsWith("@/")) {
      const base = new URL(specifier.slice(2), root);
      const resolved = [".ts", ".tsx"].map((ext) => `${base.href}${ext}`)
        .find((url) => existsSync(fileURLToPath(url)));
      return nextResolve(resolved ?? specifier, context);
    }
    return nextResolve(specifier, context);
  },
  load(url, context, nextLoad) {
    if (url.startsWith(root) && /\.tsx?$/.test(url) && !url.includes("node_modules")) {
      return { format: "module", shortCircuit: true, source: ts.transpileModule(
        readFileSync(fileURLToPath(url), "utf8"),
        { compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } },
      ).outputText };
    }
    return nextLoad(url, context);
  },
});
const { gpaPresentation } = await import("../lib/gpaPresentation.ts");
const { GpaSummary } = await import("../components/GpaSummary.tsx");
const { fetchAcademicSummary, fetchTargetPlan } = await import("../lib/api/academic.ts");
hooks.deregister();

for (const [official, derived, expected, label] of [
  [3.24, 3.23, 3.24, "GANO"],
  [null, 3.23, 3.23, "Hesaplanan GANO"],
  [3.24, 3.24, 3.24, "GANO"],
  [0, 3.23, 0, "GANO"],
]) {
  test(`card prefers official ${official} over derived ${derived} without secondary derived line`, () => {
    const presentation = gpaPresentation(official, derived);
    assert.equal(presentation.value, expected);
    assert.equal(presentation.label, label);
    const props = { officialCgpa: official, derivedCgpa: derived, totalGpaWeight: 100,
      activeCourses: 2, semesterCount: 1, highestSemesterGpa: null, weightingMode: "credit" };
    const markup = renderToStaticMarkup(createElement(GpaSummary, props));
    assert.ok(markup.includes(`>${expected.toFixed(2)}</p>`), markup);
    assert.ok(markup.includes(`>${label}</p>`));
    if (official !== null) assert.match(markup, /Transkriptte belirtilen resmî GANO/);
    assert.ok(!markup.includes("GradePilot hesabı"));
    if (official !== null && official !== derived) {
      assert.ok(!markup.includes(`>${derived.toFixed(2)}</p>`));
    }
    assert.equal(props.officialCgpa, official);
    assert.equal(props.derivedCgpa, derived);
  });
}

for (const invalid of [NaN, Infinity, -1, 4.5]) {
  test(`invalid official ${invalid} cannot become the main value`, () => {
    assert.equal(gpaPresentation(invalid, 3.23).value, 3.23);
    assert.equal(gpaPresentation(invalid, 3.23).isOfficial, false);
  });
}

test("missing values do not invent a zero GPA", () => {
  assert.equal(gpaPresentation(null, null).value, null);
});

test("summary and planner transport use official as planning baseline", async (t) => {
  const courses = [{code: "CS101", name: "Test", grade: "BB", gpaCredit: 3,
    semester: "2024 Fall", localCredit: 3, ects: 6, sourceOrder: 0}];
  const before = structuredClone(courses);
  t.mock.method(globalThis, "fetch", async (url, options) => {
    const body = JSON.parse(options.body);
    if (url.endsWith("/summary")) {
      assert.equal(body.official_cgpa, 3.24);
      return Response.json({current_gpa: 3.24, derived_cgpa: 3.23, official_cgpa: 3.24,
        total_gpa_weight: 3, active_course_count: 1, semesters: []});
    }
    assert.ok(url.endsWith("/target-plan"));
    assert.equal(body.official_cgpa, 3.24);
    return Response.json({current_gpa: 3.24, target_gpa: 3.5, estimated_gpa: 3.4, reachable: true,
      already_reached: false, strategy: "min_courses", max_grade: "AA", changes: []});
  });
  const result = await fetchAcademicSummary(courses, 3.24);
  assert.equal(result.officialCgpa, 3.24);
  assert.equal(result.derivedCgpa, 3.23);
  assert.equal(result.currentGpa, 3.24);
  const plan = await fetchTargetPlan(courses, {targetGpa: 3.5, maxGrade: "AA", strategy: "min_courses"}, 3.24);
  assert.equal(plan.currentGpa, 3.24);
  assert.deepEqual(courses, before);
});
