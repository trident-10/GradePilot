import { ContentFrame, PageHeader } from "@/components/ui";
import { TranscriptProcess } from "@/components/academic-loading";

export function UploadingState() {
  return (
    <ContentFrame width="narrow">
      <PageHeader
        title="Transkript hazırlanıyor"
        description="Derslerin ve akademik bilgilerin işleniyor."
      />
      <TranscriptProcess />
    </ContentFrame>
  );
}
