
import json
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "analyses.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                analysis_id TEXT PRIMARY KEY,
                resume_text TEXT NOT NULL,
                skills TEXT NOT NULL
            )
        """)


def save_analysis(analysis_id, resume_text, skills):
    skills_json = json.dumps(skills)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO analyses (analysis_id, resume_text, skills)
            VALUES (?, ?, ?)
            """,
            (analysis_id, resume_text, skills_json)
        )


def get_analysis(analysis_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT analysis_id, resume_text, skills
            FROM analyses
            WHERE analysis_id = ?
            """,
            (analysis_id,)
        ).fetchone()

    if row is None:
        return None

    return {
        "analysis_id": row["analysis_id"],
        "text": row["resume_text"],
        "skills": json.loads(row["skills"])
    }


def delete_analysis(analysis_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM analyses WHERE analysis_id = ?",
            (analysis_id,)
        )

        return cursor.rowcount > 0