from app import create_app, db
from app.models import Order, Product

app = create_app()

with app.app_context():
    db.create_all()
    if not Product.query.first():
        db.session.add_all(
            [
                Product(name="无线蓝牙耳机", price=299.0, stock=150),
                Product(name="机械键盘", price=599.0, stock=80),
                Product(name="显示器支架", price=199.0, stock=200),
            ]
        )
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
