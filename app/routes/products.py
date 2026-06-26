from flask import Blueprint, jsonify, request

from app import db
from app.models import InventoryLog, Product

bp = Blueprint("products", __name__, url_prefix="/api/products")


@bp.route("")
def list_products():
    category = request.args.get("category")
    query = db.session.query(Product).order_by(Product.name)
    if category:
        query = query.filter(Product.category == category)
    products = query.all()
    return jsonify(
        {
            "count": len(products),
            "data": [
                {
                    "id": p.id,
                    "name": p.name,
                    "sku": p.sku,
                    "price": p.price,
                    "stock": p.stock,
                    "category": p.category,
                }
                for p in products
            ],
        }
    )


@bp.route("/<int:product_id>")
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "product not found"}), 404
    return jsonify(
        {
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "price": product.price,
            "cost": product.cost,
            "stock": product.stock,
            "category": product.category,
            "created_at": product.created_at.isoformat(),
        }
    )


@bp.route("", methods=["POST"])
def create_product():
    data = request.get_json(silent=True)
    if not data or not data.get("name") or not data.get("sku"):
        return jsonify({"error": "name and sku are required"}), 400

    existing = Product.query.filter(Product.sku == data["sku"]).first()
    if existing:
        return jsonify({"error": "sku already exists"}), 409

    product = Product(
        name=data["name"].strip(),
        sku=data["sku"].strip(),
        price=float(data.get("price", 0)),
        cost=float(data.get("cost", 0)),
        stock=int(data.get("stock", 0)),
        category=data.get("category", "general"),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"id": product.id, "sku": product.sku}), 201


@bp.route("/<int:product_id>/stock", methods=["PUT"])
def adjust_stock(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "product not found"}), 404

    data = request.get_json(silent=True)
    if not data or "change" not in data:
        return jsonify({"error": "change is required"}), 400

    change = int(data["change"])
    reason = data.get("reason", "manual adjustment")

    if product.stock + change < 0:
        return jsonify({"error": "insufficient stock"}), 400

    product.stock += change
    db.session.add(InventoryLog(product_id=product.id, change_qty=change, reason=reason))
    db.session.commit()
    return jsonify({"id": product.id, "stock": product.stock})
