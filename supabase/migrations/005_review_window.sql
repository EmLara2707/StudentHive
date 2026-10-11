-- 005: reviews can only be left within 14 days of a transaction being completed.
-- Safe to run on a project that already has 001-004 (and on a fresh one, in order).
-- The same 14-day rule lives in models/transaction.py (REVIEW_WINDOW_DAYS); change both.

alter table public.transactions add column if not exists completed_at timestamptz;

-- Rows that were completed before this migration: the last update was the completion.
update public.transactions
   set completed_at = updated_at
 where status = 'Completed' and completed_at is null;

-- The database stamps the completion time itself (server clock, not the app's), the first
-- time a row moves to Completed. Completed is final, so it is never stamped again.
create or replace function public.stamp_completed_at() returns trigger
language plpgsql as $$
begin
    if new.status = 'Completed' and old.status is distinct from 'Completed' then
        new.completed_at := now();
    end if;
    return new;
end $$;

drop trigger if exists transactions_stamp_completed_at on public.transactions;
create trigger transactions_stamp_completed_at
    before update on public.transactions
    for each row execute function public.stamp_completed_at();

-- submit_review: same checks as 003, plus the 14-day window. A NULL completed_at (sample
-- rows inserted already Completed) has no deadline.
create or replace function public.submit_review(p_transaction_id bigint, p_rating int, p_text text)
returns void language plpgsql security definer set search_path = '' as $$
declare t public.transactions;
begin
    select * into t from public.transactions where id = p_transaction_id;
    if auth.uid() is null or not found or t.status <> 'Completed'
       or auth.uid() not in (t.provider_id, t.requester_id) then
        raise exception 'That isn''t available right now.';
    end if;
    if t.completed_at is not null and now() > t.completed_at + interval '14 days' then
        raise exception 'The 14-day review window for this has closed.';
    end if;
    insert into public.reviews (transaction_id, reviewer_id, subject_id, rating, text)
    values (p_transaction_id, auth.uid(),
            case when auth.uid() = t.provider_id then t.requester_id else t.provider_id end,
            p_rating, left(coalesce(p_text, ''), 500));
end $$;
-- create or replace keeps the existing grants, but state them again so this file stands alone.
revoke execute on function public.submit_review(bigint, int, text) from public, anon;
grant  execute on function public.submit_review(bigint, int, text) to authenticated;
