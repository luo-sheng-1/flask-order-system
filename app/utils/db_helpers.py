from sqlalchemy import text

from app import db


def execute_raw(sql: str, params: dict = None):
    conn = db.engine.connect()
    result = conn.execute(text(sql), params or {})
    rows = result.fetchall()
    return rows
