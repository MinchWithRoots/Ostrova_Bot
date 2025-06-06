import sqlite3

DB_NAME = "ostrova.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    with open("schema.sql", "r") as f:
        schema = f.read()
    cursor.executescript(schema)
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_NAME)

def save_user_to_db(first_name, last_name, user_id=0):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO Users (user_id, first_name, last_name) VALUES (?, ?, ?)", (user_id, first_name, last_name))
    conn.commit()
    conn.close()

def update_user_field(user_id, field, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE Users SET {field}=? WHERE user_id=?", (value, user_id))
    conn.commit()
    conn.close()

def user_exists_in_db(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM Users WHERE user_id=?", (user_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def get_user_info(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT first_name, last_name, birthdate, phone FROM Users WHERE user_id=?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result

def register_for_item(user_id, item_type, item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Registrations (user_id, type, item_id, status) VALUES (?, ?, ?, 'active')", (user_id, item_type, item_id))
    conn.commit()
    conn.close()

def get_all_clubs():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Clubs WHERE active=1")
    result = cur.fetchall()
    conn.close()
    return result

def get_all_events():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Events WHERE active=1")
    result = cur.fetchall()
    conn.close()
    return result

def get_all_faq():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM FAQ")
    result = cur.fetchall()
    conn.close()
    return result
