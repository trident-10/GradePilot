"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAppState } from "@/context/AppStateContext";

export default function HomePage() {
  const router = useRouter();
  const { isReady } = useAppState();

  useEffect(() => {
    router.replace(isReady ? "/genel-bakis" : "/transkript");
  }, [isReady, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg text-sm text-muted">
      Yönlendiriliyor…
    </div>
  );
}
