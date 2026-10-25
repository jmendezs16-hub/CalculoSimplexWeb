"""Helpers comunes para autenticación, empresa activa y validación de API."""

from flask_jwt_extended import get_jwt_identity

from app.auth.responses import error_response
from app.extensions import db
from app.models import Empresa


def usuario_id_actual():
    """Obtiene el ID entero guardado en el token JWT actual."""

    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def empresa_activa(usuario_id):
    """Devuelve la primera empresa activa del usuario, ordenada por ID."""

    return (
        db.session.query(Empresa)
        .filter_by(usuario_id=usuario_id, activa=True)
        .order_by(Empresa.id)
        .first()
    )


def empresa_requerida(usuario_id):
    """Devuelve (empresa, error); centraliza respuestas de token y perfil."""

    if usuario_id is None:
        return None, error_response("token_invalido", "El token no es válido.", 401)
    empresa = empresa_activa(usuario_id)
    if empresa is None:
        return None, error_response(
            "empresa_no_encontrada",
            "El usuario no tiene una empresa activa configurada.",
            404,
        )
    return empresa, None
