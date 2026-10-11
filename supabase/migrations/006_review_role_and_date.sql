-- 006: remember which role the reviewed person had, so the profile Reviews tab can filter by
-- "As provider" / "As customer". Stored on the review itself because other students cannot
-- read the transaction row (RLS), so it could not be looked up when they view a profile.
-- created_at already exists on reviews (used for "Newest / Oldest first").
-- Safe to run more than once.

alter table public.reviews add column if not exists subject_is_provider boolean;

-- Existing reviews: the reviewed person was the provider when they provided that transaction.
update public.reviews r
   set subject_is_provider = (t.provider_id = r.subject_id)
  from public.transactions t
 where r.transaction_id = t.id and r.subject_is_provider is null;

-- submit_review: same as 005 (checks + 14-day window), now also records the role.
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
    insert into public.reviews (transaction_id, reviewer_id, subject_id, subject_is_provider,
                                rating, text)
    values (p_transaction_id, auth.uid(),
            case when auth.uid() = t.provider_id then t.requester_id else t.provider_id end,
            auth.uid() = t.requester_id,       -- the reviewer was the customer, so the subject is the provider
            p_rating, left(coalesce(p_text, ''), 500));
end $$;
revoke execute on function public.submit_review(bigint, int, text) from public, anon;
grant  execute on function public.submit_review(bigint, int, text) to authenticated;
