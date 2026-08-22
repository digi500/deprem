export default async function handler(req, res) {
    // CORS Başlıkları
    res.setHeader('Access-Control-Allow-Credentials', true);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
    res.setHeader(
        'Access-Control-Allow-Headers',
        'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
    );
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0');

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    const SUPABASE_URL = "https://tiykapksaboucamusmbk.supabase.co";
    const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpeWthcGtzYWJvdWNhbXVzbWJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcxNjUyMjEsImV4cCI6MjEwMjc0MTIyMX0.D2YkQaF5Gfn49bsRpuoi3W1upoFfhGxdFQ-pBRW6IAM";

    // Ziyaretçinin ülkesini tespit et (Vercel Edge başlığı veya parametre)
    let country = (req.headers['x-vercel-ip-country'] || req.query.country || 'TR').toUpperCase().trim();
    if (!country || country.length !== 2 || country === 'XX') {
        country = 'TR';
    }

    const shouldIncrement = req.query.track !== 'false' && req.query.track !== '0';

    try {
        const headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
            'Content-Type': 'application/json'
        };

        // 1. Yeni tekil ziyaretçi ise veritabanında sayıyı 1 artır (RPC)
        if (shouldIncrement) {
            try {
                await fetch(`${SUPABASE_URL}/rest/v1/rpc/increment_visitor`, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({ p_country_code: country })
                });
            } catch (rpcErr) {
                console.error("RPC increment error:", rpcErr);
            }
        }

        // 2. Güncel ülke sayılarını visitor_counts tablosundan çek
        const tableRes = await fetch(`${SUPABASE_URL}/rest/v1/visitor_counts?select=*&order=count.desc`, {
            headers: headers
        });

        let countries = {};
        let total = 0;

        if (tableRes.ok) {
            const rows = await tableRes.json();
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
        }

        return res.status(200).json({
            success: true,
            total: total || 1,
            countries: countries,
            visitorCountry: country,
            last_updated: new Date().toISOString()
        });
    } catch (error) {
        console.error("Counter API Error:", error);
        return res.status(500).json({
            error: error.message,
            total: 1,
            countries: { [country]: 1 },
            visitorCountry: country
        });
    }
}
