import { AcademicSkeleton } from "@/components/academic-loading";
import { MetricTile } from "@/components/dashboard";
import {
  formatGpa,
  weightUnitLabel,
  weightingChip,
} from "@/lib/display";

type GpaSummaryProps = {
  currentGpa: number | null;
  totalGpaWeight: number | null;
  activeCourses: number | null;
  semesterCount: number | null;
  highestSemesterGpa: number | null;
  weightingMode: string | null;
  loading?: boolean;
};

export function GpaSummary({
  currentGpa,
  totalGpaWeight,
  activeCourses,
  semesterCount,
  highestSemesterGpa,
  weightingMode,
  loading = false,
}: GpaSummaryProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <AcademicSkeleton className="col-span-2 h-24 lg:col-span-2" />
        <AcademicSkeleton className="h-24" />
        <AcademicSkeleton className="h-24" />
        <AcademicSkeleton className="h-24" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
      <div className="col-span-2">
        <MetricTile
          strong
          label="GANO"
          value={currentGpa === null ? "—" : formatGpa(currentGpa)}
          hint={weightingChip(weightingMode)}
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
