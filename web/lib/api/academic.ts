import { ApiClientError } from "@/lib/api/transcripts";
import { getApiBaseUrl } from "@/lib/config";
import type { Course } from "@/lib/types";
import { validOfficialCgpa } from "@/lib/gpaPresentation";

export type AcademicSummaryResponse = {
  current_gpa: number;
  official_cgpa?: number | null;
  derived_cgpa?: number;
  total_gpa_weight: number;
  active_course_count: number;
  semesters: Array<{
    semester: string;
    gpa: number;
    weight: number;
    course_count: number;
  }>;
};

export type AcademicSummary = {
  /** Legacy course-derived GPA used by planner consumers. */
  currentGpa: number;
  officialCgpa: number | null;
  derivedCgpa: number;
  totalGpaWeight: number;
  activeCourseCount: number;
  semesters: Array<{
    semester: string;
    gpa: number;
    weight: number;
    courseCount: number;
  }>;
};

export type TargetPlanChange = {
  code: string;
  name: string;
  fromGrade: string;
  toGrade: string;
  gpaWeight: number;
  gpaGain: number | null;
};

export type TargetPlan = {
  currentGpa: number;
  targetGpa: number;
  estimatedGpa: number;
  reachable: boolean;
  alreadyReached: boolean;
  strategy: string;
  maxGrade: string;
  maximumPossibleGpa: number | null;
  changes: TargetPlanChange[];
};

export type ManualScenarioChangeInput = {
  courseCode: string;
  newGrade: string;
};

export type ManualScenarioChange = {
  code: string;
  name: string;
  fromGrade: string;
  toGrade: string;
};

export type ManualScenario = {
  currentGpa: number;
  projectedGpa: number;
  gpaChange: number;
  changes: ManualScenarioChange[];
};

function parseDetail(payload: unknown): string {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof (payload as { detail: unknown }).detail === "string"
  ) {
    return (payload as { detail: string }).detail;
  }
  return "İstek başarısız oldu.";
}

function serializeCourses(courses: Course[]) {
  return courses.map((course) => ({
    code: course.code,
    name: course.name,
    gpa_credit: course.gpaCredit,
    ects: course.ects,
    local_credit: course.localCredit,
    grade: course.grade,
    semester: course.semester,
    source_order: course.sourceOrder,
  }));
}

async function postJson(url: string, body: unknown): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiClientError(
      "network",
      "Şu anda bağlantı kurulamıyor. Biraz sonra yeniden dene.",
    );
  }

  let payload: unknown = null;
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      payload = await response.json();
    } catch {
      throw new ApiClientError(
        "invalid_response",
        "Sunucu yanıtı okunamadı.",
        response.status,
      );
    }
  }

  if (!response.ok) {
    throw new ApiClientError("http", parseDetail(payload), response.status);
  }

  return payload;
}

export async function fetchAcademicSummary(
  courses: Course[],
  officialCgpa: number | null = null,
): Promise<AcademicSummary> {
  const payload = await postJson(`${getApiBaseUrl()}/api/academic/summary`, {
    courses: serializeCourses(courses),
    official_cgpa: validOfficialCgpa(officialCgpa),
  });

  const data = payload as AcademicSummaryResponse;
  if (
    !data ||
    typeof data.current_gpa !== "number" ||
    (data.derived_cgpa !== undefined && (typeof data.derived_cgpa !== "number" || !Number.isFinite(data.derived_cgpa))) ||
    typeof data.total_gpa_weight !== "number" ||
    typeof data.active_course_count !== "number" ||
    !Array.isArray(data.semesters)
  ) {
    throw new ApiClientError(
      "invalid_response",
      "Akademik özet yanıtı beklenen biçimde değil.",
    );
  }

  return {
    currentGpa: data.current_gpa,
    officialCgpa: validOfficialCgpa(data.official_cgpa),
    derivedCgpa: data.derived_cgpa ?? data.current_gpa,
    totalGpaWeight: data.total_gpa_weight,
    activeCourseCount: data.active_course_count,
    semesters: data.semesters.map((row) => ({
      semester: row.semester,
      gpa: row.gpa,
      weight: row.weight,
      courseCount: row.course_count,
    })),
  };
}

export async function fetchTargetPlan(
  courses: Course[],
  input: {
    targetGpa: number;
    maxGrade: string;
    strategy: string;
  },
): Promise<TargetPlan> {
  const payload = await postJson(
    `${getApiBaseUrl()}/api/academic/target-plan`,
    {
      courses: serializeCourses(courses),
      target_gpa: input.targetGpa,
      max_grade: input.maxGrade,
      strategy: input.strategy,
    },
  );

  const data = payload as {
    current_gpa: number;
    target_gpa: number;
    estimated_gpa: number;
    reachable: boolean;
    already_reached: boolean;
    strategy: string;
    max_grade: string;
    maximum_possible_gpa: number | null;
    changes: Array<{
      code: string;
      name: string;
      from_grade: string;
      to_grade: string;
      gpa_weight: number;
      gpa_gain: number | null;
    }>;
  };

  if (
    !data ||
    typeof data.current_gpa !== "number" ||
    typeof data.target_gpa !== "number" ||
    typeof data.estimated_gpa !== "number" ||
    typeof data.reachable !== "boolean" ||
    typeof data.already_reached !== "boolean" ||
    typeof data.strategy !== "string" ||
    typeof data.max_grade !== "string" ||
    !Array.isArray(data.changes)
  ) {
    throw new ApiClientError(
      "invalid_response",
      "Hedef plan yanıtı beklenen biçimde değil.",
    );
  }

  return {
    currentGpa: data.current_gpa,
    targetGpa: data.target_gpa,
    estimatedGpa: data.estimated_gpa,
    reachable: data.reachable,
    alreadyReached: data.already_reached,
    strategy: data.strategy,
    maxGrade: data.max_grade,
    maximumPossibleGpa:
      typeof data.maximum_possible_gpa === "number"
        ? data.maximum_possible_gpa
        : null,
    changes: data.changes.map((row) => ({
      code: row.code,
      name: row.name,
      fromGrade: row.from_grade,
      toGrade: row.to_grade,
      gpaWeight: row.gpa_weight,
      gpaGain: typeof row.gpa_gain === "number" ? row.gpa_gain : null,
    })),
  };
}

export async function fetchManualScenario(
  courses: Course[],
  changes: ManualScenarioChangeInput[],
): Promise<ManualScenario> {
  const payload = await postJson(
    `${getApiBaseUrl()}/api/academic/manual-scenario`,
    {
      courses: serializeCourses(courses),
      changes: changes.map((change) => ({
        course_code: change.courseCode,
        new_grade: change.newGrade,
      })),
    },
  );

  const data = payload as {
    current_gpa: number;
    projected_gpa: number;
    gpa_change: number;
    changes: Array<{
      code: string;
      name: string;
      from_grade: string;
      to_grade: string;
    }>;
  };

  if (
    !data ||
    typeof data.current_gpa !== "number" ||
    typeof data.projected_gpa !== "number" ||
    typeof data.gpa_change !== "number" ||
    !Array.isArray(data.changes) ||
    data.changes.some(
      (change) =>
        typeof change.code !== "string" ||
        typeof change.name !== "string" ||
        typeof change.from_grade !== "string" ||
        typeof change.to_grade !== "string",
    )
  ) {
    throw new ApiClientError(
      "invalid_response",
      "Kendi planım yanıtı beklenen biçimde değil.",
    );
  }

  return {
    currentGpa: data.current_gpa,
    projectedGpa: data.projected_gpa,
    gpaChange: data.gpa_change,
    changes: data.changes.map((change) => ({
      code: change.code,
      name: change.name,
      fromGrade: change.from_grade,
      toGrade: change.to_grade,
    })),
  };
}

export function toTurkishManualScenarioMessage(error: unknown): string {
  if (!(error instanceof ApiClientError)) {
    return "Beklenmeyen bir hata oluştu. Lütfen tekrar dene.";
  }
  if (error.kind === "network") return error.detail;
  if (error.status === 429) return error.detail;

  const detail = error.detail.toLowerCase();
  if (detail.includes("no courses were provided")) {
    return "Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.";
  }
  if (detail.includes("at least one grade change")) {
    return "Planına en az bir ders eklemelisin.";
  }
  if (detail.includes("duplicate change")) {
    return "Aynı ders plana yalnızca bir kez eklenebilir.";
  }
  if (detail.includes("not found")) {
    return "Seçilen ders aktif transkriptte bulunamadı.";
  }
  if (detail.includes("must be higher")) {
    return "Yeni not, dersin mevcut notundan yüksek olmalı.";
  }
  if (detail.includes("invalid grade") || detail.includes("unknown grade")) {
    return "Seçilen not geçerli değil.";
  }
  if (detail.includes("gpa weight")) {
    return "Ders ağırlığı geçerli ve 0’dan büyük olmalı.";
  }
  return "Kendi planın hesaplanamadı. Lütfen tekrar dene.";
}

export function toTurkishPlannerMessage(error: unknown): string {
  if (!(error instanceof ApiClientError)) {
    return "Beklenmeyen bir hata oluştu. Lütfen tekrar dene.";
  }

  if (error.kind === "network") {
    return error.detail;
  }
  if (error.status === 429) {
    return error.detail;
  }

  const detail = error.detail.toLowerCase();

  if (detail.includes("no courses were provided")) {
    return "Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.";
  }
  if (detail.includes("target gpa")) {
    return "Hedef GANO 0.00 ile 4.00 arasında olmalı.";
  }
  if (detail.includes("invalid strategy")) {
    return "Seçilen strateji desteklenmiyor.";
  }
  if (
    detail.includes("invalid maximum grade") ||
    detail.includes("unknown grade")
  ) {
    return "Seçilen maksimum not geçerli değil.";
  }
  if (detail.includes("no gpa weight")) {
    return "GANO ağırlığı olmayan derslerle plan oluşturulamaz.";
  }

  return "Plan oluşturulamadı. Lütfen tekrar dene.";
}

export type CourseImpactOption = {
  grade: string;
  projectedGpa: number;
  gpaGain: number;
};

export type CourseImpact = {
  course: {
    code: string;
    name: string;
    currentGrade: string;
    gpaWeight: number;
  };
  currentGpa: number;
  options: CourseImpactOption[];
};

export async function fetchCourseImpact(
  courses: Course[],
  courseCode: string,
): Promise<CourseImpact> {
  const payload = await postJson(
    `${getApiBaseUrl()}/api/academic/course-impact`,
    {
      courses: serializeCourses(courses),
      course_code: courseCode,
    },
  );

  const data = payload as {
    course: {
      code: string;
      name: string;
      current_grade: string;
      gpa_weight: number;
    };
    current_gpa: number;
    options: Array<{
      grade: string;
      projected_gpa: number;
      gpa_gain: number;
    }>;
  };

  if (
    !data ||
    !data.course ||
    typeof data.course.code !== "string" ||
    typeof data.course.name !== "string" ||
    typeof data.course.current_grade !== "string" ||
    typeof data.course.gpa_weight !== "number" ||
    typeof data.current_gpa !== "number" ||
    !Array.isArray(data.options)
  ) {
    throw new ApiClientError(
      "invalid_response",
      "Ders etki yanıtı beklenen biçimde değil.",
    );
  }

  return {
    course: {
      code: data.course.code,
      name: data.course.name,
      currentGrade: data.course.current_grade,
      gpaWeight: data.course.gpa_weight,
    },
    currentGpa: data.current_gpa,
    options: data.options.map((row) => ({
      grade: row.grade,
      projectedGpa: row.projected_gpa,
      gpaGain: row.gpa_gain,
    })),
  };
}

export function toTurkishCourseImpactMessage(error: unknown): string {
  if (!(error instanceof ApiClientError)) {
    return "Beklenmeyen bir hata oluştu. Lütfen tekrar dene.";
  }

  if (error.kind === "network") {
    return error.detail;
  }
  if (error.status === 429) {
    return error.detail;
  }

  const detail = error.detail.toLowerCase();
  if (detail.includes("no courses were provided")) {
    return "Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.";
  }
  if (detail.includes("course code is required")) {
    return "Bir ders seçmelisin.";
  }
  if (detail.includes("not found")) {
    return "Seçilen ders aktif transkriptte bulunamadı.";
  }
  if (detail.includes("unknown grade")) {
    return "Ders notu geçerli değil.";
  }

  return "Ders etkisi hesaplanamadı. Lütfen tekrar dene.";
}

export type FutureSemesterProjection = {
  currentGpa: number;
  futureSemesterGpa: number;
  projectedCgpa: number;
  currentGpaWeight: number;
  futureGpaWeight: number;
  projectedTotalWeight: number;
};

export async function fetchFutureSemester(
  courses: Course[],
  futureCourses: Array<{
    name: string;
    gpaCredit: number;
    grade: string;
    code?: string;
  }>,
): Promise<FutureSemesterProjection> {
  const payload = await postJson(
    `${getApiBaseUrl()}/api/academic/future-semester`,
    {
      courses: serializeCourses(courses),
      future_courses: futureCourses.map((course) => ({
        name: course.name,
        gpa_credit: course.gpaCredit,
        grade: course.grade,
        code: course.code,
      })),
    },
  );

  const data = payload as {
    current_gpa: number;
    future_semester_gpa: number;
    projected_cgpa: number;
    current_gpa_weight: number;
    future_gpa_weight: number;
    projected_total_weight: number;
  };

  if (
    !data ||
    typeof data.current_gpa !== "number" ||
    typeof data.future_semester_gpa !== "number" ||
    typeof data.projected_cgpa !== "number" ||
    typeof data.current_gpa_weight !== "number" ||
    typeof data.future_gpa_weight !== "number" ||
    typeof data.projected_total_weight !== "number"
  ) {
    throw new ApiClientError(
      "invalid_response",
      "Gelecek dönem yanıtı beklenen biçimde değil.",
    );
  }

  return {
    currentGpa: data.current_gpa,
    futureSemesterGpa: data.future_semester_gpa,
    projectedCgpa: data.projected_cgpa,
    currentGpaWeight: data.current_gpa_weight,
    futureGpaWeight: data.future_gpa_weight,
    projectedTotalWeight: data.projected_total_weight,
  };
}

export type RequiredSemesterGpa = {
  currentGpa: number;
  targetGpa: number;
  futureGpaWeight: number;
  requiredSemesterGpa: number;
  reachable: boolean;
  alreadyReached: boolean;
};

export async function fetchRequiredSemesterGpa(
  courses: Course[],
  input: {
    targetGpa: number;
    futureGpaWeight: number;
  },
): Promise<RequiredSemesterGpa> {
  const payload = await postJson(
    `${getApiBaseUrl()}/api/academic/required-semester-gpa`,
    {
      courses: serializeCourses(courses),
      target_gpa: input.targetGpa,
      future_gpa_weight: input.futureGpaWeight,
    },
  );

  const data = payload as {
    current_gpa: number;
    target_gpa: number;
    future_gpa_weight: number;
    required_semester_gpa: number;
    reachable: boolean;
    already_reached: boolean;
  };

  if (
    !data ||
    typeof data.current_gpa !== "number" ||
    typeof data.target_gpa !== "number" ||
    typeof data.future_gpa_weight !== "number" ||
    typeof data.required_semester_gpa !== "number" ||
    typeof data.reachable !== "boolean" ||
    typeof data.already_reached !== "boolean"
  ) {
    throw new ApiClientError(
      "invalid_response",
      "Gerekli dönem ortalaması yanıtı beklenen biçimde değil.",
    );
  }

  return {
    currentGpa: data.current_gpa,
    targetGpa: data.target_gpa,
    futureGpaWeight: data.future_gpa_weight,
    requiredSemesterGpa: data.required_semester_gpa,
    reachable: data.reachable,
    alreadyReached: data.already_reached,
  };
}

export function toTurkishRequiredGpaMessage(error: unknown): string {
  if (!(error instanceof ApiClientError)) {
    return "Beklenmeyen bir hata oluştu. Lütfen tekrar dene.";
  }

  if (error.kind === "network") {
    return error.detail;
  }
  if (error.status === 429) {
    return error.detail;
  }

  const detail = error.detail.toLowerCase();
  if (detail.includes("no courses were provided")) {
    return "Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.";
  }
  if (detail.includes("target gpa") || detail.includes("target cgpa")) {
    return "Hedef GANO 0.00 ile 4.00 arasında olmalı.";
  }
  if (
    detail.includes("future gpa weight") ||
    detail.includes("future credits")
  ) {
    return "Gelecek dönem toplam ağırlığı 0’dan büyük olmalı.";
  }
  if (detail.includes("unknown grade")) {
    return "Transkript notları geçerli değil.";
  }

  return "Gerekli ortalama hesaplanamadı. Lütfen tekrar dene.";
}

export function toTurkishFutureSemesterMessage(error: unknown): string {
  if (!(error instanceof ApiClientError)) {
    return "Beklenmeyen bir hata oluştu. Lütfen tekrar dene.";
  }

  if (error.kind === "network") {
    return error.detail;
  }
  if (error.status === 429) {
    return error.detail;
  }

  const detail = error.detail.toLowerCase();
  if (detail.includes("no courses were provided")) {
    return "Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.";
  }
  if (detail.includes("at least one future course")) {
    return "En az bir gelecek dönem dersi eklemelisin.";
  }
  if (detail.includes("unknown grade")) {
    return "Beklenen not geçerli değil.";
  }
  if (detail.includes("positive gpa weight") || detail.includes("invalid gpa weight")) {
    return "Ağırlık 0’dan büyük bir sayı olmalı.";
  }
  if (detail.includes("missing a valid name")) {
    return "Her ders için bir ad veya kod yaz.";
  }

  return "Simülasyon hesaplanamadı. Lütfen tekrar dene.";
}
