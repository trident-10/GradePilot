import { AcademicSkeleton } from "@/components/academic-loading";
import { MetricTile } from "@/components/dashboard";
import {
  formatGpa,
  weightUnitLabel,
  weightingChip,
} from "@/lib/display";
import { gpaPresentation } from "@/lib/gpaPresentation";

type GpaSummaryProps = {
  derivedCgpa: number | null;
  officialCgpa?: number | null;
  totalGpaWeight: number | null;
  activeCourses: number | null;
  semesterCount: number | null;
  highestSemesterGpa: number | null;
  weightingMode: string | null;
  loading?: boolean;
};

export function GpaSummary({
  derivedCgpa,
  officialCgpa = null,
  totalGpaWeight,
  activeCourses,
  semesterCount,
  highestSemesterGpa,
  weightingMode,
  loading = false,
}: GpaSummaryProps) {
  const gano = gpaPresentation(officialCgpa, derivedCgpa);
  if (loading) {
    return (
      <div className="grid grid-cols-2 items-stretch gap-3 sm:gap-4 lg:grid-cols-5">
        <AcademicSkeleton className="col-span-2 min-h-[7.5rem] lg:col-span-2" />
        <AcademicSkeleton className="min-h-[7rem]" />
        <AcademicSkeleton className="min-h-[7rem]" />
        <AcademicSkeleton className="min-h-[7rem]" />
      </div>
    );
  }

  return (
    <div
      className="grid grid-cols-2 items-stretch gap-3 sm:gap-4 lg:grid-cols-5"
      aria-label="Akademik özet"
    >
      <div className="col-span-2 h-full lg:col-span-2">
        <MetricTile
          strong
          label={gano.label}
          value={gano.value === null ? "—" : formatGpa(gano.value)}
          hint={gano.isOfficial ? gano.source : `${weightingChip(weightingMode)} · ${gano.source}`}
        />
      </div>
      <MetricTile
        label={`Toplam ${weightUnitLabel(weightingMode)}`}
        value={totalGpaWeight === null ? "—" : totalGpaWeight}
      />
      <MetricTile
        label="Aktif ders"
        value={activeCourses === null ? "—" : activeCourses}
      />
      <MetricTile
        label="Dönem"
        value={semesterCount === null ? "—" : semesterCount}
        hint={
          highestSemesterGpa === null
            ? undefined
            : `En yüksek ${formatGpa(highestSemesterGpa)}`
        }
      />
    </div>
  );
}
