import type { Metadata } from "next";
import Link from "next/link";

import {
  LegalHeading,
  LegalList,
  LegalPage,
} from "@/components/legal/LegalPage";

export const metadata: Metadata = {
  title: "Gizlilik ve Kişisel Verilerin İşlenmesi",
};

export default function PrivacyPage() {
  return (
    <LegalPage title="Gizlilik ve Kişisel Verilerin İşlenmesi">
      <p>
        GradePilot, transkriptinizi analiz ederek GANO’nuzu, derslerinizi ve
        akademik planlama senaryolarınızı görüntülemenize yardımcı olur.
      </p>
      <p>
        Yüklediğiniz transkript; ders adı, ders kodu, not, kredi/AKTS ve dönem
        gibi akademik bilgiler içerebilir. Bu bilgiler yalnızca GradePilot’un
        transkript analizi, GANO hesaplama ve akademik planlama özelliklerini
        sunabilmesi amacıyla işlenir.
      </p>
      <p>
        Yüklenen PDF dosyaları kalıcı olarak saklanmaz. Dosya analiz sırasında
        geçici olarak işlenir ve işlem tamamlandığında geçici dosya sistemden
        kaldırılır.
      </p>
      <p>
        GradePilot şu anda Google Analytics, reklam takip sistemleri veya
        harici yapay zekâ servisleri kullanmamaktadır. Transkript içeriği, ders
        bilgileriniz ve GANO değeriniz bu tür üçüncü taraf sistemlere
        gönderilmez.
      </p>
      <p>
        Sistem güvenliği ve hata takibi amacıyla sınırlı teknik bilgiler
        işlenebilir. Transkript içeriği, ders listeniz ve GANO bilgileriniz
        uygulama loglarına kaydedilmez.
      </p>
      <p>
        GradePilot’un veri işleme uygulamaları veya kişisel verilerinizle ilgili
        sorularınız için bizimle iletişime geçebilirsiniz.
      </p>

      <LegalHeading>İşlenen Veriler</LegalHeading>
      <p>Hizmeti kullanırken şu bilgiler işlenebilir:</p>
      <LegalList>
        <li>yüklediğiniz transkript dosyasının içeriği,</li>
        <li>
          ders adı, ders kodu, not, kredi/AKTS ve dönem gibi akademik bilgiler,
        </li>
        <li>
          isteği iletmek, güvenlik ve hata takibi için sınırlı teknik bilgiler.
        </li>
      </LegalList>

      <LegalHeading>İşleme Amacı</LegalHeading>
      <p>
        Bu bilgiler, transkript analizi, GANO hesaplama ve akademik planlama
        senaryolarını size gösterebilmek için işlenir. Başka bir amaçla
        kullanılmaz.
      </p>

      <LegalHeading>Dosyaların Saklanması</LegalHeading>
      <p>
        Yüklenen PDF kalıcı olarak saklanmaz. Analiz sırasında geçici olarak
        işlenir; işlem tamamlandığında geçici dosya sistemden kaldırılır.
      </p>
      <p>
        Ekranda gördüğünüz ders listesi ve hesap sonuçları, sayfa oturumu
        boyunca tarayıcınızda tutulur. GradePilot hesabına veya bir veritabanına
        kaydedilmez.
      </p>

      <LegalHeading>Üçüncü Taraflar</LegalHeading>
      <p>
        GradePilot şu anda Google Analytics, reklam takip sistemleri veya harici
        yapay zekâ servisleri kullanmamaktadır. Transkript içeriği, ders
        bilgileriniz ve GANO değeriniz bu tür sistemlere gönderilmez.
      </p>

      <LegalHeading>Tarayıcı Tercihleri</LegalHeading>
      <p>
        GradePilot, açık veya koyu tema gibi arayüz tercihini hatırlamak için
        tarayıcınızın yerel deposunu (localStorage) kullanabilir. Bu tercih
        reklam, ölçüm veya profil oluşturma amacıyla kullanılmaz. Akademik
        verileriniz çerez olarak saklanmaz.
      </p>

      <LegalHeading>Haklarınız</LegalHeading>
      <p>
        6698 sayılı Kişisel Verilerin Korunması Kanunu kapsamında kişisel
        verilerinize ilişkin bilgi talep etme, düzeltilmesini veya
        silinmesini isteme ve ilgili durumlarda itiraz etme haklarınız
        bulunabilir. Gerekirse Kişisel Verileri Koruma Kurulu’na
        başvurabilirsiniz. Bu metin bir uygunluk belgesi değildir.
      </p>

      <LegalHeading>İletişim</LegalHeading>
      <p>
        <a
          href="mailto:meteartunaltay08@gmail.com"
          className="text-accent-deep underline-offset-2 hover:underline"
        >
          meteartunaltay08@gmail.com
        </a>
      </p>
      <p className="text-sm leading-6 text-faint">
        Ayrıca bkz.{" "}
        <Link
          href="/kullanim-kosullari"
          className="text-accent-deep underline-offset-2 hover:underline"
        >
          Kullanım Koşulları
        </Link>
        .
      </p>
    </LegalPage>
  );
}
