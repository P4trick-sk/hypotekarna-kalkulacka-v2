-- Rola pre FastAPI s minimálnymi právami (namiesto service_role kľúča).
-- Heslo sa NEnastavuje v migrácii: `alter role hk_api with login password '<SCRAM hash>'`
-- sa spúšťa jednorazovo mimo repozitára (pozri README – Pripojenie k Supabase).

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'hk_api') then
    create role hk_api nologin noinherit;
  end if;
end
$$;

grant usage on schema public to hk_api;
grant select, insert, update, delete on public.scenarios to hk_api;
grant insert on public.calculation_log to hk_api;
grant usage on sequence public.calculation_log_id_seq to hk_api;

-- RLS zostáva zapnuté; prístup má len rola API. Vlastníctvo (client_id) kontroluje API.
create policy scenarios_api_all on public.scenarios
  for all to hk_api using (true) with check (true);

create policy calculation_log_api_insert on public.calculation_log
  for insert to hk_api with check (true);
