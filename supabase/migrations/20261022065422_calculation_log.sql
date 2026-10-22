-- Log výpočtov (F13). Bez client_id a IP; retencia 90 dní cez pg_cron.

create table public.calculation_log (
  id              bigint generated always as identity primary key,
  created_at      timestamptz not null default now(),
  source          text not null check (source in ('live', 'scenario', 'share')),
  inputs          jsonb not null,
  monthly_total   numeric(14, 2) not null,
  total_interest  numeric(14, 2) not null,
  payments_count  int not null check (payments_count > 0),
  duration_ms     int not null check (duration_ms >= 0)
);

comment on table public.calculation_log is 'Hypotekárna kalkulačka: anonymný log úspešných výpočtov, mazaný po 90 dňoch.';

create index calculation_log_created_at_idx on public.calculation_log (created_at);

alter table public.calculation_log enable row level security;
revoke all on public.calculation_log from anon, authenticated;

create extension if not exists pg_cron;

select cron.schedule(
  'calculation-log-retention',
  '15 3 * * *',
  $$delete from public.calculation_log where created_at < now() - interval '90 days'$$
);
