PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Clubs (
    club_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    active BOOLEAN
);

CREATE TABLE IF NOT EXISTS Club_Schedule (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER,
    date DATE,
    day_of_week TEXT,
    start_time TEXT,
    end_time TEXT,
    max_participants INTEGER,
    current_participants INTEGER,
    FOREIGN KEY(club_id) REFERENCES Clubs(club_id)
);

CREATE TABLE IF NOT EXISTS Events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    date DATE,
    time TEXT,
    location TEXT,
    max_participants INTEGER,
    current_participants INTEGER,
    active BOOLEAN
);

CREATE TABLE IF NOT EXISTS FAQ (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT
);

CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    birthdate DATE,
    phone TEXT,
    reg_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS Registrations (
    reg_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT CHECK(type IN ('event', 'club')),
    item_id INTEGER,
    date DATE,
    time TEXT,
    status TEXT CHECK(status IN ('cancelled', 'active')),
    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);
