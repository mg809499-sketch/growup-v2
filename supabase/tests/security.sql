begin;

create schema if not exists extensions;
create extension if not exists pgtap with schema extensions;
grant usage on schema extensions to app_rw;
grant execute on all functions in schema extensions to app_rw;
set search_path = public, extensions;

select plan(10);

select ok(
    (
        select proconfig::text like '%pg_catalog%'
           and proconfig::text not like '%public%'
        from pg_proc
        where oid = 'app.resolve_tenant(text)'::regprocedure
    ),
    'resolve_tenant usa pg_catalog y app, sin public'
);

select ok(
    (
        select proconfig::text like '%pg_catalog%'
           and proconfig::text not like '%public%'
        from pg_proc
        where oid = 'app.is_platform_admin(uuid)'::regprocedure
    ),
    'is_platform_admin usa pg_catalog y app, sin public'
);

select ok(
    (
        select proconfig::text like '%pg_catalog%'
           and proconfig::text not like '%public%'
        from pg_proc
        where oid = 'app.create_tenant(text, text, text, text, uuid)'::regprocedure
    ),
    'create_tenant usa pg_catalog y app, sin public'
);

select ok(
    (
        select proconfig::text like '%pg_catalog%'
           and proconfig::text not like '%public%'
        from pg_proc
        where oid = 'app.append_decision_log(uuid, text, text, text, text, text, text, text, text, text, text, jsonb, integer, text)'::regprocedure
    ),
    'append_decision_log usa pg_catalog y app, sin public'
);

select ok(
    (
        select proconfig::text like '%pg_catalog%'
           and proconfig::text not like '%public%'
        from pg_proc
        where oid = 'app.verify_decision_chain(text)'::regprocedure
    ),
    'verify_decision_chain usa pg_catalog y app, sin public'
);

select ok(
    (
        select proconfig::text like '%pg_catalog%'
           and proconfig::text not like '%public%'
        from pg_proc
        where oid = 'app.create_tenant_with_owner(text, text, text, text, uuid, uuid, text)'::regprocedure
    ),
    'create_tenant_with_owner usa pg_catalog y app, sin public'
);

select ok(
    (
        select proconfig::text like '%pg_catalog%'
           and proconfig::text not like '%public%'
        from pg_proc
        where oid = 'app.expire_stale_uploads(integer)'::regprocedure
    ),
    'expire_stale_uploads usa pg_catalog y app, sin public'
);

select ok(
    not has_function_privilege(
        'app_rw',
        'app.expire_stale_uploads(integer)',
        'EXECUTE'
    ),
    'app_rw no puede ejecutar la limpieza cross-tenant'
);

select ok(
    has_function_privilege(
        'app_worker',
        'app.expire_stale_uploads(integer)',
        'EXECUTE'
    ),
    'app_worker puede ejecutar la limpieza cross-tenant acotada'
);

select ok(
    (
        select proconfig::text like '%pg_catalog%'
           and proconfig::text not like '%public%'
        from pg_proc
        where oid = 'app.list_tenants(uuid, text, text, integer, integer)'::regprocedure
    ),
    'list_tenants usa pg_catalog y app, sin public'
);

select * from finish();
rollback;
