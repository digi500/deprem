import os
from supabase import create_client, Client

SUPABASE_URL = "https://tiykapksaboucamusmbk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpeWthcGtzYWJvdWNhbXVzbWJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzE2NTIyMSwiZXhwIjoyMTAyNzQxMjIxfQ.D_dVAm0ueAw4-bODs1zt4UMR3LZZxvrBVYgfqG6V4tI"

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
