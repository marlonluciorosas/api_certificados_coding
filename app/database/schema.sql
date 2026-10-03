-- Estrutura do banco do Atividade de Victor lalala.
-- Este arquivo é lido por app/database/schema.py e executado pelo SQLite.
-- Todas as tabelas usam "IF NOT EXISTS" para poder rodar várias vezes.

PRAGMA foreign_keys = ON;

-- Usuários: agora com senha (hash) e curso de origem.
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL CHECK (length(trim(name)) >= 2),
    email         TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL CHECK (length(password_hash) > 20),
    role          TEXT NOT NULL CHECK (role IN ('participante', 'professor', 'admin')),
    course_id     INTEGER,
    created_at    TEXT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
);

-- Cursos da faculdade (ADS, Ciência da Computação, etc.).
CREATE TABLE IF NOT EXISTS courses (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL CHECK (length(trim(name)) >= 3),
    code           TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK (length(trim(code)) >= 2),
    coordinator_id INTEGER,
    created_at     TEXT NOT NULL,
    FOREIGN KEY (coordinator_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Eventos: cada evento pertence a um curso e tem um responsável.
CREATE TABLE IF NOT EXISTS events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT NOT NULL CHECK (length(trim(title)) >= 3),
    description    TEXT NOT NULL DEFAULT '',
    start_at       TEXT NOT NULL,
    location       TEXT NOT NULL CHECK (length(trim(location)) >= 2),
    capacity       INTEGER NOT NULL CHECK (capacity > 0),
    duration_hours REAL NOT NULL CHECK (duration_hours > 0),
    responsible_id INTEGER NOT NULL,
    course_id      INTEGER,
    created_at     TEXT NOT NULL,
    FOREIGN KEY (responsible_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
);

-- Inscrições: o UNIQUE(user_id, event_id) é a última proteção da RN01,
-- mesmo se dois pedidos chegarem juntos.
CREATE TABLE IF NOT EXISTS registrations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    event_id     INTEGER NOT NULL,
    status       TEXT NOT NULL DEFAULT 'inscrita'
                 CHECK (status IN ('inscrita', 'cancelada')),
    attended     INTEGER NOT NULL DEFAULT 0 CHECK (attended IN (0, 1)),
    created_at   TEXT NOT NULL,
    cancelled_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE (user_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_registrations_event_status
    ON registrations(event_id, status);
CREATE INDEX IF NOT EXISTS idx_registrations_user
    ON registrations(user_id);
CREATE INDEX IF NOT EXISTS idx_events_course
    ON events(course_id);
CREATE INDEX IF NOT EXISTS idx_users_course
    ON users(course_id);