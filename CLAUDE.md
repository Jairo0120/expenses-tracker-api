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
  `expenses-tracker-tasks` (`api/tasks.py:lambda_handler`). Deploys are done by the user.
- `api/tasks.py` rolls cycles over: creates new cycles and copies recurrent incomes, expenses, savings and
  budgets into them. Recurrent entries only affect future cycles.

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

## Recent history (see `git log`)

2026-09-25/26, while porting the Android app: movement-date defaults evaluated per record; saving-type
lookups scoped to the user; 404s for unknown cycles; budget clearing/validation on expense updates;
`budget_id` 0 handling; bound SQL parameters; JWT leeway and 401 for invalid tokens. Not yet deployed to prod
as of 2026-09-26 unless the user says otherwise.
