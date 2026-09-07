import { toUserFacingError } from "@/lib/errorModel";
import { getApiBaseUrl } from "@/lib/config";

/** Mirrors FastAPI TranscriptAnalyzeResponse (snake_case wire format). */
export type AnalyzeApiResponse = {
  official_summary?: { cgpa: number | null };
  status: "manual_mapping" | "credit_selection" | "confirmation" | "ready";
  format: string;
  confidence: number;
  credit_options: Array<{
    id: string;
    label: string;
  }>;
  mapping_candidates: Array<{
    id: string;
    label: string;
    sample_values: number[];
    confidence: "high" | "medium" | "low";
  }>;
  courses: Array<{
    code: string;
    name: string;
    gpa_credit: number;
    ects: number | null;
    local_credit: number | null;
    grade: string;
    semester: string | null;
    source_order: number;
  }>;
  warnings: string[];
};

export class ApiClientError extends Error {
  status: number | null;
  detail: string;
  kind: "http" | "network" | "invalid_response";
  retryAfterSeconds?: number;
  errorType?: string;
  code?: string;

  constructor(
    kind: "http" | "network" | "invalid_response",
    detail: string,
    status: number | null = null,
    retryAfterSeconds?: number,
    metadata?: { errorType?: string; code?: string },
  ) {
    super(detail);
    this.name = "ApiClientError";
    this.kind = kind;
    this.detail = detail;
    this.status = status;
    this.retryAfterSeconds = retryAfterSeconds;
    this.errorType = metadata?.errorType;
    this.code = metadata?.code;
  }
}

function parseRetryAfterSeconds(response: Response): number | undefined {
  const header = response.headers.get("retry-after");
  if (!header) return undefined;

  const seconds = Number(header);
  if (Number.isFinite(seconds) && seconds > 0) {
    return Math.ceil(seconds);
  }

  const retryAt = Date.parse(header);
  if (Number.isNaN(retryAt)) return undefined;

  return Math.max(1, Math.ceil((retryAt - Date.now()) / 1000));
}

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

function parseErrorMetadata(payload: unknown): {
  errorType?: string;
  code?: string;
} {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return {};
  }
  return {
    ...("error_type" in payload && typeof payload.error_type === "string"
      ? { errorType: payload.error_type }
      : {}),
    ...("code" in payload && typeof payload.code === "string"
      ? { code: payload.code }
      : {}),
  };
}

export async function analyzeTranscript(
  file: File,
  options?: {
    weightingField?: string;
    localCreditField?: string;
    ectsField?: string;
  },
): Promise<AnalyzeApiResponse> {
  const form = new FormData();
  form.append("file", file);
  if (options?.weightingField) {
    form.append("weighting_field", options.weightingField);
  }
  if (options?.localCreditField) {
    form.append("local_credit_field", options.localCreditField);
  }
  if (options?.ectsField) {
    form.append("ects_field", options.ectsField);
  }

  const url = `${getApiBaseUrl()}/api/transcripts/analyze`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      body: form,
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
    throw new ApiClientError(
      "http",
      parseDetail(payload),
      response.status,
      parseRetryAfterSeconds(response),
      parseErrorMetadata(payload),
    );
  }

  if (
    !payload ||
    typeof payload !== "object" ||
    !("status" in payload) ||
    typeof (payload as { status: unknown }).status !== "string"
  ) {
    throw new ApiClientError(
      "invalid_response",
      "Sunucu yanıtı beklenen biçimde değil.",
      response.status,
    );
  }

  return payload as AnalyzeApiResponse;
}

/** Map backend/English error text to Turkish UI copy. */
export function toTurkishUserMessage(error: unknown): string {
  return toUserFacingError(error).description;
}
