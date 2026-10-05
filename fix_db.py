import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("HATA: SUPABASE_URL veya SUPABASE_SERVICE_KEY ortam değişkenleri tanımlanmamış!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Mevcut depremleri çek
eq_res = supabase.table('earthquakes').select('id').execute()
N = len(eq_res.data)
remainder = N % 3

print(f"Toplam deprem: {N}, Kalan (remainder): {remainder}")

# Tüm tahminleri (hem eşleşen hem eşleşmeyen) sil
supabase.table('predictions').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
print("Geçmiş tüm tahminler ve doğruluk verileri silindi.")
