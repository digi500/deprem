import sys
import re

# Mevcut raporu extract et
with open('c:\\deprem\\ml_panel.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Rapor div'ini al
report_match = re.search(r'<div style="background: rgba\(0,0,0,0\.5\); padding: 20px; border-radius: 10px; margin-top: 20px;">(.*?)</div>\s*</div>', html, re.DOTALL)
if report_match:
    report_content = '<div style="background: rgba(0,0,0,0.5); padding: 20px; border-radius: 10px; margin-top: 20px;">' + report_match.group(1) + '</div>'
else:
    # Just read from backtest_report.html
    with open('c:\\deprem\\scratch\\backtest_report.html', 'r', encoding='utf-8') as f2:
        report_content = f2.read()

new_html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ML Yönetim Paneli</title>
    <style>
        body {{
            background-color: #050510;
            color: #fff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            min-height: 100vh;
        }}
        .layout-wrapper {{
            display: flex;
            gap: 20px;
            width: 100%;
            max-width: 1600px;
            box-sizing: border-box;
        }}
        .panel {{
            background: rgba(15, 10, 25, 0.95);
            border: 1px solid rgba(255,0,255,0.4);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 0 30px rgba(255,0,255,0.1);
        }}
        .side-panel {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 20px;
            opacity: 0.9;
        }}
        .center-panel {{
            flex: 2;
        }}
        h2 {{
            color: #ff00ff;
            margin-top: 0;
            border-bottom: 1px solid rgba(255,0,255,0.2);
            padding-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        h3 {{
            color: #4facfe;
            margin-top: 0;
        }}
        ul {{
            padding-left: 20px;
            line-height: 1.7;
            color: #ccc;
        }}
        li {{
            margin-bottom: 15px;
        }}
        strong {{
            color: #fff;
        }}
    </style>
</head>
<body>
    <div class="layout-wrapper">
        
        <!-- Sol Panel: Analiz ve Keşif -->
        <div class="panel side-panel" style="border-color: #4facfe; box-shadow: 0 0 30px rgba(79,172,254,0.1);">
            <h2 style="color: #4facfe; border-color: rgba(79,172,254,0.2);"><span style="font-size: 24px;">📊</span> Veri Yeterliliği ve Sorular</h2>
            <p style="color: #aaa; line-height: 1.6;">
                Modeli eğitmek için veritabanımızdaki <strong>74 mikro-deprem</strong> oldukça kısıtlı bir veri setidir. 
                Gerçek bir derin öğrenme (Deep Learning) modelinin genelleme yapabilmesi için on binlerce sismik olaya ihtiyaç vardır.
            </p>
            <ul>
                <li><strong>Soru 1: Harici Değişkenler?</strong><br>Şu an sadece koordinat ve büyüklük verisine bakıyoruz. Peki mikro-depremleri tetikleyen Ay'ın çekim kuvveti (gelgit) veya hava basıncı gibi etkenler var mı?</li>
                <li><strong>Soru 2: Derinlik (Z Ekseni) Yanılgısı?</strong><br>Kandilli bazen belirsiz depremlerde derinliği standart 5.0 veya 7.0 km olarak giriyor. Bu durum modelimizin 3D uzay algısını (Dip/Eğim) yanıltıyor olabilir mi?</li>
                <li><strong>Soru 3: Fiziksel Stres?</strong><br>Geometrik regresyon hesaplıyoruz ancak kırılma sonrası değişen <em>Coulomb Stres Transferini (Fiziksel gerilim)</em> hesaba katmalı mıyız?</li>
                <li><strong>Soru 4: Kümelenme Limiti?</strong><br>V3'teki Merkezcil Çekim çok başarılı oldu ancak kovan ne zaman dağılır ve başka bir faya sıçrar?</li>
            </ul>
        </div>

        <!-- Orta Panel: Backtest Sonuçları -->
        <div class="panel center-panel">
            <h2><span style="font-size: 28px;">🧠</span> ML Yönetim Paneli</h2>
            
            <div style="opacity: 0.9;">
                {report_content}
            </div>
        </div>
        
        <!-- Sağ Panel: Gelecek Metodlar -->
        <div class="panel side-panel" style="border-color: #ffaa00; box-shadow: 0 0 30px rgba(255,170,0,0.1);">
            <h2 style="color: #ffaa00; border-color: rgba(255,170,0,0.2);"><span style="font-size: 24px;">🚀</span> Gelecek Metodlar (V4)</h2>
            <p style="color: #aaa; line-height: 1.6;">
                Sismoloji ve Yapay Zeka sınırlarını zorlamak için planladığım sıradaki devrimsel güncellemeler:
            </p>
            <ul>
                <li><strong>Zaman Serisi Ağları (LSTM/GRU):</strong><br>RNN tabanlı derin öğrenme mimarileri kurarak depremlerin zaman içindeki gizli "Hafıza" desenlerini çözmek. Geleneksel regresyonun ötesine geçmek.</li>
                <li><strong>Gutenberg-Richter Entegrasyonu:</strong><br>Bölgenin spesifik b-değerini hesaplayıp, mikro deprem yoğunluğuna (tıkırtılara) bakarak büyük bir depremin (Ana Şok) gelme olasılığını matematiksel olarak tahmin etmek.</li>
                <li><strong>Yapay Zeka Kümeleme (DBSCAN):</strong><br>Körlemesine son 5 depreme bakmak yerine, aktif mikro-fay segmentlerini (swarm) yapay zeka ile otomatik haritalandırmak.</li>
                <li><strong>Markov Zincirleri:</strong><br>Depremlerin bir lokasyondan diğerine zıplama ihtimallerini "Stokastik Olasılık Matrisleri" ile hesaplamak.</li>
            </ul>
        </div>

    </div>
</body>
</html>
"""

with open('c:\\deprem\\ml_panel.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
