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

This is the initial project structure.

- Working pages: **Home** (`/`) and **About** (`/about`)
- Placeholder templates (no routes yet): Register, Log In, Dashboard, New Task, Edit Task
- Not implemented yet: the database, user accounts, and task management

## Project structure

```
miniproject5coytmauch/
├── tasktracker/
│   ├── __init__.py        # Application factory: create_app()
│   ├── db.py              # Database helpers (placeholder)
│   ├── auth.py            # "auth" blueprint for accounts (placeholder)
│   ├── tasks.py           # "tasks" blueprint for task pages (placeholder)
│   ├── schema.sql         # Database schema (placeholder)
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
│   ├── conftest.py        # pytest fixtures (app and client)
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
