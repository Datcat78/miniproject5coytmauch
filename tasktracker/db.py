# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    """Return the database connection for the current request, opening it if needed."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        # Return rows that can be accessed by column name, like row["title"]
        g.db.row_factory = sqlite3.Row
        # SQLite leaves foreign key enforcement off by default, and the setting
        # only lasts for one connection, so turn it on every time we connect
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


def close_db(e=None):
    """Close the database connection if this request opened one."""
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Clear any existing data and create the tables from schema.sql."""
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo(f"Initialized the database at {current_app.config['DATABASE']}")


def init_app(app):
    """Register the database functions with the Flask app."""
    # Close the connection after each request (and after each CLI command)
    app.teardown_appcontext(close_db)
    # Add "flask init-db" to the Flask command line
    app.cli.add_command(init_db_command)
