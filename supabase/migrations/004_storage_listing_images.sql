-- StudentHive migration 004: Storage bucket and policies for listing images.
-- Not in the handoff PDF's list of three migrations; added with the owner's approval
-- (deviation). Public-read bucket: anyone with a link can view an image, only the
-- signed-in owner can write inside their own folder (<user id>/<file>).
-- Applied by hand in the dashboard first; not yet tested through the app.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('listing-images', 'listing-images', true, 5242880,
        array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do nothing;

create policy "listing images: members can look" on storage.objects
    for select to authenticated using (bucket_id = 'listing-images');
create policy "listing images: owner uploads" on storage.objects
    for insert to authenticated
    with check (bucket_id = 'listing-images'
                and (storage.foldername(name))[1] = auth.uid()::text);
create policy "listing images: owner replaces" on storage.objects
    for update to authenticated
    using (bucket_id = 'listing-images' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "listing images: owner deletes" on storage.objects
    for delete to authenticated
    using (bucket_id = 'listing-images' and (storage.foldername(name))[1] = auth.uid()::text);
