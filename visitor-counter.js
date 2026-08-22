/**
 * Canlı Bayraklı Ziyaretçi Sayacı (Live Country Visitor Counter)
 * Marmara Deprem Simülasyonu İçin Özel Supabase Tabanlı Sayaç
 */
(function() {
    const SUPABASE_URL = "https://tiykapksaboucamusmbk.supabase.co";
    const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpeWthcGtzYWJvdWNhbXVzbWJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcxNjUyMjEsImV4cCI6MjEwMjc0MTIyMX0.D2YkQaF5Gfn49bsRpuoi3W1upoFfhGxdFQ-pBRW6IAM";

    const regionNames = (typeof Intl !== 'undefined' && Intl.DisplayNames) ? new Intl.DisplayNames(['tr'], { type: 'region' }) : null;

    function getCountryName(code) {
        if (!code) return 'Bilinmiyor';
        try {
            return regionNames ? regionNames.of(code.toUpperCase()) : code;
        } catch (e) {
            return code;
        }
    }

    function initCounter() {
        if (document.getElementById('live-visitor-counter')) return;

        // CSS Stillerini Enjekte Et
        if (!document.getElementById('visitor-counter-styles')) {
            const style = document.createElement('style');
            style.id = 'visitor-counter-styles';
            style.innerHTML = `
                .vc-container {
                    position: fixed;
                    bottom: 12px;
                    left: 50%;
                    transform: translateX(-50%);
                    z-index: 99999;
                    background: rgba(10, 15, 30, 0.92);
                    border: 1px solid rgba(0, 255, 255, 0.25);
                    border-radius: 12px;
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.7), 0 0 15px rgba(0, 255, 255, 0.15);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    color: #e2e8f0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    font-size: 13px;
                    padding: 8px 16px;
                    display: flex;
                    align-items: center;
                    gap: 14px;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    max-width: 95vw;
                    user-select: none;
                }
                .vc-container:hover {
                    border-color: rgba(0, 255, 255, 0.5);
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8), 0 0 25px rgba(0, 255, 255, 0.3);
                }
                .vc-header {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-weight: 600;
                    color: #38bdf8;
                    white-space: nowrap;
                    border-right: 1px solid rgba(255, 255, 255, 0.12);
                    padding-right: 14px;
                }
                .vc-live-dot {
                    width: 8px;
                    height: 8px;
                    background-color: #22c55e;
                    border-radius: 50%;
                    box-shadow: 0 0 8px #22c55e;
                    animation: vc-pulse 2s infinite;
                }
                @keyframes vc-pulse {
                    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
                    70% { transform: scale(1.15); box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
                    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
                }
                .vc-total-count {
                    font-size: 15px;
                    font-weight: 700;
                    color: #ffffff;
                    letter-spacing: 0.5px;
                    background: linear-gradient(135deg, #38bdf8, #818cf8);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                .vc-countries-list {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    overflow-x: auto;
                    max-width: 70vw;
                    padding: 2px 4px;
                    scrollbar-width: none;
                }
                .vc-countries-list::-webkit-scrollbar {
                    display: none;
                }
                .vc-country-item {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    gap: 2px;
                    padding: 3px 6px;
                    border-radius: 6px;
                    background: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    transition: transform 0.2s ease, background 0.2s ease;
                    cursor: default;
                    min-width: 32px;
                }
                .vc-country-item:hover {
                    transform: translateY(-2px);
                    background: rgba(0, 255, 255, 0.1);
                    border-color: rgba(0, 255, 255, 0.3);
                }
                .vc-flag-img {
                    width: 22px;
                    height: 15px;
                    object-fit: cover;
                    border-radius: 2px;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
                    display: block;
                }
                .vc-country-count {
                    font-size: 11px;
                    font-weight: 600;
                    color: #cbd5e1;
                    line-height: 1;
                }
                .vc-toggle-btn {
                    background: transparent;
                    border: none;
                    color: #94a3b8;
                    cursor: pointer;
                    padding: 4px 6px;
                    border-radius: 6px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 11px;
                    transition: all 0.2s;
                }
                .vc-toggle-btn:hover {
                    color: #ffffff;
                    background: rgba(255, 255, 255, 0.1);
                }
                .vc-current-user-tag {
                    border-color: rgba(34, 197, 94, 0.4);
                    background: rgba(34, 197, 94, 0.08);
                }
                .vc-current-user-tag::after {
                    content: '';
                    display: block;
                    width: 4px;
                    height: 4px;
                    border-radius: 50%;
                    background: #22c55e;
                    position: absolute;
                    top: 2px;
                    right: 2px;
                }
                .vc-minimized .vc-countries-list {
                    display: none;
                }
                .vc-minimized {
                    padding: 6px 12px;
                    gap: 8px;
                }
                .vc-minimized .vc-header {
                    border-right: none;
                    padding-right: 0;
                }
                @media (max-width: 640px) {
                    .vc-container {
                        bottom: 8px;
                        padding: 6px 10px;
                        gap: 8px;
                        max-width: 98vw;
                    }
                    .vc-header {
                        padding-right: 8px;
                        font-size: 12px;
                    }
                    .vc-header-label {
                        display: none;
                    }
                    .vc-total-count {
                        font-size: 13px;
                    }
                    .vc-countries-list {
                        gap: 6px;
                        max-width: 60vw;
                    }
                    .vc-country-item {
                        padding: 2px 4px;
                        min-width: 26px;
                    }
                    .vc-flag-img {
                        width: 18px;
                        height: 12px;
                    }
                    .vc-country-count {
                        font-size: 10px;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        // HTML Bileşeni Oluştur
        const container = document.createElement('div');
        container.className = 'vc-container';
        container.id = 'live-visitor-counter';
        container.innerHTML = `
            <div class="vc-header">
                <span class="vc-live-dot" title="Canlı Ziyaretçi Takibi"></span>
                <span class="vc-header-label">Ziyaretçi:</span>
                <span class="vc-total-count" id="vc-total-val">...</span>
            </div>
            <div class="vc-countries-list" id="vc-flags-container">
                <span style="font-size:11px; color:#64748b;">Yükleniyor...</span>
            </div>
            <button class="vc-toggle-btn" id="vc-toggle" title="Küçült / Büyüt">▼</button>
        `;
        document.body.appendChild(container);

        let isMinimized = localStorage.getItem('vc_minimized') === 'true';
        if (isMinimized) {
            container.classList.add('vc-minimized');
            document.getElementById('vc-toggle').innerText = '▲';
        }

        document.getElementById('vc-toggle').addEventListener('click', () => {
            isMinimized = !isMinimized;
            container.classList.toggle('vc-minimized', isMinimized);
            document.getElementById('vc-toggle').innerText = isMinimized ? '▲' : '▼';
            localStorage.setItem('vc_minimized', isMinimized);
        });

        // Veri Çekme ve Güncelleme Motoru
        let isTrackingDoneInSession = sessionStorage.getItem('vc_tracked') === '1';

        async function detectClientCountry() {
            try {
                const res = await fetch('https://ipapi.co/json/');
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.country_code) {
                        return data.country_code.toUpperCase().substring(0, 2);
                    }
                }
            } catch (e) {}
            return 'TR';
        }

        async function fetchStats(increment = false) {
            let detectedCountry = '';
            if (increment && !isTrackingDoneInSession) {
                detectedCountry = await detectClientCountry();
            }

            // 1. Vercel API'yi dene (Varsa Edge IP tespiti ile çok hızlı çalışır)
            try {
                const queryParam = detectedCountry ? `&country=${detectedCountry}` : '';
                const apiUrl = `/api/counter?track=${increment && !isTrackingDoneInSession ? 'true' : 'false'}${queryParam}&t=${Date.now()}`;
                const res = await fetch(apiUrl);
                if (res.ok) {
                    const data = await res.json();
                    if (increment) {
                        sessionStorage.setItem('vc_tracked', '1');
                        isTrackingDoneInSession = true;
                    }
                    renderStats(data);
                    return;
                }
            } catch (e) {}

            // 2. Doğrudan Supabase REST API Fallback (Localhost veya Vercel harici ortamlarda)
            try {
                const headers = {
                    'apikey': SUPABASE_ANON_KEY,
                    'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
                    'Content-Type': 'application/json'
                };

                if (increment && !isTrackingDoneInSession) {
                    if (!detectedCountry) detectedCountry = await detectClientCountry();
                    try {
                        await fetch(`${SUPABASE_URL}/rest/v1/rpc/increment_visitor`, {
                            method: 'POST',
                            headers: headers,
                            body: JSON.stringify({ p_country_code: detectedCountry })
                        });
                        sessionStorage.setItem('vc_tracked', '1');
                        isTrackingDoneInSession = true;
                    } catch (rpcErr) {
                        console.error("Direct RPC Error:", rpcErr);
                    }
                }

                const tableRes = await fetch(`${SUPABASE_URL}/rest/v1/visitor_counts?select=*&order=count.desc&t=${Date.now()}`, {
                    headers: headers
                });

                if (tableRes.ok) {
                    const rows = await tableRes.json();
                    let countries = {};
                    let total = 0;
                    if (Array.isArray(rows)) {
                        for (const row of rows) {
                            const c = (row.country_code || '').toUpperCase();
                            const cnt = Number(row.count) || 0;
                            if (c && cnt > 0) {
                                countries[c] = cnt;
                                total += cnt;
                            }
                        }
                    }
                    renderStats({
                        total: total || 1,
                        countries: countries,
                        visitorCountry: detectedCountry || 'TR'
                    });
                }
            } catch (err) {
                console.warn("Visitor counter load error:", err);
            }
        }

        function renderStats(data) {
            if (!data) return;
            const totalEl = document.getElementById('vc-total-val');
            const flagsEl = document.getElementById('vc-flags-container');
            if (!totalEl || !flagsEl) return;

            // Toplam Sayı
            const total = data.total || 0;
            totalEl.innerText = Number(total).toLocaleString('tr-TR');

            // Ülke Dağılımı
            const countries = data.countries || {};
            const sortedCountries = Object.entries(countries)
                .filter(([code, count]) => code && code.length === 2 && count > 0)
                .sort((a, b) => b[1] - a[1]); // En çok ziyaret edilen ülkeler en başta

            if (sortedCountries.length === 0) {
                flagsEl.innerHTML = '<span style="font-size:11px; color:#64748b;">Henüz veri yok</span>';
                return;
            }

            const visitorCountry = (data.visitorCountry || '').toUpperCase();

            flagsEl.innerHTML = sortedCountries.map(([code, count]) => {
                const countryCode = code.toUpperCase();
                const countryName = getCountryName(countryCode);
                const isCurrentUser = countryCode === visitorCountry;
                const flagUrl = `https://flagcdn.com/w40/${countryCode.toLowerCase()}.png`;

                return `
                    <div class="vc-country-item ${isCurrentUser ? 'vc-current-user-tag' : ''}" 
                         title="${countryName}: ${Number(count).toLocaleString('tr-TR')} ziyaretçi ${isCurrentUser ? '(Sizin Konumunuz)' : ''}">
                        <img src="${flagUrl}" 
                             alt="${countryName}" 
                             class="vc-flag-img" 
                             loading="lazy" 
                             onerror="this.style.display='none'">
                        <span class="vc-country-count">${Number(count).toLocaleString('tr-TR')}</span>
                    </div>
                `;
            }).join('');
        }

        // İlk Ziyaret: Bu oturumda sayılmadıysa arttır, sayıldıysa sadece oku
        const shouldIncrement = !isTrackingDoneInSession;
        fetchStats(shouldIncrement);

        // Her 30 saniyede bir yeni ziyaretçileri canlı olarak tazele
        setInterval(() => {
            fetchStats(false);
        }, 30000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCounter);
    } else {
        initCounter();
    }
})();
