-- StudentHive migration 002: listings, listing_images
-- Split from studenthive_schema_draft.sql (the draft is the source of truth for names).

-- ---------------------------------------------------------------- listings
create table public.listings (
    id           bigint generated always as identity primary key,
    owner_id     uuid not null references public.profiles (id) on delete cascade,
    title        text not null check (length(trim(title)) > 0),
    price        numeric(10, 2) not null check (price > 0),
    category     text not null check (category in ('Gig', 'Rental')),
    deliverable  text not null default '',
    unit         text not null check (unit in ('hr', 'day', 'once')),
    description  text not null default '',
    status       text not null default 'open' check (status in ('open', 'closed')),
    created_at   timestamptz not null default now(),
    check ((category = 'Gig' and deliverable in ('Service Deliverables', 'Project Deliverables'))
        or (category = 'Rental' and deliverable = ''))
);
create index listings_owner_idx on public.listings (owner_id);
create index listings_open_idx  on public.listings (created_at desc) where status = 'open';

-- Up to 10 images per listing (MAX_IMAGES), stored in Storage, not as base64 in the row.
create table public.listing_images (
    listing_id   bigint not null references public.listings (id) on delete cascade,
    position     smallint not null check (position between 0 and 9),
    storage_path text not null,
    primary key (listing_id, position)
);

-- RLS (listings, listing_images).
alter table public.listings       enable row level security;
alter table public.listing_images enable row level security;
create policy "listings readable by members" on public.listings
    for select to authenticated using (true);
create policy "own listings writable" on public.listings
    for all to authenticated using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "listing images readable" on public.listing_images
    for select to authenticated using (true);
create policy "own listing images writable" on public.listing_images
    for all to authenticated
    using (exists (select 1 from public.listings l where l.id = listing_id and l.owner_id = auth.uid()))
    with check (exists (select 1 from public.listings l where l.id = listing_id and l.owner_id = auth.uid()));