import json

def generate_html():
    with open('earthquakes.json', 'r', encoding='utf-8') as f:
        earthquakes = json.load(f)
        
    html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marmara / Adalar Bölgesi 3 Boyutlu Deprem Aktivitesi</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #050510;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
        }}
        #plot-container {{
            width: 100vw;
            height: 100vh;
        }}
        
        #data-list {{
            position: absolute; 
            top: 20px; 
            right: 20px; 
            width: 380px; 
            height: 85vh; 
            overflow-y: auto; 
            background: rgba(10,15,30,0.85); 
            border-radius: 8px; 
            color: #ddd; 
            font-size: 13px; 
            padding: 15px; 
            border: 1px solid rgba(100,150,255,0.3); 
            z-index: 1000; 
            display: flex; 
            flex-direction: column;
            box-shadow: -5px 5px 20px rgba(0,0,0,0.5);
            backdrop-filter: blur(10px);
        }}
        
        #data-list h3 {{
            color: #4facfe; 
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.2rem;
            text-align: center;
        }}
        
        table {{
            width: 100%; 
            border-collapse: collapse;
        }}
        
        th {{
            border-bottom: 2px solid #555; 
            text-align: left;
            padding-bottom: 8px;
            color: #aaa;
        }}
        
        td {{
            padding: 6px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: rgba(0,0,0,0.2); 
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #4facfe; 
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div id="plot-container"></div>
    
    <div id="data-list">
        <h3>Sismik Aktivite & Tahminler</h3>
        <table>
            <thead>
                <tr>
                    <th>Zaman/Durum</th><th>Enlem</th><th>Boylam</th><th>Der.</th><th>Mag</th>
                </tr>
            </thead>
            <tbody id="data-table-body">
            </tbody>
        </table>
    </div>

    <script>
        const rawData = {json.dumps(earthquakes)};
        
        const data = rawData.filter(d => 
            d.lat >= 40.75 && d.lat <= 40.85 && 
            d.lon >= 29.00 && d.lon <= 29.20
        );

        data.sort((a, b) => new Date(a.date) - new Date(b.date));

        const lats = data.map(d => d.lat);
        const lons = data.map(d => d.lon);
        const depths = data.map(d => -d.depth); 
        const mags = data.map(d => Math.max(d.mag, 0.5)); 
        const hoverTexts = data.map(d => `Tarih: ${{d.date.replace('T', ' ')}}<br>Büyüklük: ${{d.mag}}<br>Derinlik: ${{d.depth}} km<br>Konum: ${{d.location}}`);

        const N = data.length;
        const realPointLabels = data.map((d, i) => i === (N - 1) ? '1' : '');

        const trace = {{
            x: lons, y: lats, z: depths,
            mode: 'markers+text',
            marker: {{
                size: mags.map(m => m * 4), 
                color: depths, 
                colorscale: 'Jet', 
                opacity: 0.8,
                symbol: 'circle',
                line: {{ color: 'rgba(255, 255, 255, 0.5)', width: 1 }}
            }},
            text: realPointLabels,
            textfont: {{ size: 24, color: 'white' }},
            textposition: 'top center',
            hovertext: hoverTexts,
            hoverinfo: 'text',
            type: 'scatter3d'
        }};

        // Kesik Üçgenler (Disjoint)
        const i_indices = [];
        const j_indices = [];
        const k_indices = [];
        const intensities = []; 

        const numTriangles = Math.floor(N / 3);
        const remainder = N % 3;

        for (let t = 0; t < numTriangles; t++) {{
            i_indices.push(t * 3);
            j_indices.push(t * 3 + 1);
            k_indices.push(t * 3 + 2);
            intensities.push(t); 
        }}

        // --- Gelişmiş Morfolojik Tahmin (Prediction) Motoru ---
        
        // 1. Ortalama adım mesafesini (üçgen boyutunu) bulalım
        let totalDist = 0;
        for(let i=1; i<N; i++) {{
            totalDist += Math.sqrt(Math.pow(lons[i]-lons[i-1], 2) + Math.pow(lats[i]-lats[i-1], 2) + Math.pow(depths[i]-depths[i-1], 2));
        }}
        const avgStep = totalDist / (N - 1);

        // 2. Fayın son ilerleyiş yönünü bulalım (Son 4 nokta arası vektör)
        const lookBack = Math.min(4, N);
        let dirX = lons[N-1] - lons[N-lookBack];
        let dirY = lats[N-1] - lats[N-lookBack];
        let dirZ = depths[N-1] - depths[N-lookBack];
        
        let dirLen = Math.sqrt(dirX*dirX + dirY*dirY + dirZ*dirZ);
        if(dirLen === 0) {{ dirX=0.01; dirY=0; dirZ=0; dirLen=0.01; }}
        dirX /= dirLen; dirY /= dirLen; dirZ /= dirLen;

        const predLats = [];
        const predLons = [];
        const predDepths = [];
        const predTexts = [];
        
        let lastLon = lons[N-1];
        let lastLat = lats[N-1];
        let lastDepth = depths[N-1];
        let lastMag = data[N-1].mag;

        const pointsToPredict = remainder === 0 ? 3 : (3 - remainder); 
        
        // Geometrik olarak dağılmış bir üçgen tahmini (düz çizgi olmaması için)
        // Nokta 1: Yön vektöründe ileri
        let p1x = lastLon + dirX * avgStep;
        let p1y = lastLat + dirY * avgStep;
        let p1z = lastDepth + dirZ * avgStep;
        
        // Nokta 2: Yöne dik (orthogonal) sağa doğru açılan
        let p2x = p1x + (-dirY) * avgStep * 0.8; 
        let p2y = p1y + (dirX) * avgStep * 0.8;
        let p2z = p1z + (dirZ) * avgStep + (Math.random() - 0.5) * avgStep;
        
        // Nokta 3: Yöne dik sola doğru açılan
        let p3x = p1x + (dirY) * avgStep * 0.8;
        let p3y = p1y + (-dirX) * avgStep * 0.8;
        let p3z = p1z + (dirZ) * avgStep + (Math.random() - 0.5) * avgStep;
        
        const predictedCoords = [
            {{x: p1x, y: p1y, z: p1z}},
            {{x: p2x, y: p2y, z: p2z}},
            {{x: p3x, y: p3y, z: p3z}}
        ];
        
        for(let p = 0; p < pointsToPredict; p++) {{
            predLons.push(predictedCoords[p].x);
            predLats.push(predictedCoords[p].y);
            predDepths.push(predictedCoords[p].z);
            predTexts.push((p + 2).toString() + '?');
        }}

        const pred_i = [];
        const pred_j = [];
        const pred_k = [];
        let startIdx = N; 

        if (remainder === 1) {{
            pred_i.push(N - 1); 
            pred_j.push(startIdx); 
            pred_k.push(startIdx + 1); 
        }} else if (remainder === 2) {{
            pred_i.push(N - 2); 
            pred_j.push(N - 1); 
            pred_k.push(startIdx); 
        }} else if (remainder === 0) {{
            pred_i.push(startIdx); 
            pred_j.push(startIdx + 1); 
            pred_k.push(startIdx + 2); 
        }}

        const allLons = [...lons, ...predLons];
        const allLats = [...lats, ...predLats];
        const allDepths = [...depths, ...predDepths];

        const traceRealMesh = {{
            x: allLons, y: allLats, z: allDepths,
            i: i_indices, j: j_indices, k: k_indices,
            intensity: intensities, intensitymode: 'cell', colorscale: 'Jet',
            opacity: 0.6, type: 'mesh3d', name: 'Tamamlanmış Kırıklar', hoverinfo: 'skip'
        }};

        const tracePredMesh = {{
            x: allLons, y: allLats, z: allDepths,
            i: pred_i, j: pred_j, k: pred_k,
            color: 'rgba(255, 0, 255, 0.8)', 
            opacity: 0.9, type: 'mesh3d', name: 'Tahmini Kırılma Yönü', hoverinfo: 'skip'
        }};

        const tracePredPoints = {{
            x: predLons, y: predLats, z: predDepths,
            mode: 'markers+text',
            marker: {{ size: 8, color: '#ff00ff', symbol: 'diamond' }},
            text: predTexts, 
            textfont: {{ size: 24, color: 'white' }},
            hovertext: predTexts.map(t => 'Tahmin: ' + t), hoverinfo: 'text',
            type: 'scatter3d', name: 'Tahmin Edilen Noktalar'
        }};

        // Yüzey
        const minLon = Math.min(...lons) - 0.02;
        const maxLon = Math.max(...lons) + 0.02;
        const minLat = Math.min(...lats) - 0.02;
        const maxLat = Math.max(...lats) + 0.02;
        const surface = {{
            x: [minLon, minLon, maxLon, maxLon],
            y: [minLat, maxLat, minLat, maxLat],
            z: [0, 0, 0, 0],
            opacity: 0.2, color: 'rgba(0, 150, 255, 0.5)', type: 'mesh3d', name: 'Deniz Yüzeyi', hoverinfo: 'name'
        }};

        const layout = {{
            margin: {{ l: 0, r: 0, b: 0, t: 0 }},
            paper_bgcolor: '#050510',
            scene: {{
                xaxis: {{ title: 'Boylam (Longitude)', color: '#aaaaaa', gridcolor: '#222233', zerolinecolor: '#444455', showbackground: false }},
                yaxis: {{ title: 'Enlem (Latitude)', color: '#aaaaaa', gridcolor: '#222233', zerolinecolor: '#444455', showbackground: false }},
                zaxis: {{ title: 'Derinlik (km)', color: '#aaaaaa', gridcolor: '#222233', zerolinecolor: '#444455', range: [-30, 5], showbackground: false }},
                camera: {{ eye: {{ x: 1.5, y: -1.5, z: 0.5 }} }},
                aspectmode: 'cube'
            }}
        }};

        const config = {{ responsive: true, displayModeBar: true, displaylogo: false }};
        Plotly.newPlot('plot-container', [surface, traceRealMesh, tracePredMesh, trace, tracePredPoints], layout, config);

        // --- Sağdaki Tabloyu Doldurma ---
        const tbody = document.getElementById('data-table-body');
        let rowsHtml = '';
        
        // Önce Tahmin Edilen Noktalar (En Üste)
        for (let p = pointsToPredict - 1; p >= 0; p--) {{
            rowsHtml += `<tr style="color: #ff00ff; font-weight: bold;">
                <td>Tahmin ${{predTexts[p]}}</td>
                <td>${{predLats[p].toFixed(4)}}</td>
                <td>${{predLons[p].toFixed(4)}}</td>
                <td>${{Math.abs(predDepths[p]).toFixed(1)}}</td>
                <td>${{lastMag.toFixed(1)}} (Vars.)</td>
            </tr>`;
        }}
        
        // Sonra Gerçek Noktalar (Yeniden Eskiye, N-1'den 0'a doğru)
        for (let i = N - 1; i >= 0; i--) {{
            let d = data[i];
            let dStr = d.date.replace('T', ' ');
            let shortDate = dStr.substring(5, 16); // Örn: 08-19 21:36
            
            // Eğer sonuncu depremse 1 numaralı etiketi satırda da gösterelim
            let dateLabel = (i === N - 1) ? `<span style="background: white; color: black; padding: 2px 6px; border-radius: 50%; font-weight: bold; margin-right: 5px;">1</span>` + shortDate : shortDate;
            
            rowsHtml += `<tr>
                <td>${{dateLabel}}</td>
                <td>${{d.lat.toFixed(4)}}</td>
                <td>${{d.lon.toFixed(4)}}</td>
                <td>${{d.depth.toFixed(1)}}</td>
                <td>${{d.mag.toFixed(1)}}</td>
            </tr>`;
        }}
        tbody.innerHTML = rowsHtml;
        
    </script>
    <!-- Canlı Ülke Bayraklı Ziyaretçi Sayacı -->
    <script src="visitor-counter.js"></script>
</body>
</html>"""
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print("index.html created successfully.")

if __name__ == "__main__":
    generate_html()
