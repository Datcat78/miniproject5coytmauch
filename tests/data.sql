-- Test data loaded into every test database by tests/conftest.py
-- The hashes were made with werkzeug.security.generate_password_hash:
--   test  -> test-password
--   other -> other-password

INSERT INTO users (username, password_hash)
VALUES
  ('test', 'scrypt:32768:8:1$F3v14bBKpj75kPMY$83c96c4bcc4a946b5dd9845334d3c3bcd12d2bfbf89751b85c0af5275c2be547cde7e7c465242302d1790f94f985d7e15b190f0232710972f988dff27e6ded97'),
  ('other', 'scrypt:32768:8:1$6fSIvupAtMKXogGs$f8a8da6c1b78b18c3562fb682e56546303eaf2862ef2f002b19fec5c43558d9672b05b9d52f3dbfd731ad029034f3844f971a6b493752ac60983e46b711b957a');

INSERT INTO tasks (user_id, title, description)
VALUES
  (1, 'Finish the INF601 project', 'Belongs to the test user'),
  (2, 'Other user private task', 'Belongs to the other user');
