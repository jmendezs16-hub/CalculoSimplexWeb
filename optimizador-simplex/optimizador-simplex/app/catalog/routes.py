"""Endpoints protegidos para empresa, productos, recursos y consumos."""

from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from app.api_utils import empresa_requerida, usuario_id_actual
from app.auth.responses import error_response
from app.extensions import db
from app.models import Consumo, Producto, Recurso, ResultadoRecurso, ResultadoVariable
from app.schemas import (
    EmpresaUpdateSchema,
    MatrizConsumosSchema,
    ProductoSchema,
    ProductoUpdateSchema,
    RecursoSchema,
    RecursoUpdateSchema,
    cargar_esquema,
)


bp = Blueprint("catalogo", __name__, url_prefix="/api")


def _entrada(esquema, aceptar_lista=False):
    cuerpo = request.get_json(silent=True)
    if aceptar_lista and isinstance(cuerpo, list):
        cuerpo = {"consumos": cuerpo}
    if not isinstance(cuerpo, dict):
        return None, {"_schema": ["El cuerpo debe ser un objeto JSON válido."]}
    return cargar_esquema(esquema, cuerpo)


def _empresa_usuario():
    return empresa_requerida(usuario_id_actual())


def _error_integridad(mensaje):
    db.session.rollback()
    return error_response("conflicto_datos", mensaje, 409)


@bp.get("/empresa")
@jwt_required()
def obtener_empresa():
    """Devuelve el perfil de empresa activa del usuario autenticado.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    responses:
      200: {description: Perfil de empresa}
      401: {description: Token inválido o ausente}
      404: {description: No hay empresa activa}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    return jsonify({"empresa": empresa.to_dict()})


@bp.put("/empresa")
@jwt_required()
def actualizar_empresa():
    """Actualiza el perfil de la empresa activa.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    responses:
      200: {description: Perfil actualizado}
      400: {description: Datos inválidos}
      404: {description: Empresa activa no encontrada}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    datos, errores = _entrada(EmpresaUpdateSchema())
    if errores:
        return error_response("datos_invalidos", str(errores), 400)
    if not datos:
        return error_response(
            "datos_requeridos", "Envía al menos un campo para actualizar.", 400
        )
    if any(
        campo in datos and isinstance(datos[campo], str) and not datos[campo].strip()
        for campo in ("nombre", "moneda", "periodo")
    ):
        return error_response("datos_invalidos", "Los campos no pueden estar vacíos.", 400)
    for campo, valor in datos.items():
        setattr(empresa, campo, valor.strip() if isinstance(valor, str) else valor)
    db.session.commit()
    return jsonify({"empresa": empresa.to_dict()})


@bp.get("/productos")
@jwt_required()
def listar_productos():
    """Lista productos de la empresa activa.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    responses:
      200: {description: Productos del catálogo}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    productos = (
        Producto.query.filter_by(empresa_id=empresa.id).order_by(Producto.id).all()
    )
    return jsonify({"productos": [producto.to_dict() for producto in productos]})


@bp.post("/productos")
@jwt_required()
def crear_producto():
    """Crea un producto en la empresa activa.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    responses:
      201: {description: Producto creado}
      400: {description: Datos inválidos}
      409: {description: Código de producto duplicado}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    datos, errores = _entrada(ProductoSchema())
    if errores:
        return error_response("datos_invalidos", str(errores), 400)
    datos["codigo"] = datos["codigo"].strip()
    datos["nombre"] = datos["nombre"].strip()
    if not datos["codigo"] or not datos["nombre"]:
        return error_response("datos_invalidos", "Código y nombre son obligatorios.", 400)
    producto = Producto(empresa_id=empresa.id, **datos)
    db.session.add(producto)
    try:
        db.session.commit()
    except IntegrityError:
        return _error_integridad("Ya existe un producto con ese código en la empresa.")
    return jsonify({"producto": producto.to_dict()}), 201


@bp.put("/productos/<int:producto_id>")
@jwt_required()
def actualizar_producto(producto_id):
    """Actualiza un producto propio.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    parameters:
      - in: path
        name: producto_id
        type: integer
        required: true
    responses:
      200: {description: Producto actualizado}
      404: {description: Producto no encontrado}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    producto = Producto.query.filter_by(id=producto_id, empresa_id=empresa.id).first()
    if producto is None:
        return error_response("producto_no_encontrado", "Producto no encontrado.", 404)
    datos, errores = _entrada(ProductoUpdateSchema())
    if errores:
        return error_response("datos_invalidos", str(errores), 400)
    if not datos:
        return error_response("datos_requeridos", "Envía campos para actualizar.", 400)
    if any(
        campo in datos and not datos[campo].strip()
        for campo in ("codigo", "nombre")
    ):
        return error_response("datos_invalidos", "Código y nombre no pueden estar vacíos.", 400)
    for campo, valor in datos.items():
        setattr(producto, campo, valor.strip() if isinstance(valor, str) else valor)
    try:
        db.session.commit()
    except IntegrityError:
        return _error_integridad("Ya existe un producto con ese código en la empresa.")
    return jsonify({"producto": producto.to_dict()})


@bp.delete("/productos/<int:producto_id>")
@jwt_required()
def eliminar_producto(producto_id):
    """Elimina un producto que no esté guardado en resultados.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    parameters:
      - in: path
        name: producto_id
        type: integer
        required: true
    responses:
      200: {description: Producto eliminado}
      404: {description: Producto no encontrado}
      409: {description: Producto usado en resultados}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    producto = Producto.query.filter_by(id=producto_id, empresa_id=empresa.id).first()
    if producto is None:
        return error_response("producto_no_encontrado", "Producto no encontrado.", 404)
    referenciado = ResultadoVariable.query.filter_by(producto_id=producto.id).first()
    if referenciado:
        return error_response(
            "producto_en_uso",
            "No puedes eliminar un producto que aparece en resultados guardados.",
            409,
        )
    db.session.delete(producto)
    try:
        db.session.commit()
    except IntegrityError:
        return _error_integridad("No se pudo eliminar el producto porque está en uso.")
    return jsonify({"ok": True})


@bp.get("/recursos")
@jwt_required()
def listar_recursos():
    """Lista los recursos de la empresa activa.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    responses:
      200: {description: Recursos del catálogo}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    recursos = Recurso.query.filter_by(empresa_id=empresa.id).order_by(Recurso.id).all()
    return jsonify({"recursos": [recurso.to_dict() for recurso in recursos]})


@bp.post("/recursos")
@jwt_required()
def crear_recurso():
    """Crea un recurso en la empresa activa.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    responses:
      201: {description: Recurso creado}
      400: {description: Datos inválidos}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    datos, errores = _entrada(RecursoSchema())
    if errores:
        return error_response("datos_invalidos", str(errores), 400)
    datos["nombre"] = datos["nombre"].strip()
    datos["unidad"] = datos["unidad"].strip()
    if not datos["nombre"] or not datos["unidad"]:
        return error_response("datos_invalidos", "Nombre y unidad son obligatorios.", 400)
    recurso = Recurso(empresa_id=empresa.id, **datos)
    db.session.add(recurso)
    db.session.commit()
    return jsonify({"recurso": recurso.to_dict()}), 201


@bp.put("/recursos/<int:recurso_id>")
@jwt_required()
def actualizar_recurso(recurso_id):
    """Actualiza un recurso propio.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    parameters:
      - in: path
        name: recurso_id
        type: integer
        required: true
    responses:
      200: {description: Recurso actualizado}
      404: {description: Recurso no encontrado}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    recurso = Recurso.query.filter_by(id=recurso_id, empresa_id=empresa.id).first()
    if recurso is None:
        return error_response("recurso_no_encontrado", "Recurso no encontrado.", 404)
    datos, errores = _entrada(RecursoUpdateSchema())
    if errores:
        return error_response("datos_invalidos", str(errores), 400)
    if not datos:
        return error_response("datos_requeridos", "Envía campos para actualizar.", 400)
    if any(
        campo in datos and not datos[campo].strip()
        for campo in ("nombre", "unidad")
    ):
        return error_response("datos_invalidos", "Nombre y unidad no pueden estar vacíos.", 400)
    for campo, valor in datos.items():
        setattr(recurso, campo, valor.strip() if isinstance(valor, str) else valor)
    try:
        db.session.commit()
    except IntegrityError:
        return _error_integridad("No se pudo guardar el recurso por una restricción de datos.")
    return jsonify({"recurso": recurso.to_dict()})


@bp.delete("/recursos/<int:recurso_id>")
@jwt_required()
def eliminar_recurso(recurso_id):
    """Elimina un recurso que no esté guardado en resultados.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    parameters:
      - in: path
        name: recurso_id
        type: integer
        required: true
    responses:
      200: {description: Recurso eliminado}
      404: {description: Recurso no encontrado}
      409: {description: Recurso usado en resultados}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    recurso = Recurso.query.filter_by(id=recurso_id, empresa_id=empresa.id).first()
    if recurso is None:
        return error_response("recurso_no_encontrado", "Recurso no encontrado.", 404)
    if ResultadoRecurso.query.filter_by(recurso_id=recurso.id).first():
        return error_response(
            "recurso_en_uso",
            "No puedes eliminar un recurso que aparece en resultados guardados.",
            409,
        )
    db.session.delete(recurso)
    try:
        db.session.commit()
    except IntegrityError:
        return _error_integridad("No se pudo eliminar el recurso porque está en uso.")
    return jsonify({"ok": True})


@bp.get("/consumos")
@jwt_required()
def obtener_matriz_consumos():
    """Devuelve todas las combinaciones producto-recurso, incluyendo ceros.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    responses:
      200: {description: Matriz completa de consumos}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    productos = Producto.query.filter_by(empresa_id=empresa.id).order_by(Producto.id).all()
    recursos = Recurso.query.filter_by(empresa_id=empresa.id).order_by(Recurso.id).all()
    existentes = {
        (consumo.producto_id, consumo.recurso_id): consumo.cantidad
        for consumo in Consumo.query.join(Producto)
        .filter(Producto.empresa_id == empresa.id)
        .all()
    }
    filas = [
        {
            "producto_id": producto.id,
            "recurso_id": recurso.id,
            "cantidad": format(
                existentes.get((producto.id, recurso.id), Decimal("0")), "f"
            ),
        }
        for producto in productos
        for recurso in recursos
    ]
    return jsonify({"consumos": filas})


@bp.put("/consumos")
@jwt_required()
def guardar_matriz_consumos():
    """Reemplaza la matriz completa de consumos de la empresa.
    ---
    tags: [Catálogo]
    security: [{Bearer: []}]
    responses:
      200: {description: Matriz guardada}
      400: {description: Matriz incompleta o con referencias ajenas}
    """

    empresa, error = _empresa_usuario()
    if error:
        return error
    datos, errores = _entrada(MatrizConsumosSchema(), aceptar_lista=True)
    if errores:
        return error_response("datos_invalidos", str(errores), 400)
    productos = Producto.query.filter_by(empresa_id=empresa.id).all()
    recursos = Recurso.query.filter_by(empresa_id=empresa.id).all()
    productos_ids = {producto.id for producto in productos}
    recursos_ids = {recurso.id for recurso in recursos}
    pares_esperados = {
        (producto_id, recurso_id)
        for producto_id in productos_ids
        for recurso_id in recursos_ids
    }
    matriz = {}
    for fila in datos["consumos"]:
        par = (fila["producto_id"], fila["recurso_id"])
        if par[0] not in productos_ids or par[1] not in recursos_ids:
            return error_response(
                "referencia_invalida",
                "Cada consumo debe usar un producto y recurso de tu empresa.",
                400,
            )
        if par in matriz:
            return error_response("duplicado", "La matriz repite un par producto-recurso.", 400)
        matriz[par] = fila["cantidad"]
    if set(matriz) != pares_esperados:
        return error_response(
            "matriz_incompleta",
            "Envía exactamente una cantidad por cada combinación de producto y recurso.",
            400,
        )

    Consumo.query.filter(
        Consumo.producto_id.in_(productos_ids or {-1})
    ).delete(synchronize_session=False)
    db.session.add_all(
        Consumo(producto_id=producto_id, recurso_id=recurso_id, cantidad=cantidad)
        for (producto_id, recurso_id), cantidad in matriz.items()
    )
    try:
        db.session.commit()
    except IntegrityError:
        return _error_integridad("No se pudo guardar la matriz de consumos.")
    return jsonify({"consumos": datos["consumos"]})
