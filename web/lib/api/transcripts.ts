import { getApiBaseUrl } from "@/lib/config";

/** Mirrors FastAPI TranscriptAnalyzeResponse (snake_case wire format). */
export type AnalyzeApiResponse = {
  status: "credit_selection" | "confirmation" | "ready";
  format: string;
  confidence: number;
  credit_options: Array<{
    id: string;
    label: string;
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

  constructor(
    kind: "http" | "network" | "invalid_response",
    detail: string,
    status: number | null = null,
  ) {
    super(detail);
    this.name = "ApiClientError";
    this.kind = kind;
    this.detail = detail;
    this.status = status;
  }
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

export async function analyzeTranscript(
  file: File,
  weightingField?: string,
): Promise<AnalyzeApiResponse> {
  const form = new FormData();
  form.append("file", file);
  if (weightingField) {
    form.append("weighting_field", weightingField);
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
  if (!(error instanceof ApiClientError)) {
    return "Beklenmeyen bir hata oluştu. Lütfen tekrar dene.";
  }

  if (error.kind === "network") {
    return error.detail;
  }

  if (error.status === 429) {
    return error.detail;
  }

  if (error.status === 413) {
    return "PDF dosyası çok büyük. Maksimum 10 MB yükleyebilirsin.";
  }

  if (error.detail === "PDF en fazla 50 sayfa olabilir.") {
    return error.detail;
  }
  if (error.detail === "PDF okunamadı. Farklı bir dosya deneyin.") {
    return error.detail;
  }
  if (error.detail === "Yüklenen dosya geçerli bir PDF değil.") {
    return error.detail;
  }
  if (error.detail.startsWith("PDF dosyası çok büyük.")) {
    return "PDF dosyası çok büyük. Maksimum 10 MB yükleyebilirsin.";
  }

  const detail = error.detail.toLowerCase();

  if (
    detail.includes("not a valid pdf") ||
    detail.includes("is not a valid pdf")
  ) {
    return "Yüklenen dosya geçerli bir PDF değil.";
  }
  if (detail.includes("empty")) {
    return "PDF dosyası boş görünüyor.";
  }
  if (
    detail.includes("malformed") ||
    detail.includes("could not be opened") ||
    detail.includes("pdf okunamadı")
  ) {
    return "PDF okunamadı. Farklı bir dosya deneyin.";
  }
  if (detail.includes("too many pages") || detail.includes("en fazla 50 sayfa")) {
    return "PDF en fazla 50 sayfa olabilir.";
  }
  if (
    detail.includes("maximum allowed size") ||
    detail.includes("çok büyük")
  ) {
    return "PDF dosyası çok büyük. Maksimum 10 MB yükleyebilirsin.";
  }
  if (detail.includes("no courses were provided")) {
    return "Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.";
  }
  if (detail.includes("weighting")) {
    return "Seçilen GANO ağırlığı bu transkript için geçerli değil.";
  }
  if (detail.includes("interpreted")) {
    return "Transkript anlaşılamadı. Farklı bir PDF dene.";
  }
  if (detail.includes("no viable credit") || detail.includes("kredi alanı")) {
    return "Bu transkriptte kullanılabilecek bir kredi alanı tespit edilemedi.";
  }

  return "Transkript işlenirken bir hata oluştu. Lütfen tekrar dene.";
}
