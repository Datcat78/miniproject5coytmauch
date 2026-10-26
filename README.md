# Task Tracker

A task manager website built with Flask for **INF601 - Advanced Programming in Python, Mini Project 5**
at Fort Hays State University.

**Author:** Coyt Mauch

## Description

Task Tracker is a Flask web application where users register, log in, and manage their own private
list of tasks. The project follows the structure of the
[official Flask tutorial](https://flask.palletsprojects.com/en/stable/tutorial/): it uses an application
factory (`create_app()`), blueprints, and Jinja template inheritance.

## Features

- Register, log in, and log out, with hashed passwords and Flask sessions
- A private dashboard showing only your own tasks and how many you've completed
- Add tasks with a title and an optional description
- Edit a task's title, description, and completed status
- Mark tasks complete or not complete with one click, and delete tasks
- Green success and red error messages after every action
- Every page, including error pages like 404 Not Found, extends `base.html`

## Pages

| URL | Methods | What it does | Login required |
|---|---|---|---|
| `/` | GET | Home page | No |
| `/about` | GET | About page | No |
| `/auth/register` | GET, POST | Registration form; creates the account | No |
| `/auth/login` | GET, POST | Login form; starts the session | No |
| `/auth/logout` | POST | Ends the session, then goes to Home | No |
| `/tasks/` | GET | Dashboard: your tasks | Yes |
| `/tasks/new` | GET, POST | Add Task form; saves the new task | Yes |
| `/tasks/<id>/edit` | GET, POST | Edit Task form; saves the changes | Yes, and it must be your task |
| `/tasks/<id>/toggle` | POST | Marks the task complete or not complete | Yes, and it must be your task |
| `/tasks/<id>/delete` | POST | Deletes the task | Yes, and it must be your task |

Every action that changes data (logging out, toggling, deleting, and submitting forms) only accepts
POST, so following a link can never change anything.

## Accounts and security

- **Passwords are never stored.** Registration saves only a salted hash from Werkzeug's
  `generate_password_hash`, and login checks it with `check_password_hash`.
- **Registration rules:** usernames are 3 to 30 letters, numbers, or underscores and must be unique;
  passwords must be at least 8 characters and typed twice. The browser checks these first, and the
  server checks them again.
- **Sessions:** after login, Flask's session cookie stores only the user's id. The cookie is signed with
  the secret key, so it can't be edited or forged.
- **Private pages** use the `@login_required` decorator, which sends logged-out visitors to the login
  page.
- **Users can only see and change their own tasks.** Every task query filters by the logged-in user's
  id, which comes from the session and never from the form. Trying to view, edit, complete, or delete
  another user's task gives a 404 Not Found.
- **Task forms are validated on the server:** the title is required and up to 100 characters, and the
  description is optional and up to 1000 characters.
- **Parameterized SQL:** every query passes user input as `?` parameters, never by building SQL strings,
  so input can't change the query.
- **Jinja escapes everything it displays**, so HTML typed into a task can't run as code on the page.

### Secret key

The app falls back to the development-only secret key `"dev"`. Anywhere other than your own computer,
set the `SECRET_KEY` environment variable to a long random value:

```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex())"
flask --app tasktracker run
```

This sets the key for the current PowerShell window only. Never commit a real secret key to Git.

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
│   ├── __init__.py        # Application factory: create_app(), Home, About, error pages
│   ├── db.py              # SQLite connection helpers and the init-db command
│   ├── auth.py            # Register, login, logout, and @login_required
│   ├── tasks.py           # Dashboard, add, edit, complete, and delete tasks
│   ├── schema.sql         # Creates the users and tasks tables
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── base.html      # Shared layout every page extends
│       ├── home.html
│       ├── about.html
│       ├── error.html     # 404 and other error pages
│       ├── auth/
│       │   ├── register.html
│       │   └── login.html
│       └── tasks/
│           ├── dashboard.html
│           ├── new.html
│           └── edit.html
├── tests/
│   ├── conftest.py        # pytest fixtures (app, client, CLI runner, and auth helper)
│   ├── data.sql           # Two test users, each with one task
│   ├── test_auth.py       # Tests for registration, login, and logout
│   ├── test_db.py         # Tests for the database and init-db
│   ├── test_factory.py    # Tests for the factory, secret key, page layout, and error pages
│   └── test_tasks.py      # Tests for every task action, validation, and task privacy
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
