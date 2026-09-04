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

function displayValue(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return String(value);
}

export function CourseConfirmation() {
  const { pendingCourses, warnings, confirmCourses, resetTranscript } =
    useAppState();

  return (
    <ContentFrame width="wide">
      <PageHeader
        title="Derslerini kontrol et"
        description="Devam etmeden önce ders ve not bilgilerini gözden geçir."
      />

      {warnings.length > 0 ? (
        <InfoNote>
          {warnings.map((warning) => (
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

      <div className="flex flex-wrap gap-3">
        <PrimaryButton
          type="button"
          disabled={pendingCourses.length === 0}
          onClick={() => {
            confirmCourses();
          }}
        >
          Bilgiler doğru, devam et
        </PrimaryButton>
        <GhostButton type="button" onClick={resetTranscript}>
          Baştan yükle
        </GhostButton>
      </div>
    </ContentFrame>
  );
}
