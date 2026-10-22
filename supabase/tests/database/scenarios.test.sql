-- pgTAP testy D01–D05 (spustenie: supabase test db)
begin;
select plan(6);

insert into public.scenarios (id, client_id, name, inputs, currency, share_slug)
values ('00000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-0000000000aa',
        'Test', '{}', 'EUR', 'AbCdEf1234');

-- D01: anon nevidí žiadne scenáre
set local role anon;
select throws_ok(
  $$select * from public.scenarios$$,
  '42501', null, 'D01 anon nemá prístup k scenarios'
);
reset role;

-- D03: názov dlhší ako 100 znakov
select throws_ok(
  $$insert into public.scenarios (client_id, name, inputs, currency)
    values (gen_random_uuid(), repeat('x', 101), '{}', 'EUR')$$,
  '23514', null, 'D03 check na dĺžku názvu'
);

-- D04: duplicitný share_slug
select throws_ok(
  $$insert into public.scenarios (client_id, name, inputs, currency, share_slug)
    values (gen_random_uuid(), 'Iný', '{}', 'EUR', 'AbCdEf1234')$$,
  '23505', null, 'D04 share_slug je unikátny'
);

-- neplatná mena
select throws_ok(
  $$insert into public.scenarios (client_id, name, inputs, currency)
    values (gen_random_uuid(), 'X', '{}', 'JPY')$$,
  '23514', null, 'nepodporovaná mena'
);

-- D05: update mení updated_at
update public.scenarios set updated_at = now() - interval '1 day'
where id = '00000000-0000-4000-8000-000000000001';
update public.scenarios set name = 'Premenovaný'
where id = '00000000-0000-4000-8000-000000000001';
select ok(
  (select updated_at > now() - interval '1 minute' from public.scenarios
   where id = '00000000-0000-4000-8000-000000000001'),
  'D05 trigger nastaví updated_at'
);

select ok(
  (select relrowsecurity from pg_class where oid = 'public.scenarios'::regclass),
  'RLS je zapnuté'
);

select * from finish();
rollback;
