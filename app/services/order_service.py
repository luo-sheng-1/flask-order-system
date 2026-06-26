from sqlalchemy import text

from app import db
from app.models import Order


def batch_update_order_status(order_ids, new_status):
    valid_statuses = {"confirmed", "shipped", "delivered", "cancelled"}
    if new_status not in valid_statuses:
        return {"updated": 0, "failed": len(order_ids), "error": f"invalid status: {new_status}"}

    conn = db.engine.connect()
    updated = 0
    failed = 0
    try:
        for oid in order_ids:
            order = db.session.get(Order, oid)
            if not order:
                failed += 1
                continue
            if order.status == new_status:
                failed += 1
                continue
            order.status = new_status
            conn.execute(
                text("UPDATE orders SET status = :status, updated_at = datetime('now') WHERE id = :id"),
                {"status": new_status, "id": oid},
            )
            updated += 1
        db.session.commit()
        conn.close()
    except Exception:
        db.session.rollback()
        failed = len(order_ids) - updated
    return {"updated": updated, "failed": failed}
