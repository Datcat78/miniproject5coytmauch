# Task Tracker

A task manager website built with Flask for **INF601 - Advanced Programming in Python, Mini Project 5**
at Fort Hays State University.

**Author:** Coyt Mauch

## Description

Task Tracker is a Flask web application where users will be able to register, log in, and manage their
own list of tasks. The project follows the structure of the
[official Flask tutorial](https://flask.palletsprojects.com/en/stable/tutorial/): it uses an application
factory (`create_app()`), blueprints, and Jinja template inheritance.

## Current status

- Working pages: **Home** (`/`) and **About** (`/about`)
- SQLite database with `users` and `tasks` tables, created by `flask --app tasktracker init-db`
- Placeholder templates (no routes yet): Register, Log In, Dashboard, New Task, Edit Task
- Not implemented yet: user accounts and task management

## Database

The database is a SQLite file at `instance/tasktracker.sqlite`. It is not committed to Git; each copy
of the project creates its own with `init-db`.

| Table | Columns |
|---|---|
| `users` | `id` (primary key), `username` (unique), `password_hash` |
| `tasks` | `id` (primary key), `user_id` (foreign key to `users.id`), `title`, `description`, `is_complete` (0 or 1) |

Every task belongs to one user through `tasks.user_id`. Foreign key enforcement is turned on for every
connection, so SQLite rejects a task whose `user_id` doesn't match an existing user.

## Project structure

```
miniproject5coytmauch/
├── tasktracker/
│   ├── __init__.py        # Application factory: create_app()
│   ├── db.py              # SQLite connection helpers and the init-db command
│   ├── auth.py            # "auth" blueprint for accounts (placeholder)
│   ├── tasks.py           # "tasks" blueprint for task pages (placeholder)
│   ├── schema.sql         # Creates the users and tasks tables
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── base.html      # Shared layout every page extends
│       ├── home.html
│       ├── about.html
│       ├── auth/
│       │   ├── register.html
│       │   └── login.html
│       └── tasks/
│           ├── dashboard.html
│           ├── new.html
│           └── edit.html
├── tests/
│   ├── conftest.py        # pytest fixtures (app, client, and CLI runner)
│   ├── test_db.py         # Tests for the database and init-db
│   └── test_factory.py    # Tests for the factory, Home, and About
├── requirements.txt
└── README.md
```

## Setup

These commands are for Windows PowerShell, run from the project folder.

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   On macOS/Linux, activate with `source .venv/bin/activate` instead.

2. Install the dependencies:

   ```powershell
   pip install Flask pytest
   ```

3. Create the database:

   ```powershell
   flask --app tasktracker init-db
   ```

   This creates `instance/tasktracker.sqlite`. Running it again deletes all users and tasks and
   starts over with empty tables.

## Running the app

```powershell
flask --app tasktracker run --debug
```

Then open <http://127.0.0.1:5000/> in your browser.

## Running the tests

```powershell
python -m pytest
```

Use `python -m pytest` rather than `pytest` so the project folder is on the import path and the
tests can import the `tasktracker` package.
