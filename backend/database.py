
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "analyses.db"


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                analysis_id TEXT PRIMARY KEY,
                resume_text TEXT NOT NULL,
                skills TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS job_match_results (
                analysis_id TEXT PRIMARY KEY,
                job_description TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
        connection.execute(
            "DELETE FROM job_match_results WHERE analysis_id = ?",
            (analysis_id,)
        )

        cursor = connection.execute(
            "DELETE FROM analyses WHERE analysis_id = ?",
            (analysis_id,)
        )

        return cursor.rowcount > 0


def save_match_result(analysis_id, job_description, result):
    result_json = json.dumps(result)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO job_match_results (
                analysis_id,
                job_description,
                result_json
            )
            VALUES (?, ?, ?)
            ON CONFLICT(analysis_id) DO UPDATE SET
                job_description = excluded.job_description,
                result_json = excluded.result_json,
                created_at = CURRENT_TIMESTAMP
            """,
            (analysis_id, job_description, result_json)
        )


def get_match_result(analysis_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT analysis_id, job_description, result_json, created_at
            FROM job_match_results
            WHERE analysis_id = ?
            """,
            (analysis_id,)
        ).fetchone()

    if row is None:
        return None

    return {
        "analysis_id": row["analysis_id"],
        "job_description": row["job_description"],
        **json.loads(row["result_json"]),
        "created_at": row["created_at"]
    }