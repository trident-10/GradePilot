// Run with Node 24+: node --test tests/transcript-errors.test.mjs
import assert from "node:assert/strict";
import { registerHooks } from "node:module";
import test from "node:test";

// Resolve the application's TypeScript alias without a test-only bundler.
const aliases = registerHooks({
  resolve(specifier, context, nextResolve) {
    return nextResolve(
      specifier.startsWith("@/")
        ? new URL(`../${specifier.slice(2)}.ts`, import.meta.url).href
        : specifier,
      context,
    );
  },
});
const { analyzeTranscript, ApiClientError } = await import("../lib/api/transcripts.ts");
const { toUserFacingError } = await import("../lib/errorModel.ts");
aliases.deregister();

const file = new File(["%PDF-test"], "transcript.pdf", { type: "application/pdf" });

async function rejectedAnalysis(t, payload, status = 400, headers = {}) {
  t.mock.method(globalThis, "fetch", async () => new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json", ...headers },
  }));
  let failure;
  await assert.rejects(analyzeTranscript(file), (error) => {
    assert.ok(error instanceof ApiClientError);
    failure = error;
    return true;
  });
  return failure;
}

test("document error metadata survives transport and replaces the misleading server error", async (t) => {
  const error = await rejectedAnalysis(t, {
    error_type: "invalid_transcript",
    code: "invalid_credit_cells",
    detail: "PRIVATE COURSE CONTENT: invalid cells at C:/private/transcript.pdf",
  });
  assert.equal(error.errorType, "invalid_transcript");
  assert.equal(error.code, "invalid_credit_cells");
  const visible = toUserFacingError(error);
  assert.equal(visible.errorCode, "GP-002");
  assert.match(visible.description, /kredi bilgileri/);
  assert.equal(visible.retryable, false);
  assert.doesNotMatch(JSON.stringify(visible), /PRIVATE|C:\/private|invalid_credit_cells/);
});

test("the reported overlapping-tables response explains the actual document problem", async (t) => {
  const error = await rejectedAnalysis(t, {
    error_type: "invalid_transcript",
    code: "overlapping_tables",
    detail: "Yan yana ders tabloları güvenle ayrılamadı.",
  });
  const visible = toUserFacingError(error);
  assert.equal(visible.errorCode, "GP-002");
  assert.match(visible.description, /ders tabloları/);
  assert.doesNotMatch(visible.description, /Sunucu|daha sonra tekrar/);
});

test("mapping errors remain distinct and offer another selection attempt", async (t) => {
  const error = await rejectedAnalysis(t, {
    error_type: "invalid_mapping_request",
    code: "duplicate_mapping",
    detail: "The same numeric column cannot be assigned to both local credit and ECTS.",
  });
  const visible = toUserFacingError(error);
  assert.equal(visible.errorCode, "GP-008");
  assert.match(visible.description, /aynı sütun seçilemez/);
  assert.equal(visible.retryable, true);
});

test("all blocking extraction codes use document errors, including future codes", () => {
  for (const code of [
    "no_course_structure", "overlapping_tables", "invalid_credit_cells",
    "unreadable_course", "no_gpa_courses", "no_credit_columns",
    "incomplete_selected_credit", "invalid_transcript", "unknown_future_issue",
  ]) {
    const visible = toUserFacingError({
      status: 400, errorType: "invalid_transcript", code,
      detail: "Malformed INTERNAL EXCEPTION; empty mapping",
    });
    assert.equal(visible.errorCode, "GP-002", code);
    assert.doesNotMatch(JSON.stringify(visible), /INTERNAL EXCEPTION|unknown_future_issue/);
  }
});

test("all mapping codes use input errors without depending on English messages", () => {
  for (const code of [
    "empty_mapping", "unsupported_mapping", "duplicate_mapping", "invalid_mapping",
    "mapping_not_applicable", "incomplete_mapping", "invalid_weighting_field",
    "unknown_future_mapping",
  ]) {
    const visible = toUserFacingError({
      status: 422, errorType: "invalid_mapping_request", code,
      detail: "PDF could not be opened",
    });
    assert.equal(visible.errorCode, "GP-008", code);
    assert.equal(visible.retryable, true);
  }
});

test("real server errors take precedence over document metadata and legacy keywords", () => {
  for (const status of [500, 502, 503]) {
    const visible = toUserFacingError({
      status, errorType: "invalid_transcript", code: "no_course_structure",
      detail: "maximum allowed size; empty; could not be opened; unsupported transcript",
    });
    assert.equal(visible.errorCode, "GP-007");
    assert.equal(visible.retryable, true);
  }
});

test("unknown or malformed error metadata is ignored safely", async (t) => {
  const error = await rejectedAnalysis(t, {
    error_type: { value: "invalid_transcript" },
    code: ["no_course_structure"],
    detail: [{ msg: "SECRET VALIDATION INPUT" }],
  }, 422);
  assert.equal(error.errorType, undefined);
  assert.equal(error.code, undefined);
  const visible = toUserFacingError(error);
  assert.equal(visible.errorCode, "GP-009");
  assert.doesNotMatch(JSON.stringify(visible), /SECRET/);
});

test("unclassified client requests are not reported as server failures", () => {
  for (const status of [400, 422]) {
    const visible = toUserFacingError({ status, detail: "Some future request validation error" });
    assert.equal(visible.errorCode, "GP-009");
  }
});

test("legacy PDF failure responses remain supported", () => {
  const cases = [
    [400, "File is not a valid PDF", "GP-004"],
    [400, "PDF could not be opened", "GP-001"],
    [400, "Transcript could not be interpreted.", "GP-002"],
    [413, "Upload exceeds maximum allowed size", "GP-003"],
  ];
  for (const [status, detail, expected] of cases) {
    assert.equal(toUserFacingError({ status, detail }).errorCode, expected);
  }
});

test("rate limiting retains Retry-After through transport", async (t) => {
  const error = await rejectedAnalysis(t, { detail: "Too many uploads" }, 429, {
    "retry-after": "12",
  });
  const visible = toUserFacingError(error);
  assert.equal(visible.errorCode, "GP-005");
  assert.equal(visible.retryAfterSeconds, 12);
});

test("network failures remain a connection error", async (t) => {
  t.mock.method(globalThis, "fetch", async () => { throw new TypeError("fetch failed"); });
  await assert.rejects(analyzeTranscript(file), (error) => {
    assert.equal(toUserFacingError(error).errorCode, "GP-006");
    return true;
  });
});

test("unreadable JSON is an invalid server response, not a transcript rejection", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response("{", {
    status: 400,
    headers: { "content-type": "application/json" },
  }));
  await assert.rejects(analyzeTranscript(file), (error) => {
    assert.equal(error.kind, "invalid_response");
    assert.equal(toUserFacingError(error).errorCode, "GP-007");
    return true;
  });
});

test("successful transcript analysis and caller selections are preserved", async (t) => {
  const payload = { status: "ready", courses: [], warnings: [] };
  t.mock.method(globalThis, "fetch", async (_url, options) => {
    assert.equal(options.method, "POST");
    assert.equal(options.body.get("file").name, "transcript.pdf");
    assert.equal(options.body.get("weighting_field"), "local_credit");
    assert.equal(options.body.get("local_credit_field"), "numeric_0");
    return Response.json(payload);
  });
  assert.deepEqual(await analyzeTranscript(file, {
    weightingField: "local_credit", localCreditField: "numeric_0",
  }), payload);
});

for (const [system, field, wireField] of [
  ["credit", "localCreditField", "local_credit_field"],
  ["ects", "ectsField", "ects_field"],
]) {
  test(`single ${system} column selection includes weighting without requiring the other role`, async (t) => {
    const payload = { status: "confirmation", courses: [], warnings: [] };
    t.mock.method(globalThis, "fetch", async (_url, options) => {
      assert.equal(options.body.get("weighting_field"), system);
      assert.equal(options.body.get(wireField), "column_1");
      assert.equal(options.body.has(system === "credit" ? "ects_field" : "local_credit_field"), false);
      return Response.json(payload);
    });
    assert.deepEqual(await analyzeTranscript(file, {
      weightingField: system, [field]: "column_1",
    }), payload);
  });
}
