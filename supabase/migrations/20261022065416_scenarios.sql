-- Uložené scenáre (F11) a zdieľacie odkazy (F12).
-- Prístup má len API cez service_role; RLS je zapnuté bez politík pre anon/authenticated.

create table public.scenarios (
  id          uuid primary key default gen_random_uuid(),
  client_id   uuid not null,
  name        text not null check (char_length(name) between 1 and 100),
  inputs      jsonb not null,
  currency    char(3) not null check (currency in ('EUR', 'USD', 'GBP', 'CZK', 'CHF', 'PLN')),
  share_slug  text unique check (share_slug ~ '^[A-Za-z0-9]{10}$'),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

comment on table public.scenarios is 'Hypotekárna kalkulačka: uložené scenáre, viazané na anonymný client_id prehliadača.';

create index scenarios_client_updated_idx on public.scenarios (client_id, updated_at desc);

alter table public.scenarios enable row level security;
revoke all on public.scenarios from anon, authenticated;

create or replace function public.scenarios_set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger scenarios_set_updated_at
  before update on public.scenarios
  for each row execute function public.scenarios_set_updated_at();
