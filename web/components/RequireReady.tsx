"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { EmptyState } from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";

export function RequireReady({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isReady } = useAppState();

  useEffect(() => {
    if (!isReady) {
      router.replace("/transkript");
    }
  }, [isReady, router]);

  if (!isReady) {
    return (
      <EmptyState
        title="Başlamak için transkriptini yükle."
        description="Bu ekranı görmek için önce bir transkript yüklemelisin."
      />
    );
  }

  return <>{children}</>;
}
