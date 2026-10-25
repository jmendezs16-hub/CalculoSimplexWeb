from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash

from app.auth.responses import error_response
from app.extensions import db
from app.models import Empresa, Usuario


bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    """Valida credenciales y devuelve un token de acceso.
    ---
    tags: [Autenticación]
    consumes: [application/json]
    parameters:
      - in: body
        name: credenciales
        required: true
        schema:
          type: object
          required: [correo, password]
          properties:
            correo: {type: string, example: demo@grupo2.com}
            password: {type: string, example: demo1234}
    responses:
      200: {description: Token y usuario autenticado}
      400: {description: Datos inválidos}
      401: {description: Credenciales incorrectas}
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response(
            "solicitud_invalida",
            "El cuerpo de la solicitud debe ser JSON válido.",
            400,
        )

    correo = data.get("correo")
    password = data.get("password")
    if (
        not isinstance(correo, str)
        or not correo.strip()
        or not isinstance(password, str)
        or not password
    ):
        return error_response(
            "datos_requeridos",
            "Debes enviar correo y password.",
            400,
        )

    usuario = Usuario.query.filter_by(correo=correo.strip()).first()
    if usuario is None or not check_password_hash(usuario.password_hash, password):
        return error_response(
            "credenciales_invalidas",
            "El correo o la contraseña son incorrectos.",
            401,
        )

    token = create_access_token(identity=str(usuario.id))
    return jsonify({"token": token, "usuario": usuario.to_dict()})


@bp.get("/me")
@jwt_required()
def me():
    """Devuelve el usuario autenticado y su empresa activa.
    ---
    tags: [Autenticación]
    security: [{Bearer: []}]
    responses:
      200: {description: Usuario y empresa activa}
      401: {description: "Token requerido, inválido o expirado"}
    """
    try:
        usuario_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return error_response("token_invalido", "El token no es válido.", 401)

    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None:
        return error_response(
            "usuario_no_encontrado",
            "El usuario asociado al token ya no existe.",
            401,
        )

    empresa = (
        Empresa.query.filter_by(usuario_id=usuario.id, activa=True)
        .order_by(Empresa.id)
        .first()
    )
    return jsonify(
        {
            "usuario": usuario.to_dict(),
            "empresa_activa": empresa.to_dict() if empresa else None,
        }
    )
