"""Construcción del modelo lineal almacenado en un escenario."""

from dataclasses import dataclass

from app.models import Escenario, Producto, Recurso


class ModeloEscenarioInvalido(ValueError):
    """El escenario no contiene datos suficientes o coherentes para resolver."""


@dataclass
class ModeloLineal:
    """Coeficientes del LP y entidades ORM que corresponden a sus variables."""

    c: list
    A: list[list]
    b: list
    tipos: list[str]
    productos: list[Producto]
    recursos: list[Recurso]


def armar_modelo(escenario: Escenario) -> ModeloLineal:
    """Arma c, A, b y tipos en un orden estable.

    Las primeras restricciones son los recursos (una fila por recurso, en
    orden de id). Después se agregan las producciones mínimas y demandas máximas
    de los productos incluidos. Las variables son ``x1``, ``x2``, etc., según
    el orden de id de los productos seleccionados.
    """

    empresa_id = escenario.empresa_id

    # Revisa las asociaciones antes de construir las matrices; el esquema de
    # base de datos permite referencias cruzadas entre empresas si se cargan
    # manualmente, pero un escenario no debe usar datos de otra empresa.
    asociaciones_producto = sorted(
        escenario.escenario_productos,
        key=lambda asociacion: asociacion.producto_id,
    )
    for asociacion in asociaciones_producto:
        if asociacion.producto.empresa_id != empresa_id:
            raise ModeloEscenarioInvalido(
                "El escenario contiene un producto de otra empresa."
            )

    asociaciones_incluidas = [
        asociacion
        for asociacion in asociaciones_producto
        if asociacion.incluido is not False and asociacion.producto.activo is not False
    ]
    productos = [asociacion.producto for asociacion in asociaciones_incluidas]
    if not productos:
        raise ModeloEscenarioInvalido(
            "El escenario debe incluir al menos un producto activo."
        )

    recursos = sorted(escenario.empresa.recursos, key=lambda recurso: recurso.id)
    indices_recursos = {recurso.id: indice for indice, recurso in enumerate(recursos)}

    # El valor ajustado del escenario reemplaza la disponibilidad normal de
    # cada recurso; los recursos sin ajuste conservan su disponibilidad base.
    disponibilidad_ajustada = {}
    for asociacion in escenario.escenario_recursos:
        if asociacion.recurso.empresa_id != empresa_id:
            raise ModeloEscenarioInvalido(
                "El escenario contiene un recurso de otra empresa."
            )
        disponibilidad_ajustada[asociacion.recurso_id] = asociacion.disponible

    consumos: dict[tuple[int, int], object] = {}
    for producto in productos:
        for consumo in producto.consumos:
            if consumo.recurso_id not in indices_recursos:
                raise ModeloEscenarioInvalido(
                    f"El producto {producto.nombre!r} consume un recurso que no pertenece a su empresa."
                )
            consumos[(producto.id, consumo.recurso_id)] = consumo.cantidad

    # Coeficientes de consumo por recurso; estas filas son restricciones <=.
    A: list[list] = [
        [consumos.get((producto.id, recurso.id), 0) for producto in productos]
        for recurso in recursos
    ]
    b = [
        disponibilidad_ajustada.get(recurso.id, recurso.disponible)
        for recurso in recursos
    ]
    tipos = ["<="] * len(recursos)

    # Agrega las cotas del escenario como restricciones adicionales. Cada
    # variable de producto aparece con coeficiente 1 en su propia restricción.
    for indice, asociacion in enumerate(asociaciones_incluidas):
        if asociacion.produccion_min is not None:
            fila = [0] * len(productos)
            fila[indice] = 1
            A.append(fila)
            b.append(asociacion.produccion_min)
            tipos.append(">=")
        if asociacion.demanda_max is not None:
            fila = [0] * len(productos)
            fila[indice] = 1
            A.append(fila)
            b.append(asociacion.demanda_max)
            tipos.append("<=")

    return ModeloLineal(
        c=[producto.beneficio_unitario for producto in productos],
        A=A,
        b=b,
        tipos=tipos,
        productos=productos,
        recursos=recursos,
    )

