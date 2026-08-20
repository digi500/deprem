import os
from supabase import create_client, Client

SUPABASE_URL = "https://tiykapksaboucamusmbk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpeWthcGtzYWJvdWNhbXVzbWJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzE2NTIyMSwiZXhwIjoyMTAyNzQxMjIxfQ.D_dVAm0ueAw4-bODs1zt4UMR3LZZxvrBVYgfqG6V4tI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Mevcut depremleri çek
eq_res = supabase.table('earthquakes').select('id').execute()
N = len(eq_res.data)
remainder = N % 3

print(f"Toplam deprem: {N}, Kalan (remainder): {remainder}")

# Tüm tahminleri (hem eşleşen hem eşleşmeyen) sil
supabase.table('predictions').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
print("Geçmiş tüm tahminler ve doğruluk verileri silindi.")
