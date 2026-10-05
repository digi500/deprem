# Katkıda Bulunma Rehberi (Contributing Guidelines)

Marmara Deprem Simülasyonu ve İstatistiksel Analiz Projesi'ne katkıda bulunmak istediğiniz için teşekkür ederiz!

Proje açık kaynaklıdır ve topluluk katkılarına açıktır. Katkılarınızın düzenli ve güvenli bir şekilde entegre edilebilmesi için lütfen aşağıdaki kurallara dikkat ediniz.

---

## 🔒 1. Kesin Güvenlik Kuralı: Gizli Anahtar ve Parolalar
* Kod içerisine **kesinlikle** kişisel API anahtarı, Supabase `service_role` anahtarı, veritabanı parolası veya e-posta/SMTP şifresi yazmayınız.
* Hassas veriler yalnızca GitHub Secrets ve ortam değişkenleri (`os.environ`) üzerinden okunur.
* İçinde gizli bilgi veya yetkisiz erişim anahtarı bulunan Pull Request'ler incelenmeden derhal kapatılır.

---

## 🔍 2. İnceleme Süreci (Code Review)
* Gönderilen tüm Pull Request'ler (PR), proje yöneticisi ve yapay zeka denetim mekanizması (Claude & Gemini ikili kontrolü) tarafından detaylıca incelenir.
* Kodun güvenliği, bağımlılıkları ve mimariye uyumu doğrulandıktan sonra ana dala (`main`) kabul edilir.

---

## 🚀 3. Katkı Adımları
1. Bu depoyu kendi GitHub hesabınıza çatallayın (**Fork**).
2. İlgili konuya odaklanan yeni bir dal (branch) açın:
   ```bash
   git checkout -b ozellik/iyilestirme-adi
   ```
3. Kod değişikliklerinizi yapın ve yerelde test edin.
4. Anlaşılır bir commit mesajı ile kaydedin.
5. Dalınızı GitHub'a push edin ve ana depoya karşı bir **Pull Request** oluşturun.

---

## 💬 4. İletişim ve Fikirler
Yeni bir özellik önermek veya bir hatayı tartışmak için önce [GitHub Discussions](https://github.com/digi500/deprem/discussions) alanında başlık açmanız önerilir.
