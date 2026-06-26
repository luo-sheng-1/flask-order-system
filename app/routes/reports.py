import threading

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from app import db

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def _generate_daily_summary(app):
    app.app_context().push()
    result = db.session.execute(
        text(
            "SELECT COUNT(*) as cnt, SUM(amount) as total "
            "FROM orders WHERE date(created_at) = date('now')"
        )
    ).first()
    total = float(result.total) if result.total else 0.0
    count = int(result.cnt) if result.cnt else 0
    print(f"[DailyReport] {count} orders, total ¥{total:.2f}")


@bp.route("/daily-summary")
def daily_summary():
    app = current_app._get_current_object()
    thread = threading.Thread(target=_generate_daily_summary, args=(app,))
    thread.start()
    thread.join()
    return jsonify({"status": "report generation started"})
