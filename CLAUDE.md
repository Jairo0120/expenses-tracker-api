# Expenses Tracker — backend

FastAPI + SQLModel (SQLite) API for a personal budgeting app: expenses, incomes and savings grouped into
monthly **cycles**, with per-cycle budgets and recurrent entries. Clients authenticate with Auth0 access
tokens (RS256, validated against the tenant certificate).

Clients (sibling repos in `~/projects`, each with context of its own):
- `expenses-tracker-android` — native Android app (Kotlin/Compose), the current client. Its CLAUDE.md
  describes the whole project and history.
- `expenses-tracker-app` — the original Expo app, kept for reference.

Also in this repo: `app/` is a separate script that reads bank-notification emails (Outlook) and posts them
as expenses (`source = "Email"`).

Follow-ups and known quirks are tracked in a Claude Doc:
https://claude.ai/code/artifact/e725ea4c-d2ad-4546-96eb-20acb2935e62

## Run and test

- Poetry env (Python 3.12): `poetry run pytest api -q` (all tests must pass), `poetry run flake8 <files>`
  (79-char lines; older files have pre-existing warnings — keep touched files clean).
- Dev server: `poetry run fastapi dev api/main.py --host 0.0.0.0` (auto-reloads) on port 8000, reachable from
  the phone at `http://192.168.0.218:8000` thanks to a ufw rule. Config comes from `.env` (see
  `.env.example`): certificate path, audience list, SQLite path. The dev DB holds only test data.
- Prod: AWS Lambda behind API Gateway (`/prod` root path, via Mangum). `deploy-image.sh` (untracked) runs the
  tests, builds `Dockerfile.prod`, pushes to ECR and updates two functions: `expenses-tracker` (the API) and
  `expenses-tracker-tasks` (`api/tasks.py:lambda_handler`), then waits for both and invokes the tasks Lambda
  so migrations run before users hit the new code. Deploys are done by the user. Lambda settings since
  2026-09-27: API 60 s / 512 MB, tasks 120 s / 512 MB (the 3 s / 128 MB defaults timed out migration 0002 on
  EFS). `.dockerignore` keeps database files out of the image — never leave a DB copy in `api/`.
- `api/tasks.py` rolls cycles over: creates new cycles and copies recurrent incomes, expenses, savings and
  budgets into them. Recurrent entries only affect future cycles.
- Schema changes go through Alembic (`api/migrations/`, config in `alembic.ini`):
  `poetry run alembic revision --autogenerate -m "…"` (review the result; SQLite uses batch mode), and
  `poetry run alembic -x url=sqlite:///path/to/copy.db upgrade head` to try one on a copy.
  `api.database.run_migrations()` runs at every start of both Lambdas and of the dev server, in a single
  `BEGIN IMMEDIATE` transaction (Python's sqlite3 otherwise autocommits DDL and a failure would leave a
  half-migrated DB). A DB with tables but no recorded revision is stamped as the baseline `0001` first.
  Never use `SQLModel.metadata.create_all` against real databases. Back up the prod DB before deploying a
  new migration.

## Layout

- `api/main.py` — app + routers. `api/dependencies.py` — settings, DB session, Auth0 token validation
  (`get_current_user`, 10 s leeway for clock skew; any invalid token → 401).
- `api/models.py` — tables plus request/response models (`*Create`, `*Update`, `*Public`).
- `api/routers/` — one module per resource: expenses, budgets, incomes, savings (+ grouped summary and
  withdrawals), recurrent_* , cycles (`cycle-status`, `list-cycles`), users, categories, sandbox.
- `api/tests/` — pytest with an in-memory SQLite session (`fixtures/`); the `client` fixture acts as user 1.
  `test_auth.py` signs real tokens with a throwaway certificate.

## Conventions and gotchas

- List endpoints take `skip`/`limit` (default 100; the apps page by 10). A missing `cycle_id` means the user's
  active cycle; an unknown one is a 404.
- Datetimes are stored naive and are UTC. `date_*` defaults use `default_factory` (evaluated per record).
- `budget_id = 0` means "no budget": the list filter for unbudgeted expenses, and treated as None on create;
  on update an explicit null (or 0) clears the budget. Budgets are validated against the expense's cycle.
- `GET /budgets` prepends a synthetic "Sin ppto." row (id 0) when there are unbudgeted expenses.
- Saving types are per user and matched by capitalized description. Editing a saving's (or recurrent
  saving's) description renames the whole type — intended behaviour.
- Raw SQL (`text()`) must use bound parameters.
- Sync support (for the offline-capable Android app; plan in its CLAUDE.md): every table has `uuid`,
  `deleted_at` and `sync_version`. `models.assign_sync_versions` (a `before_flush` hook) gives every insert
  or change the next value of the counter in `syncstate`, so ORM writes are versioned automatically — bulk
  `update()`/`delete()` statements bypass it, use ORM objects. Cycles are unique per (user, start_date);
  copies of recurrent entries carry `recurrent_*_id`, unique per cycle.
- Deletes are soft: `soft_delete(session, record)` (a deleted budget is also cleared from its expenses), and
  every query uses `select_live(Model)` or filters `deleted_at IS NULL` (raw SQL too). Timestamps are naive
  UTC via `models.utcnow()`.
- `GET /sync?since=&limit=&window_start=` / `POST /sync` (`api/sync.py`, protocol in its docstring): records
  by uuid with uuid references; the `ENTITIES` table describes each synced model. Push statuses: applied,
  stale (older than the server copy, or deleted — delete wins), merged (natural-key duplicate: same month,
  saving-type name, or recurrent copy per cycle; client switches to the returned uuid), rejected.
  `window_start` limits budgets/expenses/incomes to recent cycles; savings are never windowed.

## Recent history (see `git log`)

2026-09-25/26, while porting the Android app: movement-date defaults evaluated per record; saving-type
lookups scoped to the user; 404s for unknown cycles; budget clearing/validation on expense updates;
`budget_id` 0 handling; bound SQL parameters; JWT leeway and 401 for invalid tokens. All deployed to prod on
2026-09-26. `deploy-image.sh` builds with `--provenance=false --sbom=false`: Lambda rejects the attestation
image index Docker's containerd image store produces by default.
