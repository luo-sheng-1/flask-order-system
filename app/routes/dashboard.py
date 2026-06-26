from datetime import date, datetime

from flask import Blueprint, jsonify
from sqlalchemy import text

from app import db
from app.models import Order, Product
from app.utils.db_helpers import execute_raw

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.route("/stats")
def stats():
    today = date.today()
    total_orders = Order.query.count()
    total_products = Product.query.count()
    total_revenue = (
        db.session.query(db.func.sum(Order.total_amount))
        .filter(Order.status != "cancelled")
        .scalar()
        or 0.0
    )

    today_orders = Order.query.filter(
        db.func.date(Order.created_at) == today.isoformat()
    ).count()

    return jsonify(
        {
            "total_orders": total_orders,
            "total_products": total_products,
            "total_revenue": float(total_revenue),
            "today_orders": today_orders,
        }
    )


@bp.route("/recent-activity")
def recent_activity():
    rows = execute_raw(
        "SELECT status, COUNT(*) as cnt FROM orders "
        "WHERE date(created_at) >= date('now', '-7 days') "
        "GROUP BY status"
    )
    return jsonify(
        {
            "period": "7 days",
            "data": [{"status": r[0], "count": r[1]} for r in rows],
        }
    )


@bp.route("/hourly-throughput")
def hourly_throughput():
    with db.engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT strftime('%H', created_at) as hour, COUNT(*) as cnt "
                "FROM orders WHERE date(created_at) = date('now') "
                "GROUP BY hour ORDER BY hour"
            )
        ).fetchall()

    return jsonify(
        {"date": date.today().isoformat(), "hourly": [{"hour": r[0], "count": r[1]} for r in rows]}
    )
