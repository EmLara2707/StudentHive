-- StudentHive migration 007: rental pickup / drop-off confirmations
-- The renter confirms pickup (from the start day on) and later drop-off. Once the item is
-- picked up the rental can no longer be cancelled; it can be completed or cancelled only
-- after drop-off. The app enforces the flow (Transaction model); the database guards the
-- invariants below. Safe to run on existing data: both columns start empty.

alter table public.transactions
    add column picked_up_at   timestamptz,
    add column dropped_off_at timestamptz;

-- drop-off needs a pickup first
alter table public.transactions
    add constraint transactions_dropoff_after_pickup
    check (dropped_off_at is null or picked_up_at is not null);

-- an item that is out (picked up, not yet dropped off) cannot be cancelled
alter table public.transactions
    add constraint transactions_no_cancel_while_out
    check (not (status = 'Cancelled' and picked_up_at is not null and dropped_off_at is null));
