begin;

create schema if not exists extensions;
create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to app_rw;
grant execute on all functions in schema extensions to app_rw;
set search_path = public, extensions;

select plan(21);

select app.create_tenant_with_owner(
    'gov-a', 'gov-a.growup.com', 'Gov A', null, null,
    '11111111-1111-4111-8111-111111111111', 'OwnerA@Example.com'
) as tenant_a \gset

select app.create_tenant_with_owner(
    'gov-b', 'gov-b.growup.com', 'Gov B', null, null,
    '22222222-2222-4222-8222-222222222222', 'ownerb@example.com'
) as tenant_b \gset

select is(
    (
        select role
        from app.memberships
        where tenant_id = :'tenant_a'
          and user_id = '11111111-1111-4111-8111-111111111111'
    ),
    'owner',
    'create_tenant_with_owner crea membership owner'
);

set local role app_rw;
select set_config('app.tenant_id', :'tenant_a', true);

select app.append_decision_log(
    :'tenant_a', 'staff', 'user-1', 'content.publish', 'page', 'page-1',
    'content.publish', 'v1', 'ALLOW', 'VALID', 'hash-1',
    '{"slug":"home"}'::jsonb, 5, 'trace-1'
) as log_1 \gset

select ok(:'log_1' <> '', 'append_decision_log devuelve id');
select ok(app.verify_decision_chain(:'tenant_a'), 'cadena A verifica');

select app.append_decision_log(
    :'tenant_a', 'staff', 'user-1', 'content.publish', 'page', 'page-2',
    'content.publish', 'v1', 'ALLOW', 'VALID', 'hash-2',
    '{"slug":"about"}'::jsonb, 4, 'trace-2'
) as log_2 \gset

select ok(:'log_2' <> '', 'segundo append devuelve id');
select is(
    (select count(*)::int from app.decision_logs),
    2,
    'tenant A ve sus dos decisiones'
);

select set_config('app.tenant_id', :'tenant_b', true);

select is(
    (select count(*)::int from app.decision_logs),
    0,
    'tenant B no ve decisiones de A'
);

select throws_ok(
    format(
        'insert into app.approval_tasks '
        '(tenant_id, action, requested_by, assigned_role, reason, expires_at) '
        'values (%L, %L, %L, %L, %L, now())',
        :'tenant_a',
        'refund',
        'user-1',
        'owner',
        'test'
    ),
    '42501',
    null,
    'RLS bloquea approval cross-tenant'
);

select lives_ok(
    format(
        'insert into app.approval_tasks '
        '(tenant_id, action, requested_by, assigned_role, reason, expires_at) '
        'values (%L, %L, %L, %L, %L, now())',
        :'tenant_b',
        'refund',
        'user-2',
        'owner',
        'test'
    ),
    'tenant B crea su approval'
);

select is(
    (select count(*)::int from app.approval_tasks),
    1,
    'tenant B ve su approval'
);

-- El contexto de tenant no se puede saltar al escribir la auditoría.
select throws_ok(
    format(
        'select app.append_decision_log(%L, %L, %L, %L, null, null, %L, %L, %L, %L, %L, %L::jsonb, 1, %L)',
        :'tenant_a', 'staff', 'user-1', 'content.publish',
        'content.publish', 'v1', 'ALLOW', 'VALID', 'hash-x', '{}', 'trace-x'
    ),
    '42501',
    null,
    'append cross-tenant falla'
);

select throws_ok(
    format(
        'select app.append_decision_log(null, %L, %L, %L, null, null, %L, %L, %L, %L, %L, %L::jsonb, 1, %L)',
        'system', 'system', 'test.platform',
        'test.policy', 'v1', 'ALLOW', 'OK', 'hash-y', '{}', 'trace-y'
    ),
    '42501',
    null,
    'decisión platform dentro de tenant falla'
);

select set_config('app.tenant_id', '', true);

-- Cadena de plataforma (tenant_id NULL).
select app.append_decision_log(
    null, 'platform_admin', 'platform-1', 'platform.create_tenant',
    'tenant', 'gov-a', 'platform.create_tenant', 'v1', 'ALLOW',
    'PLATFORM_ADMIN', 'hash-platform', '{"slug":"gov-a"}'::jsonb, 2, 'trace-p'
) as platform_log \gset

select ok(:'platform_log' <> '', 'append de plataforma devuelve id');
select ok(app.verify_decision_chain('platform'), 'cadena platform verifica');

-- Tamper: se desactiva el trigger solo para probar la detección.
reset role;
alter table app.decision_logs disable trigger decision_logs_append_only;
update app.decision_logs
set reason_code = 'TAMPERED'
where tenant_id = :'tenant_a'
  and seq = (
      select min(seq)
      from app.decision_logs
      where tenant_id = :'tenant_a'
  );
alter table app.decision_logs enable trigger decision_logs_append_only;

select is(app.verify_decision_chain(:'tenant_a'), false, 'tamper detectado');
select ok(app.verify_decision_chain('platform'), 'cadena platform intacta');

-- La cadena sobrevive al borrado del tenant: tenant_id pasa a NULL y chain_key
-- conserva la identidad de la cadena.
select app.create_tenant_with_owner(
    'gov-c', 'gov-c.growup.com', 'Gov C', null, null,
    '33333333-3333-4333-8333-333333333333', 'ownerc@example.com'
) as tenant_c \gset

set local role app_rw;
select set_config('app.tenant_id', :'tenant_c', true);

select app.append_decision_log(
    :'tenant_c', 'staff', 'user-3', 'content.publish', 'page', 'page-c',
    'content.publish', 'v1', 'ALLOW', 'VALID', 'hash-c',
    '{"slug":"home-c"}'::jsonb, 3, 'trace-c'
) as log_c \gset

select ok(:'log_c' <> '', 'append de tenant C devuelve id');
select ok(app.verify_decision_chain(:'tenant_c'), 'cadena C verifica antes de borrar');

reset role;
select lives_ok(
    format('delete from app.tenants where id = %L', :'tenant_c'),
    'borrar tenant no choca con append-only'
);

select is(
    (select count(*)::int from app.decision_logs where chain_key = :'tenant_c'),
    1,
    'la decisión se conserva tras borrar el tenant'
);
select is(
    (select tenant_id from app.decision_logs where chain_key = :'tenant_c'),
    null,
    'tenant_id queda en NULL'
);
select ok(app.verify_decision_chain(:'tenant_c'), 'cadena C verifica tras borrar');

select * from finish();
rollback;
