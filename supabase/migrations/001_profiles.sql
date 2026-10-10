-- StudentHive migration 001: profiles, signup trigger
-- Split from studenthive_schema_draft.sql (the draft is the source of truth for names).

-- Derived from reading the current models/repositories. Not yet run against Supabase.
-- Money is numeric; ids are database-assigned; every "delete the user" rule from
-- AuthController.delete_account is a foreign-key cascade instead of application code.

-- ---------------------------------------------------------------- profiles
-- One row per auth user. Auth (email, password, confirmation) lives in auth.users;
-- the password_hash column and utils/security.py go away if you use Supabase Auth.
create table public.profiles (
    id          uuid primary key references auth.users (id) on delete cascade,
    email       text not null unique check (email = lower(email)),
    name        text not null check (length(trim(name)) > 0),
    onboarded   boolean not null default false,
    major       text not null default '',
    bio         text not null default '' check (char_length(bio) <= 500),
    skills      text[] not null default '{}',
    portfolio   text not null default '',
    linkedin    text not null default '',
    github      text not null default '',
    socials     text[] not null default '{}',
    id_status   text not null default 'not_submitted'
                check (id_status in ('not_submitted', 'pending', 'verified', 'rejected')),
    photo_path  text,            -- Storage path, replaces Profile.photo (bytes)
    photo_mime  text check (photo_mime in ('image/jpeg', 'image/png', 'image/webp')),
    created_at  timestamptz not null default now()
);

-- Create the profile when someone signs up, and refuse non-school addresses at the
-- database too (the app checks this as well; the DB is the backstop).
-- Known loosenesses (fine for a school project): a signed-in user can update any column
-- of their own profile (including onboarded / id_status), and either participant can
-- update any column of a transaction. The Python model's rules are what really gate this.
create function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
    if lower(new.email) !~ '@([a-z0-9-]+\.)*edu\.ph$' then
        raise exception 'Please use your school email address (it ends in .edu.ph).';
    end if;
    insert into public.profiles (id, email, name)
    values (new.id, lower(new.email),
            coalesce(nullif(trim(new.raw_user_meta_data ->> 'name'), ''), 'Student'));
    return new;
end $$;

-- AFTER insert: profiles.id references auth.users(id), so the auth row must already exist.
-- An exception here still rolls the signup back. The app should check the domain first,
-- because Supabase only returns a generic "Database error saving new user" to the client.
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- RLS (profiles). Safety net only: the browser never talks to Supabase.
alter table public.profiles enable row level security;
create policy "profiles readable by members" on public.profiles
    for select to authenticated using (true);
create policy "own profile editable" on public.profiles
    for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- ---------------------------------------------------------------- A4 additions
-- Safe to run more than once. If your project already ran the part above, copy only
-- this block into the SQL editor.

-- "Is this email already registered?" for the sign-up form. The sign-up screen runs
-- before anyone is signed in, and profiles are readable only by signed-in members, so a
-- plain select would always say "no". This returns ONLY true/false, never row data.
-- Accepted trade-off: anyone can test whether an email has an account (the sign-up form
-- already reveals that). The signup trigger still guards the real insert.
create or replace function public.email_registered(p_email text) returns boolean
language sql stable security definer set search_path = '' as $$
    select exists (select 1 from public.profiles where email = lower(trim(p_email)));
$$;
revoke all on function public.email_registered(text) from public;
grant execute on function public.email_registered(text) to anon, authenticated;

-- Avatars bucket. Public read (same choice as listing-images in 004): anyone with the
-- link can view an image; only the signed-in owner can write inside their own folder
-- <user id>/<file>.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('avatars', 'avatars', true, 10485760,
        array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do nothing;

drop policy if exists "avatars: members can look" on storage.objects;
drop policy if exists "avatars: owner uploads" on storage.objects;
drop policy if exists "avatars: owner replaces" on storage.objects;
drop policy if exists "avatars: owner deletes" on storage.objects;
create policy "avatars: members can look" on storage.objects
    for select to authenticated using (bucket_id = 'avatars');
create policy "avatars: owner uploads" on storage.objects
    for insert to authenticated
    with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "avatars: owner replaces" on storage.objects
    for update to authenticated
    using (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "avatars: owner deletes" on storage.objects
    for delete to authenticated
    using (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);
