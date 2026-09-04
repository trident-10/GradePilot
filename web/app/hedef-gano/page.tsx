"use client";

import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { TargetProcess } from "@/components/academic-loading";
import { RequireReady } from "@/components/RequireReady";
import {
  ContentFrame,
  DomainStatus,
  EmptyState,
  FormField,
  InlineNotice,
  OutcomeHero,
  PageHeader,
  PrimaryButton,
  ResultSurface,
  Reveal,
  Section,
  SupportStat,
  WeightingChip,
  controlClass,
} from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { cx, formatGpa, futureWeightFieldLabel } from "@/lib/display";

function parseFiniteNumber(value: string): number | null {
  const trimmed = value.trim().replace(",", ".");
  if (trimmed === "") return null;
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed)) return null;
  return parsed;
}

export default function RequiredGpaPage() {
  const {
    academicSummary,
    weightingMode,
    requiredGpaResult,
    requiredGpaLoading,
    requiredGpaError,
    requestRequiredSemesterGpa,
    clearRequiredGpa,
  } = useAppState();

  const [targetInput, setTargetInput] = useState("");
  const [futureWeightInput, setFutureWeightInput] = useState("");

  const parsedTarget = parseFiniteNumber(targetInput);
  const parsedWeight = parseFiniteNumber(futureWeightInput);
  const targetValid =
    parsedTarget !== null && parsedTarget >= 0 && parsedTarget <= 4;
  const weightValid = parsedWeight !== null && parsedWeight > 0;
  const canSubmit = targetValid && weightValid && !requiredGpaLoading;

  function markInputsChanged() {
    if (requiredGpaResult || requiredGpaError) {
      clearRequiredGpa();
    }
  }

  return (
    <AppShell>
      <RequireReady>
        <ContentFrame width="medium" className="space-y-5">
          <PageHeader
            title="Hedef GANO"
            description="Hedefe ulaşmak için gelecek dönem kaç ortalama yapman gerekiyor?"
            aside={<WeightingChip mode={weightingMode} />}
          />

          <div className="grid min-w-0 gap-4 md:grid-cols-2 md:items-start">
          <Section surface="functional">
            <form
              className="grid gap-4"
              onSubmit={(event) => {
                event.preventDefault();
                if (!targetValid || !weightValid) return;
                void requestRequiredSemesterGpa({
                  targetGpa: parsedTarget,
                  futureGpaWeight: parsedWeight,
                });
              }}
            >
              <FormField label="Hedef GANO">
                <input
                  type="number"
                  inputMode="decimal"
                  min={0}
                  max={4}
                  step="0.01"
                  placeholder="3.00"
                  value={targetInput}
                  onChange={(event) => {
                    setTargetInput(event.target.value);
                    markInputsChanged();
                  }}
                  className={cx(controlClass, "tabular-nums")}
                />
              </FormField>
              <FormField label={futureWeightFieldLabel(weightingMode)}>
                <input
                  type="number"
                  inputMode="decimal"
                  min={0.5}
                  step="0.5"
                  placeholder="20"
                  value={futureWeightInput}
                  onChange={(event) => {
                    setFutureWeightInput(event.target.value);
                    markInputsChanged();
                  }}
                  className={cx(controlClass, "tabular-nums")}
                />
              </FormField>
              <div>
                <PrimaryButton type="submit" disabled={!canSubmit}>
                  {requiredGpaLoading ? "Hesaplanıyor" : "Gerekli Ortalamayı Hesapla"}
                </PrimaryButton>
              </div>
            </form>
          </Section>

          <div className="space-y-3">
          {requiredGpaError ? (
            <InlineNotice tone="error">{requiredGpaError}</InlineNotice>
          ) : null}

          {requiredGpaLoading ? (
            <TargetProcess
              currentGpa={academicSummary?.currentGpa ?? null}
              targetGpa={parsedTarget}
            />
          ) : null}

          {!requiredGpaResult && !requiredGpaLoading && !requiredGpaError ? (
            <EmptyState title="Hedefini girip hesapla." />
          ) : null}

          {requiredGpaResult && !requiredGpaLoading ? (
            <Reveal>
              <RequiredGpaOutcome result={requiredGpaResult} />
            </Reveal>
          ) : null}
          </div>
          </div>
        </ContentFrame>
      </RequireReady>
    </AppShell>
  );
}

function RequiredGpaOutcome({
  result,
}: {
  result: {
    alreadyReached: boolean;
    reachable: boolean;
    currentGpa: number;
    targetGpa: number;
    requiredSemesterGpa: number;
  };
}) {
  if (result.alreadyReached) {
    return (
      <ResultSurface tone="ok">
        <DomainStatus outcome="sufficient">Ek minimum yok</DomainStatus>
        <div className="mt-4">
          <OutcomeHero
            label="Mevcut GANO"
            value={formatGpa(result.currentGpa)}
            supporting={
              <SupportStat label="Hedef" value={formatGpa(result.targetGpa)} />
            }
          />
        </div>
      </ResultSurface>
    );
  }

  if (!result.reachable) {
    return (
      <ResultSurface tone="caution">
        <DomainStatus outcome="unreachable">
          Yalnızca bu dönemle zor
        </DomainStatus>
        <div className="mt-4">
          <OutcomeHero
            label="Gerekli dönem ortalaması"
            value={formatGpa(result.requiredSemesterGpa)}
            supporting={
              <>
                <SupportStat
                  label="Hedef"
                  value={formatGpa(result.targetGpa)}
                />
                <SupportStat
                  label="Mevcut"
                  value={formatGpa(result.currentGpa)}
                />
              </>
            }
          />
        </div>
      </ResultSurface>
    );
  }

  return (
    <ResultSurface tone="ok">
      <DomainStatus outcome="reachable">Ulaşılabilir</DomainStatus>
      <div className="mt-4">
        <OutcomeHero
          label="Gerekli dönem ortalaması"
          value={formatGpa(result.requiredSemesterGpa)}
          supporting={
            <>
              <SupportStat label="Hedef" value={formatGpa(result.targetGpa)} />
              <SupportStat
                label="Mevcut"
                value={formatGpa(result.currentGpa)}
              />
            </>
          }
        />
      </div>
    </ResultSurface>
  );
}
