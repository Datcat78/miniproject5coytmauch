-- Task Tracker database schema
-- Run with: flask --app tasktracker init-db
-- WARNING: this drops the existing tables, deleting all users and tasks.

-- Drop tasks before users: tasks references users, so with foreign keys
-- enforced, users can't be dropped while task rows still point at it.
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL
);

CREATE TABLE tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  -- SQLite has no boolean type: 0 = not complete, 1 = complete
  is_complete INTEGER NOT NULL DEFAULT 0 CHECK (is_complete IN (0, 1)),
  FOREIGN KEY (user_id) REFERENCES users (id)
);
