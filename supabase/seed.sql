-- Seed mínimo de desarrollo. Los precios y límites definitivos se cierran
-- después del piloto (D-01); estos valores son placeholders.
insert into app.plans (code, name, price_cents, currency, billing_interval, trial_days, features)
values
    ('starter', 'Starter', 0, 'COP', 'month', 14, '{"placeholder": true}'::jsonb),
    ('pro', 'Pro', 0, 'COP', 'month', 14, '{"placeholder": true}'::jsonb)
on conflict (code) do nothing;
