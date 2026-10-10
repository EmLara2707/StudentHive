-- DEV ONLY. Never run in production. Run once in YOUR OWN Supabase project's SQL editor
-- after migrations 001-005, so foreign keys have profile rows to point at.
--
-- These rows have no password, so nobody can sign in as them; they only exist so that
-- listings / transactions / reviews can reference real profiles.id values. The signup
-- trigger creates the matching public.profiles rows. Emails follow seed_data.email_for().
--
-- Fixed ids so scripts/seed_market.py can reference them.
-- Person A's scripts/seed_users.py creates the same emails through the admin API; if you
-- run it in this project, run the cleanup block at the bottom first (email is unique).
insert into auth.users (id, email, email_confirmed_at, raw_user_meta_data) values
    ('00000000-0000-4000-8000-000000000001', 'demo@mcm.edu.ph',  now(), '{"name": "Demo Student"}'),
    ('00000000-0000-4000-8000-000000000002', 'ana.r@mcm.edu.ph', now(), '{"name": "Ana R."}'),
    ('00000000-0000-4000-8000-000000000003', 'miguel.s@mcm.edu.ph', now(), '{"name": "Miguel S."}')
on conflict (id) do nothing;

-- Cleanup (deletes the profiles and everything that cascades from them):
-- delete from auth.users where id in (
--   '00000000-0000-4000-8000-000000000001',
--   '00000000-0000-4000-8000-000000000002',
--   '00000000-0000-4000-8000-000000000003');