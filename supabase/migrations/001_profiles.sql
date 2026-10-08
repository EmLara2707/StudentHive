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