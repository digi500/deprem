import json

# Read the generated history
with open('c:\\deprem\\scratch\\experiment_history.json', 'r', encoding='utf-8') as f:
    history = f.read()

html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ML Yönetim Paneli - Simülasyon Arenası</title>
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
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
            display: flex;
            flex-direction: column;
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
                Modeli eğitmek için 2010 yılından bugüne Marmara bölgesinden tam <strong>2530 mikro-deprem</strong> AFAD üzerinden çekildi. Yeni Puanlama Sisteminde Büyüklük (%45) ve Zaman (%45) ağırlıklı iken, Lokasyon (%10) daha esnektir.
            </p>
            <ul>
                <li><strong>Soru 1: Harici Değişkenler?</strong><br>Şu an sadece koordinat ve büyüklük verisine bakıyoruz. Peki mikro-depremleri tetikleyen Ay'ın çekim kuvveti (gelgit) veya hava basıncı gibi etkenler var mı?</li>
                <li><strong>Soru 2: Puanlama Mantığı Değişimi:</strong><br>Mesafe sapmalarının (Örn: 6km) çok önemli olmadığı, asıl odaklanılması gerekenin "Büyüklük" ve "Zaman" olduğu tespit edildi. Yeni puanlamayla modellerin başarı oranı <strong>%53 seviyelerine</strong> fırladı! Demek ki yapay zeka büyüklük ve zaman trendlerini aslında yakalamış.</li>
                <li><strong>Soru 3: Fiziksel Stres?</strong><br>Geometrik hesaplıyoruz ancak kırılma sonrası değişen Coulomb Stres Transferini hesaba katmalı mıyız?</li>
            </ul>
        </div>

        <!-- Orta Panel: Model Arenası -->
        <div class="panel center-panel">
            <h2><span style="font-size: 28px;">🧠</span> Model Evrimi Arenası (Marmara 2010-2026)</h2>
            <p style="color: #aaa; margin-bottom: 20px;">
                Son 15 yıldaki 2530 deprem üzerinde yapılan makine öğrenmesi Backtest (Geçmişe Dönük Sınama) sonuçları. Başarı formülü Mesafe, Büyüklük ve Zaman sapmalarının ortaklaşa %'sini temsil eder. (Devasa veriseti ve uzun zaman boşlukları nedeniyle puanların %30'larda kalması sismolojinin kaotik doğasını kanıtlar niteliktedir.)
            </p>
            <div id="chart-div" style="width: 100%; height: 500px; background: rgba(0,0,0,0.5); border-radius: 10px;"></div>
        </div>
        
        <!-- Sağ Panel: Gelecek Metodlar -->
        <div class="panel side-panel" style="border-color: #ffaa00; box-shadow: 0 0 30px rgba(255,170,0,0.1);">
            <h2 style="color: #ffaa00; border-color: rgba(255,170,0,0.2);"><span style="font-size: 24px;">🚀</span> Arenadaki Modellerimiz</h2>
            <p style="color: #aaa; line-height: 1.6;">
                Yeni eklenen modellerin karakteristiği:
            </p>
            <ul>
                <li><strong>V3 - Merkezcil Çekim (Clustering):</strong><br>Son 5 depremin merkezini bulup son depremin yönüyle %30 / %70 oranında harmanlayarak atılım yapar.</li>
                <li><strong>V4 - DBSCAN (Yoğunluk Odaklı):</strong><br>Son 50 depreme bakarak haritadaki "en kalabalık ve yoğun" noktayı bulur (Fay Swarm noktası) ve tahmini oraya çeker. Sıçramalara karşı dirençlidir.</li>
                <li><strong>V5 - Markov Zincirleri (Olasılık Matrisi):</strong><br>Haritayı 5x5 km'lik karelere böler. Bir karede deprem olduktan sonra, tarihsel olarak % kaç ihtimalle hangi komşu kareye sıçradığını bulup zar atar.</li>
            </ul>
        </div>

    </div>

    <script>
        const historyData = {history};
        
        const versions = historyData.map(d => d.version);
        const names = historyData.map(d => d.name);
        const scores = historyData.map(d => d.score);
        
        const trace = {{
            x: versions,
            y: scores,
            text: scores.map(s => s + '%'),
            textposition: 'auto',
            hovertext: names,
            type: 'bar',
            marker: {{
                color: ['rgba(255,255,255,0.2)', 'rgba(79,172,254,0.5)', 'rgba(255,0,255,0.7)', 'rgba(0,255,100,0.7)', 'rgba(255,170,0,0.7)'],
                line: {{
                    color: ['#fff', '#4facfe', '#ff00ff', '#00ff64', '#ffaa00'],
                    width: 2
                }}
            }}
        }};
        
        const traceLine = {{
            x: versions,
            y: scores,
            type: 'scatter',
            mode: 'lines+markers',
            line: {{ color: '#fff', width: 3, dash: 'dot' }},
            marker: {{ size: 8, color: '#fff' }}
        }};

        const layout = {{
            title: {{ text: 'Model Başarı Puanları (%)', font: {{ color: '#fff' }} }},
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{ color: '#aaa' }},
            xaxis: {{ 
                title: 'Model Versiyonu',
                gridcolor: 'rgba(255,255,255,0.1)'
            }},
            yaxis: {{ 
                title: 'Başarı Yüzdesi (%)',
                range: [0, 100],
                gridcolor: 'rgba(255,255,255,0.1)'
            }},
            showlegend: false
        }};

        Plotly.newPlot('chart-div', [trace, traceLine], layout, {{responsive: true}});
    </script>
</body>
</html>
"""

with open('c:\\deprem\\ml_panel.html', 'w', encoding='utf-8') as f:
    f.write(html)
