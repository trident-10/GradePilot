import { ContentFrame, PageHeader } from "@/components/ui";
import { TranscriptProcess } from "@/components/academic-loading";

export function UploadingState() {
  return (
    <ContentFrame width="narrow" className="gp-upload-enter space-y-5">
      <PageHeader
        title="Transkriptin işleniyor"
        description="Bu işlem genellikle birkaç saniye sürer."
      />
      <TranscriptProcess />
      <p className="text-center text-xs leading-5 text-faint">
        Sayfayı kapatmana gerek yok. İşlem bitince bir sonraki adıma
        geçileceksin.
      </p>
    </ContentFrame>
  );
}
