from flask import Flask, current_app, request
from flasgger import Swagger

from app.config import CONFIG_BY_NAME, ProductionConfig
from app.extensions import cors, db, jwt
from app.auth.responses import error_response


def create_app(config_name="development"):
    """Create and configure a Flask application instance."""
    try:
        config_class = CONFIG_BY_NAME[config_name.lower()]
    except (AttributeError, KeyError):
        available = ", ".join(CONFIG_BY_NAME)
        raise ValueError(
            f"Configuración desconocida: {config_name!r}. Usa: {available}."
        ) from None

    app = Flask(__name__)
    app.config.from_object(config_class)

    Swagger(
        app,
        config={
            "headers": [],
            # Mantiene los recursos de Swagger separados de los estáticos de Flask.
            "static_url_path": "/flasgger_static",
            "specs": [
                {
                    "endpoint": "apispec_1",
                    "route": "/apispec_1.json",
                    "rule_filter": lambda _rule: True,
                    "model_filter": lambda _tag: True,
                }
            ],
            "swagger_ui": True,
            "specs_route": "/apidocs",
        },
        template={
            "info": {
                "title": "Optimizador Simplex API",
                "description": "API REST para catálogo, escenarios y resultados simplex.",
                "version": "1.0.0",
            },
            "securityDefinitions": {
                "Bearer": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "Escribe: Bearer <token>",
                }
            },
        },
    )

    if config_class is ProductionConfig and not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError("JWT_SECRET_KEY debe definirse en .env para producción.")

    db.init_app(app)
    jwt.init_app(app)
    from app import models as _models  # noqa: F401  # Registra los modelos en SQLAlchemy.

    from app.auth import bp as auth_bp
    from app.auth.jwt_errors import register_jwt_error_handlers

    register_jwt_error_handlers(jwt)

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
    )

    from app.routes import api
    from app.catalog import bp as catalog_bp
    from app.scenarios import bp as scenarios_bp
    from app.results import bp as results_bp

    app.register_blueprint(api)
    app.register_blueprint(auth_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(scenarios_bp)
    app.register_blueprint(results_bp)

    @app.errorhandler(404)
    def api_not_found(error):
        """Mantiene el formato JSON para rutas desconocidas de la API."""

        if request.path.startswith("/api/"):
            return error_response("ruta_no_encontrada", "La ruta solicitada no existe.", 404)
        return error.get_response()

    @app.errorhandler(405)
    def api_method_not_allowed(error):
        """Devuelve JSON cuando el método HTTP no corresponde a una ruta API."""

        if request.path.startswith("/api/"):
            return error_response(
                "metodo_no_permitido", "El método HTTP no está permitido para esta ruta.", 405
            )
        return error.get_response()

    @app.errorhandler(500)
    def api_internal_error(error):
        """Evita devolver HTML de error para fallos inesperados de la API."""

        if request.path.startswith("/api/"):
            current_app.logger.error("Error no controlado en la API: %s", error)
            return error_response(
                "error_interno", "Ocurrió un error interno al procesar la solicitud.", 500
            )
        return error.get_response()

    return app
