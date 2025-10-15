
import sqlite3
from datetime import datetime


#==========Connect to Database========

def get_connection():
    """Create / connect to SQLite database"""
    return sqlite3.connect("quiz_app.db", check_same_thread=False)

#=========Create Table (with all required columns)===========

def create_table():
    """Create quiz_results table if it doesn't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            correct INTEGER,
            incorrect INTEGER,
            marks_obtained INTEGER,
            total_marks INTEGER,
            percentage REAL,
            quiz_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(" Table created / exists already.")


# ================Save Quiz Result========

def save_result(correct, incorrect, marks_obtained, total_marks, percentage):
    """Save a single quiz attempt into the database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO quiz_results (correct, incorrect, marks_obtained, total_marks, percentage)
        VALUES (?, ?, ?, ?, ?)
    ''', (correct, incorrect, marks_obtained, total_marks, percentage))
    conn.commit()
    conn.close()
    print(" Quiz result saved.")


#=================Fetch All Results================

def fetch_results():
    """Fetch all quiz results in descending order (latest first)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT correct, incorrect, marks_obtained, total_marks, percentage, quiz_date
        FROM quiz_results
        ORDER BY quiz_date DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows


#==========Initialize Table on first run===========

if __name__ == "__main__":
    create_table()
