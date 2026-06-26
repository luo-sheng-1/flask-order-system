from app import create_app, db
from app.models import OrderItem, Product

app = create_app()

with app.app_context():
    db.create_all()
    if not Product.query.first():
        db.session.add_all(
            [
                Product(name="无线蓝牙耳机", sku="BT-001", price=299.0, cost=180.0, stock=150, category="electronics"),
                Product(name="机械键盘 87键", sku="KB-087", price=599.0, cost=350.0, stock=80, category="electronics"),
                Product(name="显示器支架", sku="DS-001", price=199.0, cost=90.0, stock=200, category="office"),
                Product(name="人体工学椅", sku="CH-001", price=2999.0, cost=1800.0, stock=30, category="office"),
                Product(name="USB-C 扩展坞", sku="UD-001", price=399.0, cost=220.0, stock=120, category="electronics"),
                Product(name="笔记本散热支架", sku="LS-001", price=129.0, cost=60.0, stock=90, category="electronics"),
                Product(name="无线鼠标", sku="MS-001", price=149.0, cost=70.0, stock=200, category="electronics"),
                Product(name="桌面理线器", sku="CM-001", price=49.0, cost=20.0, stock=500, category="office"),
            ]
        )
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
