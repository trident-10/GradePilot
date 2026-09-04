"use client";

import {
  ContentFrame,
  GhostButton,
  InlineNotice,
  PageHeader,
  PrimaryButton,
} from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";

export function UploadError() {
  const { errorMessage, clearError, resetTranscript } = useAppState();

  return (
    <ContentFrame width="narrow">
      <PageHeader
        title="Transkript işlenemedi"
        description="Dosya okunamadı. PDF olduğunu ve boyutun 10 MB’ı geçmediğini kontrol edip yeniden dene."
      />
      <InlineNotice tone="error">
        {errorMessage ?? "Bilinmeyen bir hata oluştu."}
      </InlineNotice>
      <div className="flex flex-wrap gap-3">
        <PrimaryButton type="button" onClick={clearError}>
          Tekrar dene
        </PrimaryButton>
        <GhostButton type="button" onClick={resetTranscript}>
          Baştan başla
        </GhostButton>
      </div>
    </ContentFrame>
  );
}
