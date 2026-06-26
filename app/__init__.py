from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)

    from app.routes import orders, products, reports, dashboard
    from app.utils import errors

    app.register_blueprint(orders.bp)
    app.register_blueprint(products.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(dashboard.bp)
    errors.register_handlers(app)

    return app
