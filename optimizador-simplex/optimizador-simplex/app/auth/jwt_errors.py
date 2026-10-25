from app.auth.responses import error_response


def register_jwt_error_handlers(jwt):
    @jwt.unauthorized_loader
    def missing_token(_reason):
        return error_response(
            "token_requerido",
            "Debes enviar un token de acceso.",
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return error_response("token_invalido", "El token no es válido.", 401)

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return error_response("token_expirado", "El token ha expirado.", 401)

    @jwt.revoked_token_loader
    def revoked_token(_jwt_header, _jwt_payload):
        return error_response("token_revocado", "El token fue revocado.", 401)

    @jwt.needs_fresh_token_loader
    def fresh_token_required(_jwt_header, _jwt_payload):
        return error_response("token_no_fresco", "Se requiere un token reciente.", 401)

    @jwt.token_verification_failed_loader
    def token_verification_failed(_jwt_header, _jwt_payload):
        return error_response("token_no_verificado", "No se pudo verificar el token.", 401)
