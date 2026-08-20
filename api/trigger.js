export default async function handler(req, res) {
    // Sadece POST isteklerini kabul et
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Sadece POST metoduna izin verilir' });
    }
    
    // Vercel panelinden okunacak gizli Github Token'ı
    const token = process.env.GITHUB_TOKEN;
    if (!token) {
        return res.status(500).json({ error: 'Vercel ortam değişkenlerinde GITHUB_TOKEN eksik!' });
    }
    
    try {
        // Github Actions API'sine tetikleme (workflow_dispatch) isteği gönder
        // Repository adı: digi500/deprem (Değiştirmeniz gerekirse burayı düzeltin)
        const response = await fetch('https://api.github.com/repos/digi500/deprem/actions/workflows/updater.yml/dispatches', {
            method: 'POST',
            headers: {
                'Authorization': `token ${token}`,
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ref: 'main' })
        });
        
        if (!response.ok) {
            const err = await response.text();
            throw new Error(`GitHub API Hatası: ${response.status} ${err}`);
        }
        
        return res.status(200).json({ success: true, message: 'Motor başarıyla tetiklendi!' });
    } catch (error) {
        console.error("Tetikleme Hatası:", error);
        return res.status(500).json({ error: error.message });
    }
}
