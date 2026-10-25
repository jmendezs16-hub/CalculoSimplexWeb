"""Esquemas Marshmallow para validar las entradas de la API."""

from decimal import Decimal

from marshmallow import RAISE, Schema, ValidationError, fields, validate, validates_schema


class DecimalNoNegativo(fields.Decimal):
    """Campo decimal de hasta cuatro posiciones que acepta números JSON."""

    def __init__(self, **kwargs):
        kwargs.setdefault("as_string", True)
        kwargs.setdefault("places", 4)
        kwargs.setdefault("allow_nan", False)
        kwargs.setdefault("validate", validate.Range(min=Decimal("0")))
        super().__init__(**kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        # Decimal de Marshmallow está pensado para texto; JSON también envía
        # cantidades como int/float, por lo que se convierten desde su texto.
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = str(value)
        return super()._deserialize(value, attr, data, **kwargs)


class EntradaEstrica(Schema):
    """Base que rechaza claves no documentadas en las peticiones."""

    class Meta:
        unknown = RAISE


class EmpresaUpdateSchema(EntradaEstrica):
    nombre = fields.String(validate=validate.Length(min=1, max=150))
    rubro = fields.String(allow_none=True, validate=validate.Length(max=100))
    moneda = fields.String(validate=validate.Length(min=1, max=10))
    periodo = fields.String(
        validate=validate.OneOf(["diario", "semanal", "mensual", "anual"])
    )


class ProductoSchema(EntradaEstrica):
    codigo = fields.String(required=True, validate=validate.Length(min=1, max=20))
    nombre = fields.String(required=True, validate=validate.Length(min=1, max=150))
    beneficio_unitario = DecimalNoNegativo(required=True)
    activo = fields.Boolean(load_default=True)


class ProductoUpdateSchema(EntradaEstrica):
    codigo = fields.String(validate=validate.Length(min=1, max=20))
    nombre = fields.String(validate=validate.Length(min=1, max=150))
    beneficio_unitario = DecimalNoNegativo()
    activo = fields.Boolean()


class RecursoSchema(EntradaEstrica):
    nombre = fields.String(required=True, validate=validate.Length(min=1, max=150))
    unidad = fields.String(required=True, validate=validate.Length(min=1, max=30))
    disponible = DecimalNoNegativo(required=True)


class RecursoUpdateSchema(EntradaEstrica):
    nombre = fields.String(validate=validate.Length(min=1, max=150))
    unidad = fields.String(validate=validate.Length(min=1, max=30))
    disponible = DecimalNoNegativo()


class ConsumoSchema(EntradaEstrica):
    producto_id = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))
    recurso_id = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))
    cantidad = DecimalNoNegativo(required=True)


class MatrizConsumosSchema(EntradaEstrica):
    consumos = fields.List(fields.Nested(ConsumoSchema), required=True)


class EscenarioProductoSchema(EntradaEstrica):
    producto_id = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))
    incluido = fields.Boolean(load_default=True)
    produccion_min = DecimalNoNegativo(allow_none=True, load_default=None)
    demanda_max = DecimalNoNegativo(allow_none=True, load_default=None)


class EscenarioRecursoSchema(EntradaEstrica):
    recurso_id = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))
    disponible = DecimalNoNegativo(required=True)


class EscenarioSchema(EntradaEstrica):
    nombre = fields.String(required=True, validate=validate.Length(min=1, max=150))
    periodo = fields.String(allow_none=True, validate=validate.Length(max=60))
    objetivo = fields.String(
        load_default="max", validate=validate.OneOf(["max", "min"])
    )
    productos = fields.List(fields.Nested(EscenarioProductoSchema), required=True)
    recursos = fields.List(fields.Nested(EscenarioRecursoSchema), load_default=list)

    @validates_schema
    def validar_limites_de_producto(self, data, **kwargs):
        errores = {}
        for indice, producto in enumerate(data.get("productos", [])):
            minimo = producto.get("produccion_min")
            maximo = producto.get("demanda_max")
            if minimo is not None and maximo is not None and minimo > maximo:
                errores.setdefault("productos", {})[indice] = {
                    "produccion_min": [
                        "No puede ser mayor que demanda_max."
                    ]
                }
        if errores:
            raise ValidationError(errores)


def cargar_esquema(esquema, data):
    """Carga un JSON y devuelve (datos, error) con un mensaje legible."""

    try:
        return esquema.load(data), None
    except ValidationError as error:
        return None, error.messages
