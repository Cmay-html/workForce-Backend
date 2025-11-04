# WorkForce Backend

A Flask-based backend for a freelance marketplace. It provides REST APIs (with Swagger docs) for auth, projects, applications, invoices, payments, and more. The project uses an application-factory pattern and is designed for deployment on services like Render.

## Features

- Flask-RESTX API with interactive docs at `/api/docs`
- JWT authentication (access tokens) with role-aware endpoints
- Role-based project visibility and CRUD (client vs freelancer)
- Applications, invoices, payments, receipts wiring via namespaces
- CORS configured for local dev and Netlify deployments
- Database migrations with Flask-Migrate/Alembic
- Marshmallow serialization
- Email configuration via Flask-Mail (optional)

> Note: Real-time chat and a freelancer directory are planned; ensure the corresponding modules and Socket.IO setup are present before enabling those imports.

## Tech stack

- Python, Flask, Flask-RESTX, Flask-JWT-Extended
- SQLAlchemy + Flask-SQLAlchemy
- Alembic/Flask-Migrate
- Marshmallow / Flask-Marshmallow
- Flask-Mail (optional)
- Gunicorn (deployment)

## Project layout

```
run.py                  # WSGI entry (imports src.app with ProdConfig)
src/
  app.py                # Application factory + route registration
  config.py             # Dev/Prod configuration and env handling
  extensions.py         # db, migrate, jwt, ma, mail, api instances
  routes/               # Namespaces and route registration
migrations/             # Alembic migration scaffolding
requirements.txt        # Python dependencies
```

## Getting started

### 1) Clone and set up a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Configure environment variables

The app loads environment variables from `src/.env` (if present) and the system environment. Recommended variables:

- SECRET_KEY
- FLASK_ENV=development
- DATABASE_URL=postgresql+psycopg2://<user>:<pass>@<host>:<port>/<db>
- JWT_SECRET_KEY
- MAIL_SERVER=smtp.gmail.com
- MAIL_PORT=587
- MAIL_USE_TLS=True
- MAIL_USERNAME=<email>
- MAIL_PASSWORD=<app_password>
- MAIL_DEFAULT_SENDER=noreply@workforce.com

Create a `src/.env` file to simplify local dev, e.g.:

```
FLASK_ENV=development
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/workdb
JWT_SECRET_KEY=change-me
SECRET_KEY=change-me-too
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@workforce.com
```

### 3) Initialize the database

Make sure your Postgres database exists and is reachable via `DATABASE_URL`, then run migrations:

```bash
# If your environment is active (venv) and FLASK_APP points to the factory
export FLASK_APP=src.app:create_app
flask db upgrade
```

- To create a new migration after model changes:

```bash
flask db migrate -m "Describe your change"
flask db upgrade
```

### 4) Run the server (local)

Use the Flask CLI (dev-friendly):

```bash
export FLASK_APP=src.app:create_app
flask run --debug
```

Alternatively, run the WSGI entrypoint:

```bash
python run.py
```

This starts the API, with Swagger docs at:

- http://localhost:5000/api/docs

### 5) Auth usage

- Obtain a JWT via the auth endpoints (see `/api/docs`).
- Send it as an Authorization header: `Authorization: Bearer <token>`.

## Key endpoints (high level)

Namespace registration happens in `src/app.py` and routes live under `src/routes/`.

- Auth: `POST /api/auth/signup`, `POST /api/auth/login`
- Projects: `GET /api/projects/` (role-aware), `POST /api/projects/` (client), and additional visibility endpoints if present
- Applications: under `/api/applications`
- Invoices: under `/api/invoices`
- Payments/Receipts: under their respective namespaces

Use `/api/docs` for the canonical contract and try-it-out.

## Configuration details

From `src/config.py`:

- Uses `DATABASE_URL` (normalized to `postgresql+psycopg2://`)
- `JWT_SECRET_KEY` with 24-hour access tokens by default
- Dev and Prod classes (Dev enables DEBUG)
- Optional mail settings

## Deployment

- WSGI: `gunicorn run:app` (uses `ProdConfig` via `run.py`)
- Ensure `DATABASE_URL`, `SECRET_KEY`, and `JWT_SECRET_KEY` are set in the environment
- If enabling real-time chat, you may need an async worker (e.g., eventlet) and a Socket.IO server setup

## CORS

`src/app.py` configures CORS for local development (`http://localhost:5173`, `http://localhost:3000`, etc.) and Netlify-origin URLs. Update the allowed origins list as needed.

## Troubleshooting

- 401 with JWT: tokens may be expired or malformed—re-login and ensure `Authorization: Bearer <token>` header
- DB connection errors: verify `DATABASE_URL` and that Postgres is reachable
- Migrations: if you change models, create and apply a new migration
- Missing modules (chat/freelancers_list): if you see import errors for `src/routes/chat.py` or `src/routes/freelancers_list.py`, create those modules or remove their imports in `src/app.py`
- Socket.IO: if enabled, make sure the socket instance is created in `src/extensions.py` and initialized in `src/app.py`

## License

This project is licensed under the MIT License. See `LICENSE` for details.
