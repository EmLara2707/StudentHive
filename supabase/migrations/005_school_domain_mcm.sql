-- 005: tighten the signup trigger from "any .edu.ph address" to the real school domain,
-- mcm.edu.ph (subdomains such as student.mcm.edu.ph are allowed, the same rule as
-- AuthController.is_school_email). Safe to run on a project that already has 001, and
-- on a fresh one (001 creates the function, this replaces it; the trigger keeps pointing
-- at it). Existing profiles are not touched.
-- If the school domain ever changes, change it here AND in SCHOOL_EMAIL_DOMAINS in
-- controllers/auth_controller.py.
create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
    if lower(new.email) !~ '@([a-z0-9-]+\.)*mcm\.edu\.ph$' then
        raise exception 'Please use your school email address (it ends in mcm.edu.ph).';
    end if;
    insert into public.profiles (id, email, name)
    values (new.id, lower(new.email),
            coalesce(nullif(trim(new.raw_user_meta_data ->> 'name'), ''), 'Student'));
    return new;
end $$;
