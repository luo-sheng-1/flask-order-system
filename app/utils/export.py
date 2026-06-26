import csv
import os
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import Config

# BUG: a module-level raw engine + sessionmaker is created outside of
# Flask-SQLAlchemy's management.  Sessions obtained from ExportSession
# are never tracked by the Flask app's teardown_appcontext, so calling
# code must remember to close() every session manually.  If any caller
# forgets, the connection is leaked.
_raw_engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
ExportSession = sessionmaker(bind=_raw_engine)


def export_orders_to_file():
    """
    Export orders to a CSV file using a raw session.
    BUG: the session is created but never closed.  Its connection
    stays checked out of the pool until the process exits.
    """
    session = ExportSession()
    rows = session.execute(
        text("SELECT id, product_id, quantity, amount, status FROM orders")
    ).fetchall()

    fd, path = tempfile.mkstemp(suffix=".csv", prefix="orders_export_")
    with os.fdopen(fd, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "product_id", "quantity", "amount", "status"])
        for row in rows:
            writer.writerow(row)
    return path
