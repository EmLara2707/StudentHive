-- StudentHive migration 003: transactions, reviews, submit_review
-- Split from studenthive_schema_draft.sql (the draft is the source of truth for names).

-- ---------------------------------------------------------------- transactions
create table public.transactions (
    id               bigint generated always as identity primary key,
    kind             text not null check (kind in ('Gig', 'Rental')),
    listing_id       bigint references public.listings (id) on delete set null,
    item             text not null,                 -- title copied at booking time
    image_path       text,
    provider_id      uuid not null references public.profiles (id) on delete cascade,
    requester_id     uuid not null references public.profiles (id) on delete cascade,
    start_date       date not null,
    end_date         date not null,
    start_time       time,
    end_time         time,
    price            numeric(10, 2) not null,
    unit             text not null check (unit in ('hr', 'day', 'once')),
    quantity         numeric(8, 2) not null,
    total            numeric(12, 2) not null,
    status           text not null default 'Pending'
                     check (status in ('Pending', 'Active', 'Completed', 'Cancelled')),
    cancelled_by     uuid references public.profiles (id) on delete cascade,
    meeting_mode     text,
    location         text not null default '',
    project_details  text not null default '',
    deadline         date,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now(),
    check (provider_id <> requester_id),
    check (end_date >= start_date),
    check ((status = 'Cancelled') = (cancelled_by is not null)),
    check (cancelled_by is null or cancelled_by in (provider_id, requester_id))
);
create index transactions_provider_idx  on public.transactions (provider_id);
create index transactions_requester_idx on public.transactions (requester_id);

-- "An identical request is refused while the first is Pending or Active", enforced by
-- the database so two simultaneous clicks cannot both succeed.
create unique index transactions_no_duplicate_request on public.transactions (
    requester_id, listing_id, start_date, end_date,
    coalesce(start_time, '00:00'), coalesce(end_time, '00:00'),
    coalesce(deadline, '1900-01-01'), md5(project_details)
) where status in ('Pending', 'Active') and listing_id is not null;

-- ---------------------------------------------------------------- reviews
-- Replaces Transaction.reviewed_by: "has this person reviewed?" is a row lookup, and the
-- unique constraint makes a double submit impossible.
-- transaction_id / reviewer_id are nullable only for the seeded sample reviews.
create table public.reviews (
    id              bigint generated always as identity primary key,
    transaction_id  bigint references public.transactions (id) on delete cascade,
    reviewer_id     uuid references public.profiles (id) on delete cascade,
    reviewer_name   text,                       -- only for sample reviews with no account
    subject_id      uuid not null references public.profiles (id) on delete cascade,
    rating          numeric(2, 1) not null check (rating between 1 and 5),
    text            text not null default '' check (char_length(text) <= 500),
    created_at      timestamptz not null default now(),
    unique (transaction_id, reviewer_id),
    check (reviewer_id is null or reviewer_id <> subject_id)
);
create index reviews_subject_idx on public.reviews (subject_id);

-- One call = one database transaction: checks, inserts. Real reviews are whole stars.
create function public.submit_review(p_transaction_id bigint, p_rating int, p_text text)
returns void language plpgsql security definer set search_path = '' as $$
declare t public.transactions;
begin
    select * into t from public.transactions where id = p_transaction_id;
    if auth.uid() is null or not found or t.status <> 'Completed'
       or auth.uid() not in (t.provider_id, t.requester_id) then
        raise exception 'That isn''t available right now.';
    end if;
    insert into public.reviews (transaction_id, reviewer_id, subject_id, rating, text)
    values (p_transaction_id, auth.uid(),
            case when auth.uid() = t.provider_id then t.requester_id else t.provider_id end,
            p_rating, left(coalesce(p_text, ''), 500));
end $$;

-- Deviation from the draft (found by testing): with no signed-in user auth.uid() is NULL,
-- "NULL not in (...)" is NULL, and the guard above did not fire, so an anonymous caller
-- could insert a review with reviewer_id = NULL. Fixed by the explicit NULL check above
-- and by not letting anon call the function at all.
revoke execute on function public.submit_review(bigint, int, text) from public, anon;
grant  execute on function public.submit_review(bigint, int, text) to authenticated;

-- RLS (transactions, reviews).
alter table public.transactions enable row level security;
alter table public.reviews      enable row level security;
create policy "participants read transactions" on public.transactions
    for select to authenticated using (auth.uid() in (provider_id, requester_id));
create policy "requester creates transactions" on public.transactions
    for insert to authenticated with check (requester_id = auth.uid() and status = 'Pending');
create policy "participants update transactions" on public.transactions
    for update to authenticated
    using (auth.uid() in (provider_id, requester_id))
    with check (auth.uid() in (provider_id, requester_id));
create policy "reviews readable by members" on public.reviews
    for select to authenticated using (true);
-- no insert policy on purpose: reviews are created only through submit_review().