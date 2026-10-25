"""Método simplex exacto para ejercicios de Investigación de Operaciones.

El módulo no depende de Flask ni de una base de datos. Todos los valores de
los tableaux y todos los cálculos se representan con ``fractions.Fraction``.
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any


@dataclass
class Iteracion:
    """Un tableau guardado antes de aplicar el pivote indicado.

    ``filas`` contiene una fila por restricción y una última columna ``b``
    con el lado derecho. ``pivote`` usa índices desde cero: (fila, columna).
    El objetivo y los costos reducidos se guardan aparte para que la pantalla
    de comprobación pueda presentarlos sin mezclarlos con las restricciones.
    """

    numero: int
    base: list[str]
    columnas: list[str]
    filas: list[list[Fraction]]
    entra: str | None
    sale: str | None
    pivote: tuple[int, int] | None
    fase: str = "simplex"
    elemento_pivote: Fraction | None = None
    costos_reducidos: dict[str, Fraction] = field(default_factory=dict)
    valor_objetivo: Fraction = Fraction(0)
    accion: str | None = None
    # T = B^-1 S, donde S conserva la normalización de las restricciones.
    # Se necesita para calcular sensibilidad del lado derecho desde el tableau.
    transformacion: list[list[Fraction]] = field(default_factory=list)


@dataclass
class ResultadoSimplex:
    """Resultado exacto del algoritmo y la secuencia completa de tableaux."""

    estado: str  # optimo | infactible | no_acotado | multiple | degenerado
    z: Fraction | None
    valores: dict[str, Fraction]
    holguras: dict[str, Fraction]
    precios_sombra: dict[str, Fraction]
    iteraciones: list[Iteracion] = field(default_factory=list)
    # Si coinciden varios diagnósticos, ``estado`` prioriza multiple sobre
    # degenerado. Esta lista permite mostrar todos los que se detectaron.
    diagnosticos: list[str] = field(default_factory=list)
    # Convierte el objetivo interno max(Z) o max(-Z) al objetivo del usuario.
    escala_objetivo: Fraction = Fraction(1)


def _a_fraction(valor: Any) -> Fraction:
    """Convierte números o cadenas decimales sin introducir redondeo binario."""

    if isinstance(valor, Fraction):
        return valor
    if isinstance(valor, bool):
        return Fraction(int(valor))
    # str(float) conserva la representación decimal que escribió el usuario,
    # en lugar de capturar la aproximación binaria interna del float.
    return Fraction(str(valor).strip())


def _capturar(
    historial: list[Iteracion],
    base: list[int],
    columnas: list[str],
    filas: list[list[Fraction]],
    costos: list[Fraction],
    transformacion: list[list[Fraction]],
    fase: str,
    entra: int | None = None,
    sale_fila: int | None = None,
    elemento: Fraction | None = None,
    accion: str | None = None,
) -> None:
    """Copia el estado actual para que las iteraciones no se muten después."""

    reducidos, valor_objetivo = _costos_reducidos(costos, base, filas, len(columnas))
    posicion = None if entra is None or sale_fila is None else (sale_fila, entra)
    historial.append(
        Iteracion(
            numero=len(historial) + 1,
            base=[columnas[indice] for indice in base],
            columnas=[*columnas, "b"],
            filas=[list(fila) for fila in filas],
            entra=None if entra is None else columnas[entra],
            sale=None if sale_fila is None else columnas[base[sale_fila]],
            pivote=posicion,
            fase=fase,
            elemento_pivote=elemento,
            costos_reducidos={
                columnas[indice]: reducidos[indice]
                for indice in range(len(columnas))
            },
            valor_objetivo=valor_objetivo,
            accion=accion,
            transformacion=[list(fila) for fila in transformacion],
        )
    )


def _costos_reducidos(
    costos: list[Fraction],
    base: list[int],
    filas: list[list[Fraction]],
    cantidad_columnas: int,
) -> tuple[list[Fraction], Fraction]:
    """Calcula ``c - c_B B^-1 A`` y el valor actual de la función objetivo."""

    costo_base = [costos[indice] for indice in base]
    reducidos: list[Fraction] = []
    for columna in range(cantidad_columnas):
        contribucion = sum(
            (costo_base[fila] * filas[fila][columna] for fila in range(len(filas))),
            Fraction(0),
        )
        reducidos.append(costos[columna] - contribucion)
    valor = sum(
        (costo_base[fila] * filas[fila][-1] for fila in range(len(filas))),
        Fraction(0),
    )
    return reducidos, valor


def _pivotar(
    filas: list[list[Fraction]],
    transformacion: list[list[Fraction]],
    base: list[int],
    fila_pivote: int,
    columna_pivote: int,
) -> Fraction:
    """Aplica Gauss-Jordan al tableau y a la transformación de restricciones."""

    elemento = filas[fila_pivote][columna_pivote]
    # Normaliza la fila pivote para que la variable que entra tenga coeficiente 1.
    filas[fila_pivote] = [valor / elemento for valor in filas[fila_pivote]]
    transformacion[fila_pivote] = [
        valor / elemento for valor in transformacion[fila_pivote]
    ]

    # Elimina la columna pivote de todas las otras filas.
    for indice_fila, fila in enumerate(filas):
        if indice_fila == fila_pivote:
            continue
        factor = fila[columna_pivote]
        if factor == 0:
            continue
        filas[indice_fila] = [
            valor - factor * pivote
            for valor, pivote in zip(fila, filas[fila_pivote])
        ]
        transformacion[indice_fila] = [
            valor - factor * pivote
            for valor, pivote in zip(
                transformacion[indice_fila], transformacion[fila_pivote]
            )
        ]

    # La base queda actualizada después de transformar todas las filas.
    base[fila_pivote] = columna_pivote
    return elemento


def _simplex_fase(
    historial: list[Iteracion],
    columnas: list[str],
    filas: list[list[Fraction]],
    transformacion: list[list[Fraction]],
    base: list[int],
    costos: list[Fraction],
    fase: str,
) -> tuple[str, list[Fraction], Fraction, bool]:
    """Ejecuta una fase de maximización usando la regla de Bland."""

    hubo_empate = False
    while True:
        # Un RHS básico cero también cuenta como degeneración, aunque después
        # esa variable salga de la base y el tableau final ya no tenga ceros.
        if any(fila[-1] == 0 for fila in filas):
            hubo_empate = True
        reducidos, valor_objetivo = _costos_reducidos(
            costos, base, filas, len(columnas)
        )
        basicas = set(base)

        # Bland: entre todos los costos reducidos positivos entra la columna
        # con el índice más pequeño. En fase 1 también se consideran las
        # artificiales no básicas, según su costo reducido.
        candidatos = [
            indice
            for indice in range(len(columnas))
            if indice not in basicas
            and reducidos[indice] > 0
        ]
        if not candidatos:
            _capturar(
                historial,
                base,
                columnas,
                filas,
                costos,
                transformacion,
                fase,
            )
            return "optimo", reducidos, valor_objetivo, hubo_empate

        columna_entra = min(candidatos)

        # Solo filas con coeficiente positivo limitan cuánto puede aumentar
        # la variable que entra. Si no hay ninguna, el objetivo no está acotado.
        razones: list[tuple[Fraction, int]] = [
            (filas[indice_fila][-1] / filas[indice_fila][columna_entra], indice_fila)
            for indice_fila in range(len(filas))
            if filas[indice_fila][columna_entra] > 0
        ]
        if not razones:
            _capturar(
                historial,
                base,
                columnas,
                filas,
                costos,
                transformacion,
                fase,
                entra=columna_entra,
            )
            return "no_acotado", reducidos, valor_objetivo, hubo_empate

        razon_minima = min(razon for razon, _ in razones)
        empatadas = [
            indice_fila
            for razon, indice_fila in razones
            if razon == razon_minima
        ]
        if len(empatadas) > 1:
            hubo_empate = True

        # Bland también desempata la salida: sale la variable básica de menor
        # índice entre las filas empatadas.
        fila_sale = min(empatadas, key=lambda indice: base[indice])
        elemento = filas[fila_sale][columna_entra]
        _capturar(
            historial,
            base,
            columnas,
            filas,
            costos,
            transformacion,
            fase,
            entra=columna_entra,
            sale_fila=fila_sale,
            elemento=elemento,
        )
        _pivotar(filas, transformacion, base, fila_sale, columna_entra)


def _valores_variables(
    nombres_decision: list[str], columnas: list[str], filas: list[list[Fraction]], base: list[int]
) -> dict[str, Fraction]:
    """Lee las variables de decisión a partir de la solución básica actual."""

    valores = {nombre: Fraction(0) for nombre in nombres_decision}
    for indice_fila, indice_columna in enumerate(base):
        nombre = columnas[indice_columna]
        if nombre in valores:
            valores[nombre] = filas[indice_fila][-1]
    return valores


def _calcular_holguras(
    A: list[list[Fraction]],
    b: list[Fraction],
    tipos: list[str],
    valores: dict[str, Fraction],
) -> dict[str, Fraction]:
    """Devuelve el margen no negativo según el sentido de cada restricción."""

    vector = [valores[f"x{indice + 1}"] for indice in range(len(A[0]) if A else len(valores))]
    holguras: dict[str, Fraction] = {}
    for indice, fila in enumerate(A):
        actividad = sum(
            (coeficiente * variable for coeficiente, variable in zip(fila, vector)),
            Fraction(0),
        )
        if tipos[indice] == "<=":
            margen = b[indice] - actividad
        elif tipos[indice] == ">=":
            margen = actividad - b[indice]
        else:
            margen = Fraction(0)
        holguras[f"r{indice + 1}"] = margen
    return holguras


def resolver(c, A, b, tipos, objetivo="max") -> ResultadoSimplex:
    """Resuelve un problema lineal con variables de decisión no negativas.

    Args:
        c: Coeficientes de la función objetivo.
        A: Matriz de coeficientes de las restricciones.
        b: Lados derechos de las restricciones.
        tipos: Sentido de cada restricción: ``<=``, ``>=`` o ``=``.
        objetivo: ``"max"`` o ``"min"``.

    Las variables se nombran ``x1``, ``x2``, etc.; las restricciones se nombran
    ``r1``, ``r2``, etc. Para minimizar se maximiza ``-Z`` internamente y se
    devuelve ``z`` y los precios sombra con el signo del problema original.
    """

    # Convierte primero toda entrada numérica a Fraction para que no haya
    # operaciones de punto flotante en el algoritmo.
    coef_objetivo = [_a_fraction(valor) for valor in c]
    matriz = [[_a_fraction(valor) for valor in fila] for fila in A]
    lado_derecho = [_a_fraction(valor) for valor in b]
    sentidos = [str(tipo).strip() for tipo in tipos]
    modo = str(objetivo).strip().lower()

    if modo not in {"max", "min"}:
        raise ValueError("objetivo debe ser 'max' o 'min'.")
    if not coef_objetivo:
        raise ValueError("c debe contener al menos una variable.")
    if len(matriz) != len(lado_derecho) or len(matriz) != len(sentidos):
        raise ValueError("A, b y tipos deben tener la misma cantidad de restricciones.")
    if any(len(fila) != len(coef_objetivo) for fila in matriz):
        raise ValueError("Cada fila de A debe tener la misma longitud que c.")
    if any(tipo not in {"<=", ">=", "="} for tipo in sentidos):
        raise ValueError("Cada tipo debe ser '<=', '>=' o '='.")

    cantidad_variables = len(coef_objetivo)
    cantidad_restricciones = len(matriz)
    nombres_decision = [f"x{indice + 1}" for indice in range(cantidad_variables)]
    columnas = list(nombres_decision)
    base_nombres: list[str] = []
    filas_auxiliares: list[tuple[list[Fraction], Fraction, dict[str, Fraction]]] = []
    signos_originales: list[Fraction] = []
    artificiales_nombres: set[str] = set()

    # Un RHS negativo se multiplica por -1. También se invierte el sentido de
    # la desigualdad para conservar una restricción equivalente.
    for indice, (fila_original, rhs_original, tipo_original) in enumerate(
        zip(matriz, lado_derecho, sentidos), start=1
    ):
        signo = Fraction(1)
        fila = list(fila_original)
        rhs = rhs_original
        tipo = tipo_original
        if rhs < 0:
            signo = Fraction(-1)
            fila = [-valor for valor in fila]
            rhs = -rhs
            tipo = {"<=": ">=", ">=": "<=", "=": "="}[tipo]
        signos_originales.append(signo)

        auxiliares: dict[str, Fraction] = {}
        if tipo == "<=":
            nombre_holgura = f"s{indice}"
            columnas.append(nombre_holgura)
            auxiliares[nombre_holgura] = Fraction(1)
            base_nombres.append(nombre_holgura)
        elif tipo == ">=":
            nombre_exceso = f"e{indice}"
            nombre_artificial = f"a{indice}"
            columnas.extend([nombre_exceso, nombre_artificial])
            auxiliares[nombre_exceso] = Fraction(-1)
            auxiliares[nombre_artificial] = Fraction(1)
            artificiales_nombres.add(nombre_artificial)
            base_nombres.append(nombre_artificial)
        else:  # igualdad: requiere una artificial como variable básica inicial.
            nombre_artificial = f"a{indice}"
            columnas.append(nombre_artificial)
            auxiliares[nombre_artificial] = Fraction(1)
            artificiales_nombres.add(nombre_artificial)
            base_nombres.append(nombre_artificial)
        filas_auxiliares.append((fila, rhs, auxiliares))

    # Materializa las filas después de conocer el orden completo de columnas.
    columnas_auxiliares = columnas[cantidad_variables:]
    filas: list[list[Fraction]] = []
    for fila, rhs, auxiliares in filas_auxiliares:
        filas.append(
            [
                *fila,
                *(auxiliares.get(nombre, Fraction(0)) for nombre in columnas_auxiliares),
                rhs,
            ]
        )
    base = [columnas.index(nombre) for nombre in base_nombres]

    # Esta matriz registra cómo cada fila actual combina las restricciones
    # originales. Se actualiza con los mismos pivotes para obtener duales.
    transformacion = [
        [
            signos_originales[fila] if fila == columna else Fraction(0)
            for columna in range(cantidad_restricciones)
        ]
        for fila in range(cantidad_restricciones)
    ]
    artificiales = {columnas.index(nombre) for nombre in artificiales_nombres}
    historial: list[Iteracion] = []
    escala_objetivo = Fraction(1) if modo == "max" else Fraction(-1)
    costos_originales = [escala_objetivo * valor for valor in coef_objetivo]
    hubo_empate = False

    # Fase I: maximiza el negativo de la suma de artificiales. Su óptimo debe
    # ser cero para que exista una solución factible al problema original.
    if artificiales:
        costos_fase_uno = [
            Fraction(-1) if indice in artificiales else Fraction(0)
            for indice in range(len(columnas))
        ]
        estado_fase_uno, _, valor_fase_uno, empate_fase_uno = _simplex_fase(
            historial,
            columnas,
            filas,
            transformacion,
            base,
            costos_fase_uno,
            "fase_1",
        )
        hubo_empate = hubo_empate or empate_fase_uno
        if estado_fase_uno == "no_acotado":
            return ResultadoSimplex(
                "no_acotado",
                None,
                {},
                {},
                {},
                historial,
                ["no_acotado"],
                escala_objetivo,
            )
        if valor_fase_uno < 0:
            return ResultadoSimplex(
                "infactible",
                None,
                {},
                {},
                {},
                historial,
                ["infactible"],
                escala_objetivo,
            )

        # Si una artificial sigue básica con valor cero, se pivota fuera usando
        # cualquier columna original no artificial con coeficiente no nulo.
        fila_indice = 0
        while fila_indice < len(base):
            if base[fila_indice] not in artificiales:
                fila_indice += 1
                continue

            candidata = next(
                (
                    columna
                    for columna in range(len(columnas))
                    if columna not in artificiales
                    and columna not in base
                    and filas[fila_indice][columna] != 0
                ),
                None,
            )
            if candidata is not None:
                elemento = filas[fila_indice][candidata]
                _capturar(
                    historial,
                    base,
                    columnas,
                    filas,
                    costos_fase_uno,
                    transformacion,
                    "fase_1_limpieza",
                    entra=candidata,
                    sale_fila=fila_indice,
                    elemento=elemento,
                    accion="retirar_artificial_de_la_base",
                )
                _pivotar(filas, transformacion, base, fila_indice, candidata)
                fila_indice += 1
                continue

            # La fila no contiene variables originales: es redundante y se
            # elimina junto con la artificial que la mantenía en la base.
            _capturar(
                historial,
                base,
                columnas,
                filas,
                costos_fase_uno,
                transformacion,
                "fase_1_limpieza",
                accion="eliminar_restriccion_redundante",
            )
            del filas[fila_indice]
            del transformacion[fila_indice]
            del base[fila_indice]

        # Las columnas artificiales ya no se necesitan en la fase del objetivo.
        conservar = [
            indice for indice in range(len(columnas)) if indice not in artificiales
        ]
        nuevo_indice = {anterior: actual for actual, anterior in enumerate(conservar)}
        filas = [
            [*[fila[indice] for indice in conservar], fila[-1]] for fila in filas
        ]
        columnas = [columnas[indice] for indice in conservar]
        base = [nuevo_indice[indice] for indice in base]

    # Fase II (o simplex normal): convierte min en max(-Z) y usa Bland.
    costos_fase_dos = [
        costos_originales[indice] if nombre in nombres_decision else Fraction(0)
        for indice, nombre in enumerate(columnas)
    ]
    estado_final, reducidos_finales, _, empate_fase_dos = _simplex_fase(
        historial,
        columnas,
        filas,
        transformacion,
        base,
        costos_fase_dos,
        "fase_2" if artificiales_nombres else "simplex",
    )
    hubo_empate = hubo_empate or empate_fase_dos

    # Construye la solución básica factible actual, incluso si la fase II
    # detectó que el objetivo puede crecer sin límite.
    valores = _valores_variables(nombres_decision, columnas, filas, base)
    holguras = _calcular_holguras(matriz, lado_derecho, sentidos, valores)

    if estado_final == "no_acotado":
        return ResultadoSimplex(
            "no_acotado",
            None,
            valores,
            holguras,
            {},
            historial,
            ["no_acotado"],
            escala_objetivo,
        )

    # El valor de Z se calcula con la función original para devolver el signo
    # correcto incluso cuando el problema era de minimización.
    z = sum(
        (coeficiente * valores[nombre] for coeficiente, nombre in zip(coef_objetivo, nombres_decision)),
        Fraction(0),
    )

    # El dual se obtiene de c_B multiplicado por la transformación acumulada.
    # La escala de objetivo devuelve los precios con el sentido original.
    precios_sombra: dict[str, Fraction] = {}
    for indice_restriccion in range(cantidad_restricciones):
        precio = sum(
            (
                costos_fase_dos[base[fila]] * transformacion[fila][indice_restriccion]
                for fila in range(len(base))
            ),
            Fraction(0),
        )
        precios_sombra[f"r{indice_restriccion + 1}"] = escala_objetivo * precio

    # Una variable no básica con costo reducido cero indica óptimos alternos.
    basicas_finales = set(base)
    hay_multiple = any(
        indice not in basicas_finales and reducidos_finales[indice] == 0
        for indice in range(len(columnas))
    )
    degenerado = hubo_empate or any(fila[-1] == 0 for fila in filas)
    diagnosticos = ["optimo"]
    if degenerado:
        diagnosticos.append("degenerado")
    if hay_multiple:
        diagnosticos.append("multiple")

    # Como ``estado`` solo puede contener una etiqueta, multiple tiene prioridad;
    # ``diagnosticos`` conserva también degenerado si ambas condiciones ocurren.
    if hay_multiple:
        estado = "multiple"
    elif degenerado:
        estado = "degenerado"
    else:
        estado = "optimo"

    return ResultadoSimplex(
        estado=estado,
        z=z,
        valores=valores,
        holguras=holguras,
        precios_sombra=precios_sombra,
        iteraciones=historial,
        diagnosticos=diagnosticos,
        escala_objetivo=escala_objetivo,
    )

