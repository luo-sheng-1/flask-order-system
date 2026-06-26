from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from app.services.report_service import generate_sales_report, get_daily_summary

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@bp.route("/sales")
def sales_report():
    try:
        end_str = request.args.get("end_date", date.today().isoformat())
        start_str = request.args.get("start_date", (date.today() - timedelta(days=30)).isoformat())
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except ValueError:
        return jsonify({"error": "invalid date format, use YYYY-MM-DD"}), 400

    stats = generate_sales_report(start_date, end_date)
    return jsonify(stats)


@bp.route("/daily-summary")
def daily_summary():
    summary = get_daily_summary()
    return jsonify(summary)


@bp.route("/inventory-status")
def inventory_status():
    from app import db
    from app.models import Product

    low_stock = request.args.get("low_stock_threshold", 10, type=int)
    products = Product.query.order_by(Product.stock).all()

    return jsonify(
        {
            "total_products": len(products),
            "low_stock_threshold": low_stock,
            "low_stock_items": [
                {"id": p.id, "name": p.name, "stock": p.stock, "category": p.category}
                for p in products
                if p.stock <= low_stock
            ],
            "out_of_stock": [
                {"id": p.id, "name": p.name, "category": p.category}
                for p in products
                if p.stock == 0
            ],
        }
    )
