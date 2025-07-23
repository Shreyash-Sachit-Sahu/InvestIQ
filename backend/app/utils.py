from flask import jsonify

def error_response(message, status_code=400, errors=None):
    response = {"error": message}
    if errors:
        response["errors"] = errors
    return jsonify(response), status_code

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return error_response("Bad request.", 400)
    @app.errorhandler(401)
    def unauthorized(e):
        return error_response("Unauthorized.", 401)
    @app.errorhandler(403)
    def forbidden(e):
        return error_response("Forbidden.", 403)
    @app.errorhandler(404)
    def not_found(e):
        return error_response("Not found.", 404)
    @app.errorhandler(500)
    def internal_server_error(e):
        return error_response("Internal server error.", 500)
