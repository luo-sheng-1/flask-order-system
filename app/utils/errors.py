from flask import jsonify


def register_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "bad request"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "internal server error"}), 500
