"""Recomendaciones deterministas basadas en el resultado del simplex."""

from collections.abc import Mapping, Sequence
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction

from .simplex import Iteracion, ResultadoSimplex


def _fraccion(valor) -> Fraction:
    """Normaliza valores numéricos sin usar aritmética de punto flotante."""

    if isinstance(valor, Fraction):
        return valor
    return Fraction(str(valor))


def _decimal(valor: Fraction, decimales: int = 2) -> str:
    """Convierte a decimal solo para los mensajes que verá la persona usuaria."""

    valor = _fraccion(valor)
    precision = max(
        28,
        len(str(abs(valor.numerator))) + decimales + 8,
        len(str(valor.denominator)) + decimales + 8,
    )
    quantum = Decimal(1).scaleb(-decimales)
    with localcontext() as contexto:
        contexto.prec = precision
        decimal = (Decimal(valor.numerator) / Decimal(valor.denominator)).quantize(
            quantum, rounding=ROUND_HALF_UP
        )
    texto = f"{decimal:.{decimales}f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto or "0"


def _cantidad(valor: Fraction, unidad: str) -> str:
    sufijo = f" {unidad}" if unidad else ""
    return f"{_decimal(valor)}{sufijo}"


def _precio_y_unidad(precio: Fraction, unidad: str) -> tuple[Fraction, str]:
    """Expresa los precios sombra de minutos como precio por hora."""

    normalizada = unidad.strip().lower().rstrip(".")
    if normalizada in {"min", "mins", "minuto", "minutos", "minute", "minutes"}:
        return precio * 60, "hora"
    if normalizada in {"h", "hr", "hrs", "hora", "horas", "hour", "hours"}:
        return precio, "hora"
    return precio, unidad or "unidad"


def _crear(
    tipo: str,
    titulo: str,
    detalle: str,
    destacada: bool = False,
    **datos: object,
) -> dict[str, object]:
    """Da a todas las recomendaciones una estructura sencilla y uniforme."""

    return {
        "tipo": tipo,
        "titulo": titulo,
        "detalle": detalle,
        "destacada": destacada,
        **datos,
    }


def _tabla_final(resultado: ResultadoSimplex) -> Iteracion | None:
    """Encuentra el tableau óptimo, omitiendo los snapshots de limpieza."""

    for tabla in reversed(resultado.iteraciones):
        if tabla.fase in {"simplex", "fase_2"} and tabla.entra is None:
            return tabla
    return None


def _sensibilidad_derecha(
    tabla: Iteracion,
    cantidad_recursos: int,
) -> list[tuple[Fraction | None, Fraction | None]]:
    """Calcula cuánto puede aumentar o disminuir cada RHS con la base fija.

    Si ``T = B^-1 S``, cambiar solo ``b_i`` en ``delta`` cambia los básicos a
    ``b_bar + T[:, i] * delta``. El intervalo se obtiene exigiendo que sigan
    siendo no negativos. ``None`` significa que no hay límite en ese sentido.
    """

    if len(tabla.transformacion) != len(tabla.filas):
        return []
    if any(len(fila) < cantidad_recursos for fila in tabla.transformacion):
        return []

    rangos: list[tuple[Fraction | None, Fraction | None]] = []
    for indice_recurso in range(cantidad_recursos):
        aumentos: list[Fraction] = []
        disminuciones: list[Fraction] = []
        for fila, transformada in zip(tabla.filas, tabla.transformacion):
            coeficiente = transformada[indice_recurso]
            rhs_basico = fila[-1]
            if coeficiente < 0:
                aumentos.append(rhs_basico / -coeficiente)
            elif coeficiente > 0:
                disminuciones.append(rhs_basico / coeficiente)

        aumento_maximo = min(aumentos) if aumentos else None
        disminucion_maxima = min(disminuciones) if disminuciones else None
        rangos.append((aumento_maximo, disminucion_maxima))
    return rangos


def _esquinas_vecinas(
    resultado: ResultadoSimplex,
    tabla: Iteracion,
) -> list[tuple[dict[str, Fraction], Fraction, Fraction]]:
    """Enumera esquinas adyacentes pivoteando cada variable no básica."""

    if resultado.z is None or resultado.z == 0:
        return []

    columnas = tabla.columnas[:-1] if tabla.columnas and tabla.columnas[-1] == "b" else tabla.columnas
    basicas = set(tabla.base)
    alternativas: dict[tuple[Fraction, ...], tuple[dict[str, Fraction], Fraction, Fraction]] = {}
    nombres_decision = list(resultado.valores)

    for indice_columna, nombre_columna in enumerate(columnas):
        if nombre_columna in basicas:
            continue
        costo_reducido = tabla.costos_reducidos.get(nombre_columna)
        if costo_reducido is None:
            continue

        # La prueba de razón mínima determina cuánto puede crecer la variable
        # no básica conservando la factibilidad.
        razones = [
            (fila[-1] / fila[indice_columna], indice_fila)
            for indice_fila, fila in enumerate(tabla.filas)
            if fila[indice_columna] > 0
        ]
        if not razones:
            continue
        paso = min(razon for razon, _ in razones)

        valores_candidatos = dict(resultado.valores)
        for indice_fila, variable_basica in enumerate(tabla.base):
            if variable_basica in valores_candidatos:
                valores_candidatos[variable_basica] = (
                    tabla.filas[indice_fila][-1]
                    - tabla.filas[indice_fila][indice_columna] * paso
                )
        if nombre_columna in valores_candidatos:
            valores_candidatos[nombre_columna] = paso

        # Cambiar una holgura puede cambiar la base sin moverse a otra esquina
        # del espacio de productos; esas bases repetidas no son alternativas.
        vector = tuple(valores_candidatos[nombre] for nombre in nombres_decision)
        vector_actual = tuple(resultado.valores[nombre] for nombre in nombres_decision)
        if vector == vector_actual:
            continue

        z_interno = tabla.valor_objetivo + costo_reducido * paso
        z_candidato = z_interno * resultado.escala_objetivo
        rendimiento = Fraction(1) - abs(z_candidato - resultado.z) / abs(resultado.z)
        anterior = alternativas.get(vector)
        if anterior is None or rendimiento > anterior[2]:
            alternativas[vector] = (valores_candidatos, z_candidato, rendimiento)

    return sorted(alternativas.values(), key=lambda item: item[2], reverse=True)


def generar_recomendaciones(
    resultado: ResultadoSimplex,
    nombres_recursos: Sequence[str],
    unidades_recursos: Sequence[str],
    nombres_productos: Mapping[str, str] | Sequence[str] | None = None,
) -> list[dict[str, object]]:
    """Genera recomendaciones fijas usando holguras, duales y tableaux.

    ``nombres_recursos`` y ``unidades_recursos`` siguen el orden de las
    restricciones ``r1``, ``r2``, etc. Se devuelve una lista serializable con
    ``tipo``, ``titulo``, ``detalle`` y campos numéricos expresados como texto.
    El argumento opcional ``nombres_productos`` acepta un mapeo ``x1 -> nombre``
    o una secuencia alineada con las variables de ``resultado.valores``.
    """

    if len(nombres_recursos) != len(unidades_recursos):
        raise ValueError("nombres_recursos y unidades_recursos deben tener igual longitud.")

    # No se emiten consejos de producción si el problema no tiene un óptimo.
    if resultado.z is None or resultado.estado not in {"optimo", "degenerado", "multiple"}:
        return []

    # El modelo puede llevar restricciones adicionales de producción mínima
    # y demanda máxima después de las filas de recursos. Solo se reciben los
    # nombres/unidades de estas primeras restricciones.
    ids_recursos = list(resultado.holguras)[: len(nombres_recursos)]
    if len(ids_recursos) != len(nombres_recursos):
        raise ValueError(
            "Debe indicarse un nombre y una unidad por cada recurso del resultado."
        )

    recomendaciones: list[dict[str, object]] = []
    recursos: list[dict[str, object]] = []
    for indice, identificador in enumerate(ids_recursos):
        nombre = str(nombres_recursos[indice]).strip() or identificador
        unidad = str(unidades_recursos[indice]).strip() or "unidades"
        holgura = _fraccion(resultado.holguras[identificador])
        precio = _fraccion(resultado.precios_sombra.get(identificador, Fraction(0)))
        precio_convertido, unidad_precio = _precio_y_unidad(precio, unidad)
        recursos.append(
            {
                "id": identificador,
                "nombre": nombre,
                "unidad": unidad,
                "holgura": holgura,
                "precio": precio,
                "precio_convertido": precio_convertido,
                "unidad_precio": unidad_precio,
            }
        )

    # Entre recursos agotados, el precio sombra mayor señala el cuello principal.
    vinculantes = [recurso for recurso in recursos if recurso["holgura"] == 0]
    if vinculantes:
        mayor_precio = max(recurso["precio_convertido"] for recurso in vinculantes)
        for recurso in vinculantes:
            if recurso["precio_convertido"] != mayor_precio:
                continue
            unidad_precio = recurso["unidad_precio"]
            precio_texto = _decimal(recurso["precio_convertido"])
            recomendaciones.append(
                _crear(
                    "cuello_botella",
                    "Cuello de botella",
                    f"{recurso['nombre']} limita más la producción. Cada {unidad_precio} extra aporta cerca de Q{precio_texto}.",
                    destacada=True,
                    recurso=recurso["nombre"],
                    precio_sombra=str(recurso["precio"]),
                    precio_por_hora=str(recurso["precio_convertido"])
                    if unidad_precio == "hora"
                    else None,
                )
            )

        for recurso in vinculantes:
            if recurso["precio_convertido"] >= mayor_precio:
                continue
            precio_texto = _decimal(recurso["precio_convertido"])
            recomendaciones.append(
                _crear(
                    "recurso_secundario",
                    "Recurso secundario",
                    f"{recurso['nombre']} limita menos la producción; su precio sombra es Q{precio_texto} por {recurso['unidad_precio']}.",
                    recurso=recurso["nombre"],
                    precio_sombra=str(recurso["precio"]),
                )
            )

    # Cada holgura positiva se puede reducir o reasignar a otra producción.
    sobrantes = [recurso for recurso in recursos if recurso["holgura"] > 0]
    for recurso in sobrantes:
        holgura = recurso["holgura"]
        recomendaciones.append(
            _crear(
                "recurso_sobrante",
                "Recurso sobrante",
                f"Sobran {_cantidad(holgura, recurso['unidad'])} de {recurso['nombre']}; podrías reducirlo o usarlo en otro producto.",
                recurso=recurso["nombre"],
                holgura=str(holgura),
                unidad=recurso["unidad"],
            )
        )
    if recursos and not sobrantes:
        recomendaciones.append(
            _crear("sin_sobrantes", "Sin sobrantes", "No sobra ningún recurso.")
        )

    # El intervalo mantiene la base óptima mientras las variables básicas
    # transformadas sigan siendo no negativas al cambiar cada RHS por separado.
    tabla = _tabla_final(resultado)
    if tabla is not None:
        rangos = _sensibilidad_derecha(tabla, len(recursos))
        for recurso, (aumento, disminucion) in zip(recursos, rangos):
            partes = []
            if aumento is None:
                partes.append("puede aumentar sin límite superior")
            else:
                partes.append(
                    f"puede aumentar hasta {_cantidad(aumento, recurso['unidad'])}"
                )
            if disminucion is None:
                partes.append("y disminuir sin límite inferior")
            else:
                partes.append(
                    f"y disminuir hasta {_cantidad(disminucion, recurso['unidad'])}"
                )
            detalle = (
                f"La disponibilidad de {recurso['nombre']} {', '.join(partes)} "
                "sin cambiar la base óptima (variando este recurso por separado)."
            )
            recomendaciones.append(
                _crear(
                    "sensibilidad_derecha",
                    "Rango de sensibilidad del lado derecho",
                    detalle,
                    recurso=recurso["nombre"],
                    unidad=recurso["unidad"],
                    aumento_maximo=None if aumento is None else str(aumento),
                    disminucion_maxima=None if disminucion is None else str(disminucion),
                )
            )

        # Recorre los pivotes factibles desde el óptimo y compara las esquinas
        # vecinas exactas con el valor óptimo. Se muestran las que conservan 90%.
        alternativas = [
            alternativa
            for alternativa in _esquinas_vecinas(resultado, tabla)
            if alternativa[2] >= Fraction(90, 100)
        ]
        for numero, (valores, z_alternativo, rendimiento) in enumerate(
            alternativas, start=1
        ):
            etiqueta = f"L{numero}"
            porcentaje = _decimal(rendimiento * 100)
            productos = ", ".join(
                f"{_nombre_producto(variable, nombres_productos)}={_decimal(valor)}"
                for variable, valor in valores.items()
            )
            recomendaciones.append(
                _crear(
                    "alternativa_cercana",
                    "Alternativa cercana",
                    f"La alternativa {etiqueta} rinde el {porcentaje} % del óptimo: {productos}.",
                    alternativa=etiqueta,
                    porcentaje=f"{_decimal(rendimiento * 100)}%",
                    z_alternativo=str(z_alternativo),
                    valores={variable: str(valor) for variable, valor in valores.items()},
                )
            )

    # Una variable de decisión igual a cero se presenta como producto no rentable.
    for variable, valor in resultado.valores.items():
        if valor != 0:
            continue
        nombre_producto = _nombre_producto(variable, nombres_productos)
        recomendaciones.append(
            _crear(
                "producto_no_rentable",
                "Producto no rentable",
                f"Con los precios actuales no conviene fabricar {nombre_producto}.",
                producto=nombre_producto,
                variable=variable,
            )
        )

    return recomendaciones


def _nombre_producto(
    variable: str,
    nombres_productos: Mapping[str, str] | Sequence[str] | None,
) -> str:
    """Resuelve un nombre de pantalla o usa el nombre algebraico de la variable."""

    if nombres_productos is None:
        return variable
    if isinstance(nombres_productos, Mapping):
        return str(nombres_productos.get(variable, variable))
    try:
        indice = int(variable[1:]) - 1
        if 0 <= indice < len(nombres_productos):
            return str(nombres_productos[indice])
    except (ValueError, TypeError):
        pass
    return variable

