import type { Metadata } from "next";
import Link from "next/link";

import { LegalHeading, LegalPage } from "@/components/legal/LegalPage";

export const metadata: Metadata = {
  title: "Kullanım Koşulları",
};

export default function TermsPage() {
  return (
    <LegalPage title="Kullanım Koşulları">
      <p>
        GradePilot, öğrencilerin akademik durumlarını anlamalarına ve farklı
        not senaryolarını değerlendirmelerine yardımcı olmak amacıyla
        geliştirilmiş bir akademik planlama aracıdır.
      </p>

      <LegalHeading>Hizmetin Amacı</LegalHeading>
      <p>
        GradePilot, yüklediğiniz transkripte göre GANO, dersler ve planlama
        senaryolarını görüntülemenize yardımcı olur. Resmi bir kayıt veya
        danışmanlık hizmeti değildir.
      </p>

      <LegalHeading>Akademik Sonuçların Niteliği</LegalHeading>
      <p>
        GradePilot tarafından gösterilen GANO hesaplamaları, ders etkileri ve
        gelecek dönem senaryoları bilgilendirme ve planlama amaçlıdır.
        GradePilot resmi bir üniversite öğrenci bilgi sistemi değildir ve
        üniversitenizin resmi transkriptinin veya akademik danışmanınızın yerine
        geçmez.
      </p>
      <p>
        Üniversitelerin not hesaplama, ders tekrarı, kredi, AKTS ve mezuniyet
        kuralları farklılık gösterebilir. Bu nedenle önemli akademik kararlar
        almadan önce sonuçları üniversitenizin resmi yönetmelikleri ve öğrenci
        bilgi sistemi üzerinden doğrulamanız önerilir.
      </p>

      <LegalHeading>Kullanıcının Sorumluluğu</LegalHeading>
      <p>
        GradePilot’a yüklediğiniz belgelerin kullanım hakkına sahip olmanız ve
        başkalarına ait belgeleri izinsiz yüklememeniz gerekir.
      </p>

      <LegalHeading>Kabul Edilebilir Kullanım</LegalHeading>
      <p>
        Hizmetin güvenliğini veya çalışmasını bozmayı amaçlayan otomatik, kötü
        niyetli veya aşırı kullanım yasaktır.
      </p>

      <LegalHeading>Hizmet Sınırları</LegalHeading>
      <p>
        GradePilot’un doğru sonuç üretmesi için gerekli kontroller yapılmakla
        birlikte yazılım hataları, eksik transkript format desteği veya
        üniversiteye özgü kurallar nedeniyle sonuçlarda farklılık oluşabilir.
      </p>

      <p className="text-sm leading-6 text-faint">
        Kişisel veriler için bkz.{" "}
        <Link
          href="/gizlilik"
          className="text-accent-deep underline-offset-2 hover:underline"
        >
          Gizlilik ve Kişisel Verilerin İşlenmesi
        </Link>
        .
      </p>
    </LegalPage>
  );
}
