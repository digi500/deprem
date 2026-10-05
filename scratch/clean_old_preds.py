import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("HATA: SUPABASE_URL veya SUPABASE_SERVICE_KEY ortam değişkenleri tanımlanmamış!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch all pending predictions
res = supabase.table('predictions').select('*').is_('matched_earthquake_id', 'null').execute()
pending = res.data

deleted_count = 0
for p in pending:
    if p.get('target_order') != 1:
        supabase.table('predictions').delete().eq('id', p['id']).execute()
        deleted_count += 1

print(f"Deleted {deleted_count} obsolete predictions.")
