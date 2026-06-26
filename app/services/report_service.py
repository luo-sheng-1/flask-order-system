from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app import db
from config import Config


def generate_sales_report(start_date: date, end_date: date):
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    stats = {}
    with db.engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT COUNT(*) as cnt, COALESCE(SUM(total_amount), 0) as total "
                "FROM orders WHERE date(created_at) BETWEEN :start AND :end "
                "AND status != 'cancelled'"
            ),
            {"start": start_str, "end": end_str},
        ).first()
        stats["order_count"] = int(result.cnt) if result.cnt else 0
        stats["total_revenue"] = float(result.total) if result.total else 0.0

        top_result = conn.execute(
            text(
                "SELECT p.name, SUM(oi.quantity) as sold, SUM(oi.subtotal) as revenue "
                "FROM order_items oi JOIN products p ON p.id = oi.product_id "
                "JOIN orders o ON o.id = oi.order_id "
                "WHERE date(o.created_at) BETWEEN :start AND :end "
                "AND o.status != 'cancelled' "
                "GROUP BY p.name ORDER BY sold DESC LIMIT 10"
            ),
            {"start": start_str, "end": end_str},
        ).fetchall()

        stats["top_products"] = [
            {"name": r[0], "sold": r[1], "revenue": float(r[2])} for r in top_result
        ]

    return stats


def get_daily_summary():
    conn = db.engine.connect()
    today = date.today().isoformat()
    result = conn.execute(
        text(
            "SELECT status, COUNT(*) as cnt, COALESCE(SUM(total_amount), 0) as total "
            "FROM orders WHERE date(created_at) = :today GROUP BY status"
        ),
        {"today": today},
    ).fetchall()

    summary = {"date": today, "total_orders": 0, "total_amount": 0.0, "by_status": {}}
    for row in result:
        status = row[0]
        cnt = int(row[1])
        amt = float(row[2])
        summary["by_status"][status] = {"count": cnt, "amount": amt}
        summary["total_orders"] += cnt
        summary["total_amount"] += amt

    return summary
