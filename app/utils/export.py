import csv
import os
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import Config

_raw_engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
ExportSession = sessionmaker(bind=_raw_engine)


def export_orders_to_file():
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
