-- ContextIQ minimal SQL seed
--
-- This is a SMALL, illustrative seed for quickly poking at the API/DB by
-- hand (e.g. via psql or a SQL client). For realistic, pattern-rich
-- behavioural data used by the ML pipeline, use
-- `scripts/generate_synthetic_data.py` instead (see README.md).
--
-- Usage:
--   psql "$DATABASE_URL" -f database/seeds/seed_demo.sql

BEGIN;

-- Demo user
INSERT INTO users (id, email, display_name, timezone, is_active, created_at, updated_at)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'seed.demo@contextiq.dev',
    'Seed Demo User',
    'UTC',
    true,
    now(),
    now()
)
ON CONFLICT (id) DO NOTHING;

-- Locations
INSERT INTO locations (id, user_id, name, location_type, is_active, created_at, updated_at)
VALUES
    ('22222222-2222-2222-2222-222222222221', '11111111-1111-1111-1111-111111111111', 'Home', 'HOME', true, now(), now()),
    ('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'Office Desk', 'WORK', true, now(), now()),
    ('22222222-2222-2222-2222-222222222223', '11111111-1111-1111-1111-111111111111', 'Gym', 'GYM', true, now(), now())
ON CONFLICT (id) DO NOTHING;

-- Tasks
INSERT INTO tasks (
    id, user_id, title, description, status, priority, due_at,
    estimated_minutes, context_location_id, context_tag, is_recurring,
    created_at, updated_at
)
VALUES
    (
        '33333333-3333-3333-3333-333333333331', '11111111-1111-1111-1111-111111111111',
        'Leave for work', NULL, 'COMPLETED', 'MEDIUM', now() - interval '1 day' + interval '2 hours',
        5, '22222222-2222-2222-2222-222222222221', 'home_morning', false, now() - interval '1 day', now() - interval '1 day'
    ),
    (
        '33333333-3333-3333-3333-333333333332', '11111111-1111-1111-1111-111111111111',
        'Take out the trash', NULL, 'FORGOTTEN', 'LOW', now() - interval '1 day' + interval '2 hours',
        5, '22222222-2222-2222-2222-222222222221', 'home_morning', false, now() - interval '1 day', now() - interval '1 day'
    ),
    (
        '33333333-3333-3333-3333-333333333333', '11111111-1111-1111-1111-111111111111',
        'Review PR comments', 'Address feedback on the auth PR', 'PENDING', 'HIGH', now() + interval '4 hours',
        30, '22222222-2222-2222-2222-222222222222', 'work_block', false, now(), now()
    )
ON CONFLICT (id) DO NOTHING;

-- Task events (illustrating the event model)
INSERT INTO task_events (id, task_id, user_id, event_type, occurred_at, location_id, created_at)
VALUES
    ('44444444-4444-4444-4444-444444444441', '33333333-3333-3333-3333-333333333331', '11111111-1111-1111-1111-111111111111', 'CREATED', now() - interval '1 day', '22222222-2222-2222-2222-222222222221', now() - interval '1 day'),
    ('44444444-4444-4444-4444-444444444442', '33333333-3333-3333-3333-333333333331', '11111111-1111-1111-1111-111111111111', 'STARTED', now() - interval '1 day' + interval '1 minute', '22222222-2222-2222-2222-222222222221', now() - interval '1 day'),
    ('44444444-4444-4444-4444-444444444443', '33333333-3333-3333-3333-333333333331', '11111111-1111-1111-1111-111111111111', 'COMPLETED', now() - interval '1 day' + interval '10 minutes', '22222222-2222-2222-2222-222222222221', now() - interval '1 day'),
    ('44444444-4444-4444-4444-444444444444', '33333333-3333-3333-3333-333333333332', '11111111-1111-1111-1111-111111111111', 'CREATED', now() - interval '1 day', '22222222-2222-2222-2222-222222222221', now() - interval '1 day'),
    ('44444444-4444-4444-4444-444444444445', '33333333-3333-3333-3333-333333333332', '11111111-1111-1111-1111-111111111111', 'FORGOTTEN', now() - interval '1 day' + interval '3 hours', '22222222-2222-2222-2222-222222222221', now() - interval '1 day')
ON CONFLICT (id) DO NOTHING;

-- Interruptions
INSERT INTO interruptions (id, user_id, task_id, interruption_type, occurred_at, duration_seconds, location_id, created_at)
VALUES
    ('55555555-5555-5555-5555-555555555551', '11111111-1111-1111-1111-111111111111', NULL, 'SOCIAL_MEDIA', now() - interval '2 hours', 120, '22222222-2222-2222-2222-222222222221', now()),
    ('55555555-5555-5555-5555-555555555552', '11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333', 'MESSAGE', now() - interval '1 hour', 60, '22222222-2222-2222-2222-222222222222', now())
ON CONFLICT (id) DO NOTHING;

COMMIT;
