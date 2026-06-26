from flask import Blueprint, jsonify, request
from sqlalchemy import text

from app import db
from app.models import Order, Product

bp = Blueprint("orders", __name__, url_prefix="/api/orders")


@bp.route("/list")
def list_orders():
    orders = db.session.query(Order).order_by(Order.created_at.desc()).limit(50).all()
    return jsonify(
        {
            "count": len(orders),
            "data": [
                {
                    "id": o.id,
                    "product_id": o.product_id,
                    "quantity": o.quantity,
                    "amount": o.amount,
                    "status": o.status,
                }
                for o in orders
            ],
        }
    )


@bp.route("/create", methods=["POST"])
def create_order():
    data = request.get_json()
    product = db.session.get(Product, data["product_id"])
    if not product or product.stock < data["quantity"]:
        return jsonify({"error": "insufficient stock"}), 400

    order = Order(
        product_id=product.id,
        quantity=data["quantity"],
        amount=product.price * data["quantity"],
    )
    product.stock -= data["quantity"]
    db.session.add(order)
    db.session.commit()
    return jsonify({"id": order.id, "status": order.status}), 201


@bp.route("/export")
def export_orders():
    """
    Export all orders as CSV.
    BUG: db.engine.connect() borrows a raw connection from the pool,
    but conn is never closed.  Flask-SQLAlchemy's teardown_appcontext
    only calls db.session.remove() ― it does NOT touch raw connections
    obtained via engine.connect().  Each call to this endpoint leaks
    one connection permanently.
    """
    conn = db.engine.connect()
    rows = conn.execute(
        text("SELECT id, product_id, quantity, amount, status FROM orders")
    ).fetchall()
    csv_lines = ["id,product_id,quantity,amount,status"]
    for row in rows:
        csv_lines.append(f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}")
    return "\n".join(csv_lines), 200, {"Content-Type": "text/csv"}
