"use client";

import {
  ContentFrame,
  GhostButton,
  GradeBadge,
  InfoNote,
  PageHeader,
  PrimaryButton,
} from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { selectHistoricalCourses } from "@/lib/courses";

function displayValue(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return String(value);
}

function userFacingWarning(warning: string): string | null {
  const normalized = warning.toLocaleLowerCase("tr-TR");

  // Confirmation page already asks the user to review courses — skip this noise.
  if (normalized.includes("generic parsing was used")) {
    return null;
  }
  if (normalized.includes("no courses were extracted")) {
    return "Seçilen kredi sütunuyla ders bilgileri oluşturulamadı. Lütfen yeni bir PDF seçin.";
  }
  if (
    normalized.includes("gano hesabında") ||
    normalized.includes("dersler bulundu ancak") ||
    normalized.includes("transkriptte kredi")
  ) {
    return warning;
  }

  return "Bazı ders bilgileri otomatik olarak doğrulanamadı. Lütfen tabloyu dikkatlice kontrol edin.";
}

function SummaryItem({ children }: { children: string }) {
  return (
    <li className="flex min-w-0 items-center gap-2 text-sm text-ink">
      <span
        aria-hidden
        className="inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-ok-soft text-xs font-bold text-ok"
      >
        ✓
      </span>
      <span>{children}</span>
    </li>
  );
}

export function CourseConfirmation() {
  const { pendingCourses, warnings, confirmCourses, resetTranscript } =
    useAppState();
  const semesterCount = new Set(
    pendingCourses
      .map((course) => course.semester?.trim())
      .filter((semester): semester is string => Boolean(semester)),
  ).size;
  const repeatedCourseCount = selectHistoricalCourses(pendingCourses).length;
  const visibleWarnings = [
    ...new Set(
      warnings
        .map(userFacingWarning)
        .filter((warning): warning is string => warning !== null),
    ),
  ];

  return (
    <ContentFrame width="wide" className="gp-upload-enter space-y-5">
      <PageHeader
        title="Transkript Doğrulama"
        description="Ders listesi hazır. Analize başlamadan önce not ve kredi bilgilerini gözden geçir."
      />

      {pendingCourses.length > 0 ? (
        <section
          role="status"
          aria-live="polite"
          aria-label="Transkript özeti"
          className="w-full rounded-[16px] border border-ok/30 bg-ok-soft/55 p-5 text-left shadow-[var(--shadow-sm)] sm:p-6"
        >
          <span className="inline-flex items-center gap-1.5 rounded-full bg-ok/12 px-2.5 py-1 text-xs font-bold tracking-[0.08em] text-ok">
            <svg aria-hidden className="size-4" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.7" />
              <path
                d="m8 12 2.6 2.6L16.5 9"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.7"
              />
            </svg>
            BAŞARILI
          </span>
          <h2 className="mt-3 text-lg font-bold tracking-[-0.025em] text-ink">
            Transkript özeti hazır
          </h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-muted">
            Aşağıdaki özet ve tablo doğru görünüyorsa analize devam
            edebilirsin.
          </p>
          <ul className="mt-4 grid gap-2 border-t border-ok/20 pt-4 sm:grid-cols-3">
            <SummaryItem>{`${pendingCourses.length} ders bulundu`}</SummaryItem>
            {semesterCount > 0 ? (
              <SummaryItem>{`${semesterCount} dönem algılandı`}</SummaryItem>
            ) : null}
            <SummaryItem>
              {repeatedCourseCount > 0
                ? `${repeatedCourseCount} tekrar alınan ders bulundu`
                : "Tekrar alınan ders bulunmadı"}
            </SummaryItem>
          </ul>
        </section>
      ) : null}

      {visibleWarnings.length > 0 ? (
        <InfoNote>
          {visibleWarnings.map((warning) => (
            <span key={warning} className="block">
              {warning}
            </span>
          ))}
        </InfoNote>
      ) : null}

      {pendingCourses.length === 0 ? (
        <p className="text-sm text-muted">Onaylanacak ders bulunamadı.</p>
      ) : (
        <div className="overflow-x-auto rounded-[14px] bg-surface/90 shadow-[var(--shadow-sm)]">
          <table className="w-full min-w-[640px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-rule/80 text-left text-[11px] uppercase tracking-[0.06em] text-faint">
                <th className="px-4 py-2.5 font-medium">Ders</th>
                <th className="px-4 py-2.5 font-medium">Not</th>
                <th className="px-4 py-2.5 font-medium">Kredi</th>
                <th className="px-4 py-2.5 font-medium">AKTS</th>
                <th className="px-4 py-2.5 font-medium">Dönem</th>
              </tr>
            </thead>
            <tbody>
              {pendingCourses.map((course) => (
                <tr
                  key={`${course.sourceOrder ?? "x"}-${course.code}-${course.semester ?? ""}-${course.grade}`}
                  className="border-b border-rule/70 last:border-b-0"
                >
                  <td className="px-4 py-2.5">
                    <p className="font-semibold tracking-wide text-ink">
                      {course.code}
                    </p>
                    <p className="text-xs text-faint">{course.name}</p>
                  </td>
                  <td className="px-4 py-2.5">
                    <GradeBadge grade={course.grade} />
                  </td>
                  <td className="px-4 py-2.5 tabular-nums text-muted">
                    {displayValue(course.localCredit)}
                  </td>
                  <td className="px-4 py-2.5 tabular-nums text-muted">
                    {displayValue(course.ects)}
                  </td>
                  <td className="px-4 py-2.5 text-muted">
                    {displayValue(course.semester)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <PrimaryButton
          type="button"
          className="w-full sm:w-auto"
          disabled={pendingCourses.length === 0}
          onClick={() => {
            confirmCourses();
          }}
        >
          Bilgiler Doğru, Analize Devam Et
        </PrimaryButton>
        <GhostButton
          type="button"
          className="w-full sm:w-auto"
          onClick={resetTranscript}
        >
          Yeni PDF Seç
        </GhostButton>
      </div>
    </ContentFrame>
  );
}
