"""Endpoints de planificación e historial de escenarios."""

from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.api_utils import empresa_requerida, usuario_id_actual
from app.auth.responses import error_response
from app.extensions import db
from app.models import (
    Escenario,
    EscenarioProducto,
    EscenarioRecurso,
    Producto,
    Recurso,
)
from app.schemas import EscenarioSchema, cargar_esquema
from app.services.modelo import ModeloEscenarioInvalido, armar_modelo


bp = Blueprint("escenarios", __name__, url_prefix="/api")


def _escenario_propietario(escenario_id):
    """Carga un escenario solo si pertenece a una empresa del usuario."""

    usuario_id = usuario_id_actual()
    if usuario_id is None:
        return None, error_response("token_invalido", "El token no es válido.", 401)
    escenario = Escenario.query.filter_by(id=escenario_id).first()
    if escenario is None or escenario.empresa.usuario_id != usuario_id:
        return None, error_response(
            "escenario_no_encontrado",
            "El escenario no existe o no pertenece a tu usuario.",
            404,
        )
    return escenario, None


def _cuerpo_json():
    cuerpo = request.get_json(silent=True)
    if not isinstance(cuerpo, dict):
        return None, {"_schema": ["El cuerpo debe ser un objeto JSON válido."]}
    try:
        return EscenarioSchema().load(cuerpo), None
    except ValidationError as error:
        return None, error.messages


@bp.get("/escenarios")
@jwt_required()
def listar_escenarios():
    """Lista el historial de escenarios de la empresa activa.
    ---
    tags: [Escenarios]
    security: [{Bearer: []}]
    responses:
      200: {description: Historial con el último estado y valor objetivo}
      401: {description: Token requerido o inválido}
    """

    empresa, error = empresa_requerida(usuario_id_actual())
    if error:
        return error
    escenarios = (
        Escenario.query.filter_by(empresa_id=empresa.id)
        .order_by(Escenario.creado_en.desc(), Escenario.id.desc())
        .all()
    )
    historial = []
    for escenario in escenarios:
        resultado = escenario.resultado
        historial.append(
            {
                "id": escenario.id,
                "nombre": escenario.nombre,
                "periodo": escenario.periodo,
                "objetivo": escenario.objetivo,
                "creado_en": escenario.creado_en.isoformat()
                if escenario.creado_en
                else None,
                "estado": resultado.estado if resultado else None,
                "valor_z": float(resultado.valor_z) if resultado and resultado.valor_z is not None else None,
                "resultado_id": resultado.id if resultado else None,
            }
        )
    return jsonify({"escenarios": historial})


@bp.post("/escenarios")
@jwt_required()
def crear_escenario():
    """Crea el escenario con productos y disponibilidades personalizadas.
    ---
    tags: [Escenarios]
    security: [{Bearer: []}]
    consumes: [application/json]
    parameters:
      - in: body
        name: escenario
        required: true
        schema:
          type: object
          required: [nombre, productos]
          properties:
            nombre: {type: string, example: Plan de octubre}
            periodo: {type: string, example: octubre}
            objetivo: {type: string, enum: [max, min]}
            productos: {type: array, items: {type: object}}
            recursos: {type: array, items: {type: object}}
    responses:
      201: {description: Escenario creado}
      400: {description: Datos inválidos}
      401: {description: Token requerido o inválido}
    """

    empresa, error = empresa_requerida(usuario_id_actual())
    if error:
        return error
    datos, errores = _cuerpo_json()
    if errores:
        return error_response("datos_invalidos", str(errores), 400)

    catalogo_productos = {
        producto.id: producto
        for producto in Producto.query.filter_by(empresa_id=empresa.id).all()
    }
    catalogo_recursos = {
        recurso.id: recurso
        for recurso in Recurso.query.filter_by(empresa_id=empresa.id).all()
    }
    ids_productos = [fila["producto_id"] for fila in datos["productos"]]
    ids_recursos = [fila["recurso_id"] for fila in datos["recursos"]]
    if len(set(ids_productos)) != len(ids_productos):
        return error_response("duplicado", "No repitas productos en el escenario.", 400)
    if len(set(ids_recursos)) != len(ids_recursos):
        return error_response("duplicado", "No repitas recursos en el escenario.", 400)
    if not ids_productos:
        return error_response("sin_productos", "Incluye al menos un producto.", 400)
    if any(producto_id not in catalogo_productos for producto_id in ids_productos):
        return error_response(
            "referencia_invalida", "Todos los productos deben pertenecer a tu empresa.", 400
        )
    if any(recurso_id not in catalogo_recursos for recurso_id in ids_recursos):
        return error_response(
            "referencia_invalida", "Todos los recursos deben pertenecer a tu empresa.", 400
        )
    if not any(
        fila["incluido"] and catalogo_productos[fila["producto_id"]].activo
        for fila in datos["productos"]
    ):
        return error_response(
            "sin_productos_incluidos", "Incluye al menos un producto activo.", 400
        )

    escenario = Escenario(
        empresa_id=empresa.id,
        nombre=datos["nombre"].strip(),
        periodo=datos.get("periodo"),
        objetivo=datos["objetivo"],
    )
    if not escenario.nombre:
        return error_response("datos_invalidos", "El nombre es obligatorio.", 400)
    for fila in datos["productos"]:
        escenario.escenario_productos.append(
            EscenarioProducto(
                producto_id=fila["producto_id"],
                incluido=fila["incluido"],
                produccion_min=fila["produccion_min"],
                demanda_max=fila["demanda_max"],
            )
        )
    for fila in datos["recursos"]:
        escenario.escenario_recursos.append(
            EscenarioRecurso(
                recurso_id=fila["recurso_id"], disponible=fila["disponible"]
            )
        )
    db.session.add(escenario)
    db.session.commit()
    return jsonify({"escenario": escenario.to_dict()}), 201


@bp.post("/escenarios/<int:escenario_id>/validar")
@jwt_required()
def validar_escenario(escenario_id):
    """Valida estructura y mínimos de recursos sin ejecutar el simplex.
    ---
    tags: [Escenarios]
    security: [{Bearer: []}]
    parameters:
      - in: path
        name: escenario_id
        type: integer
        required: true
    responses:
      200: {description: Resultado de validación con avisos}
      404: {description: Escenario no encontrado}
    """

    escenario, error = _escenario_propietario(escenario_id)
    if error:
        return error
    avisos = []
    for asociacion in escenario.escenario_productos:
        if (
            asociacion.produccion_min is not None
            and asociacion.demanda_max is not None
            and asociacion.produccion_min > asociacion.demanda_max
        ):
            avisos.append(
                f"El mínimo de {asociacion.producto.nombre} supera su demanda máxima."
            )
    try:
        modelo = armar_modelo(escenario)
    except ModeloEscenarioInvalido as exc:
        avisos.append(str(exc))
        return jsonify({"valido": False, "avisos": avisos})

    asociaciones = {
        asociacion.producto_id: asociacion
        for asociacion in escenario.escenario_productos
    }
    for indice, recurso in enumerate(modelo.recursos):
        uso_minimo = Decimal("0")
        for indice_producto, producto in enumerate(modelo.productos):
            minimo = asociaciones[producto.id].produccion_min or Decimal("0")
            uso_minimo += Decimal(str(modelo.A[indice][indice_producto])) * minimo
        disponible = Decimal(str(modelo.b[indice]))
        if uso_minimo > disponible:
            avisos.append(
                f"El mínimo de producción requiere {uso_minimo} {recurso.unidad} "
                f"de {recurso.nombre}, pero solo hay {disponible}."
            )
    return jsonify({"valido": not avisos, "avisos": avisos})


@bp.post("/escenarios/<int:escenario_id>/duplicar")
@jwt_required()
def duplicar_escenario(escenario_id):
    """Copia la configuración de un escenario sin copiar su resultado.
    ---
    tags: [Escenarios]
    security: [{Bearer: []}]
    parameters:
      - in: path
        name: escenario_id
        type: integer
        required: true
    responses:
      201: {description: Copia creada}
      404: {description: Escenario no encontrado}
    """

    origen, error = _escenario_propietario(escenario_id)
    if error:
        return error
    cuerpo = request.get_json(silent=True) or {}
    if not isinstance(cuerpo, dict) or set(cuerpo) - {"nombre"}:
        return error_response(
            "datos_invalidos", "Solo se permite enviar un nombre opcional.", 400
        )
    nombre = cuerpo.get("nombre", f"Copia de {origen.nombre}")
    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 150:
        return error_response(
            "datos_invalidos", "El nombre debe tener entre 1 y 150 caracteres.", 400
        )
    copia = Escenario(
        empresa_id=origen.empresa_id,
        nombre=nombre.strip(),
        periodo=origen.periodo,
        objetivo=origen.objetivo,
    )
    for fila in origen.escenario_productos:
        copia.escenario_productos.append(
            EscenarioProducto(
                producto_id=fila.producto_id,
                incluido=fila.incluido,
                produccion_min=fila.produccion_min,
                demanda_max=fila.demanda_max,
            )
        )
    for fila in origen.escenario_recursos:
        copia.escenario_recursos.append(
            EscenarioRecurso(
                recurso_id=fila.recurso_id, disponible=fila.disponible
            )
        )
    db.session.add(copia)
    db.session.commit()
    return jsonify({"escenario": copia.to_dict()}), 201
