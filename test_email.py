import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_test():
    smtp_email = os.environ.get("SMTP_EMAIL", "digitalist500@gmail.com")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    print(f"Gönderici E-posta: {smtp_email}")
    if not smtp_password:
        raise ValueError("HATA: SMTP_PASSWORD secret değeri bulunamadı! Lütfen GitHub Secrets ayarını kontrol edin.")

    smtp_password = smtp_password.replace(" ", "").strip()
    recipients = ["digitalist500@gmail.com", "filizyilmaz2008@gmail.com"]

    msg = MIMEMultipart()
    msg["From"] = f"Marmara Deprem AI Botu <{smtp_email}>"
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = "✅ Marmara Deprem AI - E-Posta Bildirim Testi Başarılı!"

    html_content = """
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; border: 1px solid #4caf50; border-radius: 8px; padding: 20px; margin: auto;">
        <div style="background-color: #4caf50; color: white; padding: 12px; border-radius: 6px; text-align: center;">
            <h2 style="margin: 0; font-size: 20px;">✅ E-POSTA BİLDİRİM TESTİ BAŞARILI</h2>
        </div>
        <p style="margin-top: 15px; font-size: 15px;">Merhaba,</p>
        <p style="font-size: 15px;">
            Marmara Deprem Simülasyonu ve Yapay Zeka Tahmin Sistemi'nin e-posta bildirim entegrasyonu başarıyla kuruldu ve test edildi.
        </p>
        <div style="background-color: #f4fbf4; border-left: 4px solid #4caf50; padding: 12px; margin: 15px 0;">
            <strong>🎯 Aktif Kural:</strong> Sistemimiz Kandilli verilerini takip ederken <strong>M4.0 ve üzeri</strong> büyüklükte bir deprem tahmini ürettiğinde bu adrese anında detaylı alarm gönderecektir.
        </div>
        <p style="font-size: 13px; color: #666; margin-top: 20px;">
            Alıcılar: digitalist500@gmail.com, filizyilmaz2008@gmail.com<br>
            Durum: 7/24 Bulutta Aktif
        </p>
    </div>
    """
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, recipients, msg.as_string())

    print(f"Test e-postası başarıyla gönderildi -> {recipients}")

if __name__ == "__main__":
    send_test()
