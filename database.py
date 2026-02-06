import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "platform.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student','company','admin'))
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS student_profile (
            user_id INTEGER PRIMARY KEY,
            skills TEXT,
            cgpa REAL DEFAULT 0,
            interest_domain TEXT,
            experience_years INTEGER DEFAULT 0,
            resume_path TEXT,
            past_education TEXT,
            profile_photo TEXT,
            extracted_skills TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS company_profile (
            user_id INTEGER PRIMARY KEY,
            company_name TEXT,
            location TEXT,
            contact_email TEXT,
            contact_no TEXT,
            profile_logo TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS company_positions (
            position_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            domain TEXT,
            required_skills TEXT,
            min_cgpa REAL DEFAULT 0,
            positions INTEGER DEFAULT 0,
            stipend INTEGER DEFAULT 0,
            FOREIGN KEY(company_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            company_id INTEGER NOT NULL,
            position_id INTEGER NOT NULL,
            score REAL,
            rank INTEGER,
            UNIQUE(student_id),
            FOREIGN KEY(student_id) REFERENCES users(user_id),
            FOREIGN KEY(company_id) REFERENCES users(user_id),
            FOREIGN KEY(position_id) REFERENCES company_positions(position_id)
        )
        """)
        conn.commit()
    print("Database schema ready")