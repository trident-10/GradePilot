"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { ContentFrame, PrimaryButton } from "@/components/ui";
import { useAppState } from "@/context/AppStateContext";
import { cx } from "@/lib/display";

const VALUE_POINTS = [
  { title: "GANO Analizi", body: "Mevcut not ortalamanı ve dönemlerini net gör." },
  {
    title: "Ders Etkisi",
    body: "Bir not yükselince GANO’nun nasıl değişeceğini incele.",
  },
  {
    title: "Akademik Planlama",
    body: "Hedefin için senaryolar ve gelecek dönem planı kur.",
  },
] as const;

export function UploadStart() {
  const inputRef = useRef<HTMLInputElement>(null);
  const { isBusy, uploadFile } = useAppState();
  const [dragging, setDragging] = useState(false);
  const [termsRead, setTermsRead] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);

  function acceptFile(file: File | undefined | null) {
    if (!file || !termsAccepted) return;
    void uploadFile(file);
  }

  useEffect(() => {
    if (process.env.NODE_ENV === "production") return;
    const w = window as Window & {
      __gradePilotUploadFile?: (file: File) => void;
    };
    w.__gradePilotUploadFile = (file: File) => {
      setTermsAccepted(true);
      void uploadFile(file);
    };
    return () => {
      delete w.__gradePilotUploadFile;
    };
  }, [uploadFile]);

  return (
    <ContentFrame width="narrow" className="my-auto space-y-8">
      <div className="gp-enter">
        <h1 className="font-display text-[1.8rem] font-semibold leading-tight tracking-[-0.035em] text-ink sm:text-[2rem] md:text-[2.2rem]">
          Transkriptini yükle, akademik durumunu planla.
        </h1>
        <p className="mt-3 text-[15px] leading-7 text-muted">
          GANO’nu incele, derslerinin etkisini gör ve hedeflerin için senaryolar
          oluştur.
        </p>
      </div>

      {!termsAccepted ? (
        <div className="gp-enter-delay rounded-[14px] border border-rule bg-surface px-5 py-6 text-left sm:py-8">
          <p className="text-base font-semibold text-ink">Devam etmeden önce</p>
          <p className="mt-2 text-sm leading-6 text-muted">
            Transkriptini yüklemeden önce verilerinin nasıl işlendiğini
            inceleyebilir ve GradePilot Kullanım Koşulları’nı okuyabilirsin.
          </p>
          <div className="mt-4 flex items-start gap-3 text-sm leading-6 text-ink">
            <input
              id="transcript-terms-ack"
              type="checkbox"
              checked={termsRead}
              onChange={(event) => setTermsRead(event.target.checked)}
              aria-label="Gizlilik Bildirimi’ni okudum ve Kullanım Koşulları’nı kabul ediyorum."
              className="mt-1 size-4 shrink-0 rounded border-rule accent-accent"
            />
            <span className="min-w-0 break-words">
              <Link
                href="/gizlilik"
                className="text-accent-deep underline-offset-2 hover:underline"
              >
                Gizlilik Bildirimi
              </Link>
              <label htmlFor="transcript-terms-ack" className="cursor-pointer">
                ’ni okudum ve{" "}
              </label>
              <Link
                href="/kullanim-kosullari"
                className="text-accent-deep underline-offset-2 hover:underline"
              >
                Kullanım Koşulları
              </Link>
              <label htmlFor="transcript-terms-ack" className="cursor-pointer">
                ’nı kabul ediyorum.
              </label>
            </span>
          </div>
          <PrimaryButton
            type="button"
            className="mt-5 h-11 w-full px-5 sm:w-auto"
            disabled={!termsRead}
            onClick={() => setTermsAccepted(true)}
          >
            Devam Et
          </PrimaryButton>
        </div>
      ) : (
        <div
          onDragEnter={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            setDragging(false);
          }}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            acceptFile(event.dataTransfer.files?.[0]);
          }}
          className={cx(
            "gp-enter-delay rounded-[14px] border border-dashed bg-surface px-5 py-8 text-center gp-lift",
            dragging ? "border-accent bg-accent-soft/50" : "border-rule",
          )}
        >
          <div
            className="mx-auto flex size-11 items-center justify-center rounded-[10px] border border-rule bg-bg text-accent-deep"
            aria-hidden
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path
                d="M7 3.75h6.5L19 9.25V20.25a.75.75 0 0 1-.75.75H7.75A.75.75 0 0 1 7 20.25V3.75Z"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <path
                d="M13.5 3.75V9h5.5"
                stroke="currentColor"
                strokeWidth="1.5"
              />
            </svg>
          </div>
          <p className="mt-4 text-base font-semibold text-ink">
            Transkript PDF’ini yükle
          </p>
          <p className="mt-1 text-sm leading-6 text-muted">
            Dosyanı buraya sürükle veya bilgisayarından seç.
          </p>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            className="hidden"
            onChange={(event) => {
              acceptFile(event.target.files?.[0]);
              event.target.value = "";
            }}
          />
          <PrimaryButton
            type="button"
            disabled={isBusy}
            onClick={() => inputRef.current?.click()}
            className="mt-5 h-11 px-5"
          >
            {isBusy ? "Hazırlanıyor" : "Transkript Yükle"}
          </PrimaryButton>
          <p className="mt-4 text-xs text-faint">
            PDF · Maks. 10 MB · Maks. 50 sayfa
          </p>
        </div>
      )}

      <ul className="grid gap-x-6 gap-y-4 sm:grid-cols-3">
        {VALUE_POINTS.map((item, index) => (
          <li
            key={item.title}
            className="border-t border-rule pt-3 gp-enter"
            style={{ animationDelay: `${80 + index * 40}ms` }}
          >
            <p className="text-sm font-semibold text-ink">{item.title}</p>
            <p className="mt-1 text-xs leading-5 text-muted">{item.body}</p>
          </li>
        ))}
      </ul>

      <p className="text-center text-xs leading-5 text-faint">
        Dosyan analiz için işlenir ve işlem tamamlandığında kaldırılır.{" "}
        <Link
          href="/gizlilik"
          className="text-muted underline-offset-2 hover:text-ink hover:underline"
        >
          Gizlilik
        </Link>
      </p>
    </ContentFrame>
  );
}
