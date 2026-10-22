-- pgTAP testy D02, D06 (spustenie: supabase test db)
begin;
select plan(3);

-- D02: anon nemôže zapisovať
set local role anon;
select throws_ok(
  $$insert into public.calculation_log (source, inputs, monthly_total, total_interest, payments_count, duration_ms)
    values ('live', '{}', 1, 1, 1, 1)$$,
  '42501', null, 'D02 anon nemôže zapisovať do calculation_log'
);
reset role;

-- D06: retenčný príkaz zmaže len staré záznamy
insert into public.calculation_log (created_at, source, inputs, monthly_total, total_interest, payments_count, duration_ms)
values (now() - interval '91 days', 'live', '{"t":"old"}', 1, 1, 1, 1),
       (now() - interval '89 days', 'live', '{"t":"new"}', 1, 1, 1, 1);

select is(
  (select command from cron.job where jobname = 'calculation-log-retention'),
  $$delete from public.calculation_log where created_at < now() - interval '90 days'$$,
  'retenčná úloha je naplánovaná'
);

delete from public.calculation_log where created_at < now() - interval '90 days';
select is(
  (select count(*)::int from public.calculation_log where inputs->>'t' in ('old', 'new')),
  1,
  'D06 ostane len záznam mladší ako 90 dní'
);

select * from finish();
rollback;
