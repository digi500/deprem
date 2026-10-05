# Marmara Deprem Simülasyonu & İstatistiksel Tahmin Sistemi (3D)

> **⚠️ ÖNEMLİ YASAL UYARI VE BİLGİLENDİRME**  
> Bu proje, Marmara Denizi ve çevresindeki sismik hareketlilik verileri üzerinde makine öğrenimi ve istatistiksel modellerin incelenmesini amaçlayan **tamamen akademik/deneysel açık kaynaklı bir Ar-Ge çalışmasıdır**.  
> **Burada üretilen tahminler resmi bir deprem tahmini veya erken uyarı DEĞİLDİR.**  
> Deprem ve afet durumlarında yalnızca yetkili kurumların (**T.C. İçişleri Bakanlığı AFAD** ve **Boğaziçi Üniversitesi Kandilli Rasathanesi**) resmi duyuru, rapor ve uyarılarını takip ediniz.

---

## 🌐 Canlı Uygulama
Simülasyon ve görselleştirme arayüzüne doğrudan web tarayıcınızdan erişebilirsiniz:  
👉 **[https://digi500.github.io/deprem/](https://digi500.github.io/deprem/)**

---

## 📋 Proje Hakkında
Bu çalışma, Kandilli Rasathanesi tarafından yayımlanan güncel sismik verileri kullanarak:
* Marmara fay segmentleri üzerindeki mikro-depremleri 3 boyutlu derinlik/koordinat uzayında modeller,
* Coulomb gerilim transferi ve sismisite kümeleme yaklaşımlarını analiz eder,
* İstatistiksel/makine öğrenmesi algoritmalarıyla olası sonraki sismik olaylar için matematiksel modeller üretir ve geçmişe dönük hata paylarını hesaplar.

### 🏗️ Sistem Mimarisi
Proje, tamamen sunucusuz ve açık kaynak altyapılarla sürdürülebilir şekilde tasarlanmıştır:
* **Ön Yüz (Frontend):** GitHub Pages üzerinde statik HTML5, CSS3, JavaScript ve Plotly.js 3D görselleştirme kütüphanesi.
* **Veri Motoru (Engine):** GitHub Actions zamanlayıcısı ile düzenli çalışan Python veri işleme motoru (`updater.py`).
* **Veritabanı:** Supabase PostgreSQL (PostgREST API & RLS güvenlik katmanı).

### 📡 Veri Kaynakları
* **Boğaziçi Üniversitesi Kandilli Rasathanesi ve Deprem Araştırma Enstitüsü (KRDAE):** Canlı son depremler akışı.

---

## 💬 Topluluk & Tartışmalar
Görüş, öneri veya model geliştirme fikirlerinizi GitHub Discussions üzerinden paylaşabilirsiniz:  
👉 **[GitHub Discussions](https://github.com/digi500/deprem/discussions)**

---

## 🤝 Katkıda Bulunma
Açık kaynak katkılarınızı memnuniyetle karşılıyoruz!  
Detaylı bilgi ve kurallar için lütfen [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını inceleyin.

Kısaca:
1. Depoyu Fork'layın (`Fork`).
2. Kendi özellik/düzeltme dalınızı oluşturun (`git checkout -b ozellik/yeni-model`).
3. Değişikliklerinizi yapın (Asla gizli anahtar/token eklemeyin).
4. Bir Pull Request (PR) açın.

---

## 🌍 English Summary

### Marmara Earthquake 3D Simulation & Experimental Statistical Model

**Disclaimer:** This is strictly an experimental and academic open-source research project applying machine learning and statistical physics algorithms to seismic observation data in the Sea of Marmara region. **It is NOT an official earthquake prediction or warning system.** For official information and emergency warnings, please rely exclusively on official authorities: [AFAD](https://www.afad.gov.tr/) and [Kandilli Observatory](http://www.koeri.boun.edu.tr/).

* **Live Demo:** [https://digi500.github.io/deprem/](https://digi500.github.io/deprem/)
* **Architecture:** GitHub Pages (Static Web UI) + GitHub Actions (Python Data Updater) + Supabase (Database & REST API).
* **Contributions:** We welcome open-source contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
