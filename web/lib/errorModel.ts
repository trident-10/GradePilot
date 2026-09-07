export type ErrorCode =
  | "GP-001"
  | "GP-002"
  | "GP-003"
  | "GP-004"
  | "GP-005"
  | "GP-006"
  | "GP-007"
  | "GP-008"
  | "GP-009";

export type ErrorSeverity = "info" | "warning" | "error" | "success";

export type UserFacingError = {
  title: string;
  description: string;
  suggestions: string[];
  errorCode: ErrorCode;
  severity: ErrorSeverity;
  retryable: boolean;
  retryAfterSeconds?: number;
};

type ApiErrorLike = {
  kind?: unknown;
  status?: unknown;
  detail?: unknown;
  retryAfterSeconds?: unknown;
  errorType?: unknown;
  code?: unknown;
};

function createError(
  errorCode: ErrorCode,
  title: string,
  description: string,
  suggestions: string[],
  severity: ErrorSeverity,
  retryable: boolean,
  retryAfterSeconds?: number,
): UserFacingError {
  return {
    errorCode,
    title,
    description,
    suggestions,
    severity,
    retryable,
    ...(retryAfterSeconds ? { retryAfterSeconds } : {}),
  };
}

export function unsupportedFileError(): UserFacingError {
  return createError(
    "GP-004",
    "Desteklenmeyen dosya",
    "Lütfen yalnızca PDF yükleyin.",
    ["PDF formatında bir dosya seçin."],
    "warning",
    false,
  );
}

export function fileTooLargeError(): UserFacingError {
  return createError(
    "GP-003",
    "Dosya boyutu çok büyük",
    "Maksimum dosya boyutu 10 MB olmalıdır.",
    ["PDF'yi 10 MB'tan küçük olacak şekilde yeniden dışa aktarın."],
    "warning",
    false,
  );
}

function unreadablePdfError(): UserFacingError {
  return createError(
    "GP-001",
    "PDF okunamadı",
    "Yüklediğiniz PDF dosyası okunamadı. Bu dosya bozuk, şifre korumalı veya desteklenmeyen bir PDF olabilir.",
    [
      "PDF'yi yeniden dışa aktarın.",
      "Şifre korumasını kaldırın.",
      "Farklı Kaydet seçeneğini deneyin.",
    ],
    "error",
    true,
  );
}

function unsupportedTranscriptError(): UserFacingError {
  return createError(
    "GP-002",
    "Transkript formatı desteklenmiyor",
    "Bu transkript formatı henüz desteklenmiyor.",
    [
      "Transkripti öğrenci bilgi sisteminden yeniden indirin.",
      "Farklı bir PDF deneyin.",
      "Sorun sürerse destek koduyla bizimle iletişime geçin.",
    ],
    "warning",
    false,
  );
}

function invalidTranscriptError(code: string): UserFacingError {
  let description =
    "Transkriptteki ders, not veya kredi bilgileri güvenilir biçimde okunamadı. Hesaplama başlatılmadı.";
  switch (code) {
    case "no_course_structure":
      description = "PDF içinde okunabilir bir ders tablosu bulunamadı.";
      break;
    case "overlapping_tables":
      description = "Transkriptte yan yana bulunan ders tabloları güvenilir biçimde ayrılamadı.";
      break;
    case "invalid_credit_cells":
    case "no_credit_columns":
    case "incomplete_selected_credit":
      description = "Derslerin kredi bilgileri eksik veya okunamıyor. Yanlış bir ortalama hesaplamamak için işlem durduruldu.";
      break;
    case "unreadable_course":
      description = "Bazı ders satırları veya notları okunamadı. Eksik derslerle ortalama hesaplamamak için işlem durduruldu.";
      break;
    case "no_gpa_courses":
      description = "Transkriptte ortalama hesabına katılabilecek notlandırılmış ders bulunamadı.";
      break;
  }
  return createError(
    "GP-002",
    "Transkript güvenilir biçimde okunamadı",
    description,
    [
      "Transkriptin tüm sayfalarını içeren PDF'yi öğrenci bilgi sisteminden yeniden indirin.",
      "Sorun sürerse destek koduyla bizimle iletişime geçin.",
    ],
    "warning",
    false,
  );
}

function invalidMappingError(code: string): UserFacingError {
  let description = "Seçtiğiniz kredi alanları bu transkript için kullanılamıyor.";
  switch (code) {
    case "empty_mapping":
      description = "Devam etmek için en az bir kredi alanı seçilmelidir.";
      break;
    case "duplicate_mapping":
      description = "Yerel kredi ve AKTS için aynı sütun seçilemez.";
      break;
    case "incomplete_mapping":
      description = "Seçtiğiniz sütunda her ders için bir kredi değeri bulunmuyor.";
      break;
    case "invalid_weighting_field":
      description = "Ortalama hesabı için seçtiğiniz kredi türü bu transkriptte kullanılamıyor.";
      break;
  }
  return createError(
    "GP-008",
    "Kredi seçimi geçersiz",
    description,
    ["Tekrar Dene ile transkripti yeniden analiz edip kredi seçimini kontrol edin."],
    "warning",
    true,
  );
}

function invalidRequestError(): UserFacingError {
  return createError(
    "GP-009",
    "İstek işlenemedi",
    "Gönderilen dosya veya seçim bilgileri doğrulanamadı.",
    ["PDF'yi yeniden seçerek işlemi başlatın."],
    "warning",
    false,
  );
}

function rateLimitError(retryAfterSeconds?: number): UserFacingError {
  return createError(
    "GP-005",
    "Çok fazla istek gönderildi",
    "Kısa süre içerisinde çok fazla yükleme yaptınız. Lütfen biraz bekleyip tekrar deneyin.",
    [
      retryAfterSeconds
        ? `Sunucunun önerdiği süre olan ${retryAfterSeconds} saniye bekleyin.`
        : "Kısa bir süre bekleyip tekrar deneyin.",
    ],
    "warning",
    true,
    retryAfterSeconds,
  );
}

function networkError(): UserFacingError {
  return createError(
    "GP-006",
    "Sunucuya ulaşılamadı",
    "İnternet bağlantınızı kontrol edip tekrar deneyin.",
    ["Bağlantınızı kontrol edin.", "Bağlantı sağlandıktan sonra tekrar deneyin."],
    "error",
    true,
  );
}

function internalServerError(): UserFacingError {
  return createError(
    "GP-007",
    "Beklenmeyen bir hata oluştu",
    "Sunucu beklenmeyen bir hata döndürdü. Lütfen daha sonra tekrar deneyin.",
    ["Biraz bekleyip tekrar deneyin."],
    "error",
    true,
  );
}

function isApiErrorLike(error: unknown): error is ApiErrorLike {
  return typeof error === "object" && error !== null;
}

function normaliseRetryAfter(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) && value > 0
    ? Math.ceil(value)
    : undefined;
}

/**
 * Converts untrusted transport and backend failures to copy that is safe to
 * show in the product. Backend messages and exception details are never
 * returned to the UI.
 */
export function toUserFacingError(error: unknown): UserFacingError {
  if (!isApiErrorLike(error)) {
    return internalServerError();
  }

  const status = typeof error.status === "number" ? error.status : null;
  const kind = typeof error.kind === "string" ? error.kind : "";
  const detail = typeof error.detail === "string" ? error.detail.toLowerCase() : "";
  const errorType = typeof error.errorType === "string" ? error.errorType : "";
  const code = typeof error.code === "string" ? error.code : "";

  // A server failure must never be disguised as a document or user input issue.
  if (status !== null && status >= 500) {
    return internalServerError();
  }
  if (kind === "network") {
    return networkError();
  }
  if (status === 429) {
    return rateLimitError(normaliseRetryAfter(error.retryAfterSeconds));
  }
  if (status === 413) {
    return fileTooLargeError();
  }
  if (kind === "invalid_response") {
    return internalServerError();
  }
  if (status === 400 || status === 422) {
    if (errorType === "invalid_transcript") {
      return invalidTranscriptError(code);
    }
    if (errorType === "invalid_mapping_request") {
      return invalidMappingError(code);
    }
  }
  if (
    detail.includes("maximum allowed size") ||
    detail.includes("dosyası çok büyük")
  ) {
    return fileTooLargeError();
  }
  if (
    detail.includes("not a valid pdf") ||
    detail.includes("is not a valid pdf") ||
    detail.includes("geçerli bir pdf değil")
  ) {
    return unsupportedFileError();
  }
  if (
    detail.includes("ders yapısı") ||
    detail.includes("course structure") ||
    detail.includes("interpreted") ||
    detail.includes("unsupported transcript") ||
    detail.includes("transkript formatı desteklenmiyor") ||
    detail.includes("no viable credit") ||
    detail.includes("kredi alanı")
  ) {
    return unsupportedTranscriptError();
  }
  if (
    detail.includes("malformed") ||
    detail.includes("could not be opened") ||
    detail.includes("pdf okunamadı") ||
    detail.includes("şifre") ||
    detail.includes("empty")
  ) {
    return unreadablePdfError();
  }
  if (status === 400 || status === 422) {
    return invalidRequestError();
  }

  return internalServerError();
}
