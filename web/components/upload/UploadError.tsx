"use client";

import { ErrorCard } from "@/components/feedback/ErrorCard";
import { ContentFrame } from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { toUserFacingError } from "@/lib/errorModel";

export function UploadError() {
  const { error, clearError, retryUpload } = useAppState();

  return (
    <ContentFrame width="narrow" className="gp-upload-enter">
      <ErrorCard
        error={error ?? toUserFacingError(new Error("Missing error state"))}
        onRetry={retryUpload}
        onStartOver={clearError}
      />
    </ContentFrame>
  );
}
