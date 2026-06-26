from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import text

from app import db
from app.models import InventoryLog, Order, OrderItem, Product
from app.services.order_service import batch_update_order_status

bp = Blueprint("orders", __name__, url_prefix="/api/orders")


@bp.route("")
def list_orders():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status")

    query = db.session.query(Order).order_by(Order.created_at.desc())
    if status:
        query = query.filter(Order.status == status)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "total": pagination.total,
            "page": pagination.page,
            "data": [
                {
                    "id": o.id,
                    "order_no": o.order_no,
                    "customer_name": o.customer_name,
                    "total_amount": o.total_amount,
                    "status": o.status,
                    "created_at": o.created_at.isoformat(),
                }
                for o in pagination.items
            ],
        }
    )


@bp.route("", methods=["POST"])
def create_order():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid request body"}), 400

    customer_name = data.get("customer_name", "").strip()
    if not customer_name:
        return jsonify({"error": "customer_name is required"}), 400

    items_data = data.get("items", [])
    if not items_data:
        return jsonify({"error": "items is required"}), 400

    order_no = f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{Order.query.count() + 1:06d}"

    try:
        order = Order(
            order_no=order_no,
            customer_name=customer_name,
            customer_phone=data.get("customer_phone", ""),
            remark=data.get("remark", ""),
            status="pending",
        )
        total = 0.0
        for item_data in items_data:
            product = db.session.get(Product, item_data["product_id"])
            if not product:
                db.session.rollback()
                return jsonify({"error": f"product {item_data['product_id']} not found"}), 400
            if product.stock < item_data["quantity"]:
                db.session.rollback()
                return jsonify({"error": f"insufficient stock for {product.name}"}), 400

            subtotal = product.price * item_data["quantity"]
            total += subtotal
            product.stock -= item_data["quantity"]

            order_item = OrderItem(
                product_id=product.id,
                quantity=item_data["quantity"],
                unit_price=product.price,
                subtotal=subtotal,
            )
            order.items.append(order_item)

            db.session.add(
                InventoryLog(
                    product_id=product.id,
                    change_qty=-item_data["quantity"],
                    reason=f"order {order_no}",
                )
            )

        order.total_amount = total
        db.session.add(order)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "order creation failed"}), 500

    return jsonify({"id": order.id, "order_no": order.order_no, "status": order.status}), 201


@bp.route("/<int:order_id>")
def get_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "order not found"}), 404

    return jsonify(
        {
            "id": order.id,
            "order_no": order.order_no,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "total_amount": order.total_amount,
            "status": order.status,
            "remark": order.remark,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal,
                }
                for item in order.items
            ],
        }
    )


@bp.route("/<int:order_id>/status", methods=["PUT"])
def update_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "order not found"}), 404

    new_status = request.get_json(silent=True).get("status", "").strip()
    valid_statuses = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
    if new_status not in valid_statuses:
        return jsonify({"error": f"invalid status, must be one of {valid_statuses}"}), 400

    order.status = new_status
    db.session.commit()
    return jsonify({"id": order.id, "status": order.status})


@bp.route("/batch-update-status", methods=["POST"])
def batch_update_status():
    data = request.get_json(silent=True)
    if not data or "order_ids" not in data or "status" not in data:
        return jsonify({"error": "order_ids and status are required"}), 400

    result = batch_update_order_status(data["order_ids"], data["status"])
    if result["failed"] > 0:
        return jsonify(result), 207
    return jsonify(result), 200


@bp.route("/export")
def export_orders():
    fmt = request.args.get("format", "csv")
    status_filter = request.args.get("status")

    if fmt == "csv":
        sql = "SELECT o.order_no, o.customer_name, o.total_amount, o.status, o.created_at FROM orders o"
        params = {}
        if status_filter:
            sql += " WHERE o.status = :status"
            params["status"] = status_filter
        sql += " ORDER BY o.created_at DESC LIMIT 1000"

        conn = db.engine.connect()
        result = conn.execute(text(sql), params)
        headers = ["order_no", "customer_name", "total_amount", "status", "created_at"]
        lines = [",".join(headers)]
        for row in result:
            lines.append(f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}")
        conn.close()
        return "\n".join(lines), 200, {"Content-Type": "text/csv"}

    orders = (
        Order.query.filter(Order.status == status_filter) if status_filter else Order.query
    ).order_by(Order.created_at.desc()).limit(1000).all()

    return jsonify(
        {
            "format": "json",
            "count": len(orders),
            "data": [
                {
                    "order_no": o.order_no,
                    "customer_name": o.customer_name,
                    "total_amount": o.total_amount,
                    "status": o.status,
                    "created_at": o.created_at.isoformat(),
                }
                for o in orders
            ],
        }
    )
