-- The page saves read markers with an upsert, which also writes channel_id (same value).
grant update (channel_id) on public.channel_reads to authenticated;
