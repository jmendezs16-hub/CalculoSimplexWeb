from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.auth.responses import error_response
from app.extensions import db
from app.models import (
    Escenario,
    Iteracion as IteracionDB,
    Recomendacion,
    Resultado,
    ResultadoRecurso,
    ResultadoVariable,
)
from app.services.modelo import ModeloEscenarioInvalido, armar_modelo
from app.services.recomendaciones import generar_recomendaciones
from app.services.simplex import Iteracion as IteracionSimplex
from app.services.simplex import ResultadoSimplex, resolver

api = Blueprint("api", __name__, url_prefix="/api")


@api.get("/health")
def health():
    """Comprueba que la API está disponible.
    ---
    tags: [Sistema]
    responses:
      200:
        description: API disponible
        examples:
          application/json: {ok: true}
    """
    return jsonify({"ok": True})


class _ErrorEndpoint(Exception):
    """Error esperado de autorización o existencia que se traduce a JSON."""

    def __init__(self, codigo: str, mensaje: str, estado_http: int):
        super().__init__(mensaje)
        self.codigo = codigo
        self.estado_http = estado_http


def _a_fraction(valor) -> Fraction:
    if isinstance(valor, Fraction):
        return valor
    return Fraction(str(valor))


def _a_decimal(valor: Fraction, escala: int) -> Decimal:
    """Redondea solo al guardar en las columnas DECIMAL de la base de datos."""

    valor = _a_fraction(valor)
    precision = max(
        28,
        len(str(abs(valor.numerator))) + escala + 8,
        len(str(valor.denominator)) + escala + 8,
    )
    quantum = Decimal(1).scaleb(-escala)
    with localcontext() as contexto:
        contexto.prec = precision
        return (Decimal(valor.numerator) / Decimal(valor.denominator)).quantize(
            quantum, rounding=ROUND_HALF_UP
        )


def _tabla_a_json(tabla: IteracionSimplex) -> dict:
    """Convierte el tableau exacto en JSON sin perder fracciones."""

    pivote = None
    if tabla.pivote is not None:
        pivote = {
            "fila": tabla.pivote[0],
            "columna": tabla.pivote[1],
            "valor": None
            if tabla.elemento_pivote is None
            else str(tabla.elemento_pivote),
        }

    return {
        "fase": tabla.fase,
        "base": list(tabla.base),
        "columnas": list(tabla.columnas),
        "filas": [[str(valor) for valor in fila] for fila in tabla.filas],
        "pivote": pivote,
        "entra": tabla.entra,
        "sale": tabla.sale,
        "elemento_pivote": None
        if tabla.elemento_pivote is None
        else str(tabla.elemento_pivote),
        "costos_reducidos": {
            nombre: str(valor) for nombre, valor in tabla.costos_reducidos.items()
        },
        "valor_objetivo": str(tabla.valor_objetivo),
        "accion": tabla.accion,
        "transformacion": [
            [str(valor) for valor in fila] for fila in tabla.transformacion
        ],
    }


def _explicacion_tabla(tabla: IteracionSimplex) -> str:
    if tabla.accion == "retirar_artificial_de_la_base":
        return "Se pivotea una variable original para retirar una artificial de la base."
    if tabla.accion == "eliminar_restriccion_redundante":
        return "Se elimina una restricción redundante de la fase 1."
    if tabla.entra and tabla.sale:
        return f"Entra {tabla.entra} y sale {tabla.sale} ({tabla.fase})."
    if tabla.entra:
        return f"Entra {tabla.entra}; no existe variable saliente, por lo que el problema no está acotado."
    return f"Tableau terminal de {tabla.fase}."


@api.post("/escenarios/<int:escenario_id>/resolver")
@jwt_required()
def resolver_escenario(escenario_id: int):
    """Resuelve un escenario y reemplaza su resultado dentro de una transacción.
    ---
    tags: [Escenarios]
    security: [{Bearer: []}]
    parameters:
      - in: path
        name: escenario_id
        type: integer
        required: true
        description: Identificador del escenario propio
    responses:
      201:
        description: Resultado calculado
        schema:
          type: object
          properties:
            resultado_id: {type: integer}
      404: {description: Escenario no encontrado o ajeno}
      422: {description: Escenario inválido}
    """

    try:
        usuario_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return error_response("token_invalido", "El token no es válido.", 401)

    try:
        with db.session.begin():
            # Carga y autoriza dentro de la misma transacción que escribirá el
            # resultado, ocultando también si el escenario ajeno existe.
            escenario = db.session.get(Escenario, escenario_id)
            if escenario is None or escenario.empresa.usuario_id != usuario_id:
                raise _ErrorEndpoint(
                    "escenario_no_encontrado",
                    "El escenario no existe o no pertenece a tu usuario.",
                    404,
                )

            modelo = armar_modelo(escenario)
            solucion: ResultadoSimplex = resolver(
                modelo.c,
                modelo.A,
                modelo.b,
                modelo.tipos,
                objetivo=escenario.objetivo,
            )

            nombres_productos = {
                f"x{indice + 1}": producto.nombre
                for indice, producto in enumerate(modelo.productos)
            }
            recomendaciones = generar_recomendaciones(
                solucion,
                [recurso.nombre for recurso in modelo.recursos],
                [recurso.unidad for recurso in modelo.recursos],
                nombres_productos=nombres_productos,
            )

            # El esquema impone un resultado único por escenario: al resolverlo
            # otra vez, reemplaza todos sus detalles sin salir de la transacción.
            resultado_db = escenario.resultado
            es_nuevo = resultado_db is None
            if es_nuevo:
                resultado_db = Resultado(escenario=escenario)
            else:
                resultado_db.resultado_variables.clear()
                resultado_db.resultado_recursos.clear()
                resultado_db.recomendaciones.clear()
                resultado_db.iteraciones.clear()
                # Borra los hijos existentes dentro de la transacción antes
                # de insertar de nuevo las claves compuestas del mismo solve.
                db.session.flush()

            resultado_db.estado = solucion.estado
            resultado_db.valor_z = (
                None if solucion.z is None else _a_decimal(solucion.z, 4)
            )
            resultado_db.iteraciones_n = sum(
                tabla.pivote is not None for tabla in solucion.iteraciones
            )
            db.session.add(resultado_db)
            db.session.flush()

            # Solo hay valores de producción interpretables cuando simplex
            # halló un óptimo (incluidos múltiples o degenerados).
            if solucion.z is not None:
                for indice, producto in enumerate(modelo.productos):
                    variable = f"x{indice + 1}"
                    valor = solucion.valores.get(variable, Fraction(0))
                    aporte = _a_fraction(modelo.c[indice]) * valor
                    resultado_db.resultado_variables.append(
                        ResultadoVariable(
                            producto_id=producto.id,
                            valor=_a_decimal(valor, 4),
                            aporte=_a_decimal(aporte, 4),
                        )
                    )

                # Las filas de recursos son las primeras filas del modelo; las
                # restricciones adicionales son cotas de los productos.
                for indice, recurso in enumerate(modelo.recursos):
                    usado = sum(
                        (
                            _a_fraction(modelo.A[indice][indice_producto])
                            * solucion.valores.get(f"x{indice_producto + 1}", Fraction(0))
                            for indice_producto in range(len(modelo.productos))
                        ),
                        Fraction(0),
                    )
                    identificador = f"r{indice + 1}"
                    resultado_db.resultado_recursos.append(
                        ResultadoRecurso(
                            recurso_id=recurso.id,
                            usado=_a_decimal(usado, 4),
                            holgura=_a_decimal(
                                solucion.holguras.get(identificador, Fraction(0)), 4
                            ),
                            precio_sombra=_a_decimal(
                                solucion.precios_sombra.get(identificador, Fraction(0)), 6
                            ),
                        )
                    )

                for orden, recomendacion in enumerate(recomendaciones, start=1):
                    resultado_db.recomendaciones.append(
                        Recomendacion(
                            orden=orden,
                            titulo=str(recomendacion["titulo"])[:200],
                            detalle=str(recomendacion["detalle"])[:500],
                            destacada=bool(recomendacion.get("destacada", False)),
                        )
                    )

            for tabla in solucion.iteraciones:
                resultado_db.iteraciones.append(
                    IteracionDB(
                        numero=tabla.numero,
                        tabla_json=_tabla_a_json(tabla),
                        entra=tabla.entra,
                        sale=tabla.sale,
                        explicacion=_explicacion_tabla(tabla),
                    )
                )

            db.session.flush()
            resultado_id = resultado_db.id

        return jsonify({"resultado_id": resultado_id}), 200 if not es_nuevo else 201

    except _ErrorEndpoint as error:
        db.session.rollback()
        return error_response(error.codigo, str(error), error.estado_http)
    except ModeloEscenarioInvalido as error:
        db.session.rollback()
        return error_response("modelo_invalido", str(error), 422)
    except ValueError as error:
        db.session.rollback()
        return error_response("modelo_invalido", str(error), 422)
    except Exception:
        # Cubre errores de cálculo, inserción y commit; ninguna escritura parcial
        # debe sobrevivir si falla cualquiera de las tablas relacionadas.
        db.session.rollback()
        current_app.logger.exception(
            "No se pudo resolver el escenario %s", escenario_id
        )
        return error_response(
            "error_al_resolver",
            "No se pudo resolver el escenario. La transacción fue revertida.",
            500,
        )
