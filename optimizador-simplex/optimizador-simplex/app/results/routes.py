"""Consulta detallada de resultados y generación de reportes PDF."""

from fractions import Fraction
from io import BytesIO
from xml.sax.saxutils import escape

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.api_utils import usuario_id_actual
from app.auth.responses import error_response
from app.models import Resultado
from app.services.modelo import armar_modelo
from app.services.recomendaciones import generar_recomendaciones
from app.services.simplex import resolver


bp = Blueprint("resultados", __name__, url_prefix="/api")


def _resultado_propietario(resultado_id):
    """Carga un resultado solo cuando pertenece a una empresa del usuario."""

    usuario_id = usuario_id_actual()
    if usuario_id is None:
        return None, error_response("token_invalido", "El token no es válido.", 401)
    resultado = Resultado.query.filter_by(id=resultado_id).first()
    if resultado is None or resultado.escenario.empresa.usuario_id != usuario_id:
        return None, error_response(
            "resultado_no_encontrado",
            "El resultado no existe o no pertenece a tu usuario.",
            404,
        )
    return resultado, None


def _numero(valor):
    """Convierte DECIMAL a número JSON, conservando null cuando no aplica."""

    return None if valor is None else float(valor)


def _posibilidades(resultado):
    """Arma el plan óptimo y las esquinas cercanas del tableau guardado."""

    if resultado.valor_z is None:
        return []
    variables = sorted(
        resultado.resultado_variables,
        key=lambda fila: fila.producto.id,
    )
    optimal = {
        "opcion": "Plan mixto (óptimo)",
        "valores": [float(fila.valor) for fila in variables],
        "z": float(resultado.valor_z),
        "pct": 100,
    }
    opciones = [optimal]
    # Los detalles de recomendaciones se almacenan como texto para respetar
    # el esquema original. El servicio reconstruye los datos estructurados de
    # las esquinas vecinas al leer el resultado.
    try:
        modelo = armar_modelo(resultado.escenario)
        solucion = resolver(
            modelo.c,
            modelo.A,
            modelo.b,
            modelo.tipos,
            objetivo=resultado.escenario.objetivo,
        )
        recomendaciones = generar_recomendaciones(
            solucion,
            [recurso.nombre for recurso in modelo.recursos],
            [recurso.unidad for recurso in modelo.recursos],
            nombres_productos={
                f"x{indice + 1}": producto.nombre
                for indice, producto in enumerate(modelo.productos)
            },
        )
        for recomendacion in recomendaciones:
            if recomendacion.get("tipo") != "alternativa_cercana":
                continue
            valores = recomendacion.get("valores", {})
            opciones.append(
                {
                    "opcion": recomendacion.get("alternativa", "Alternativa"),
                    "valores": [float(Fraction(valores.get(f"x{i + 1}", "0"))) for i in range(len(modelo.productos))],
                    "z": float(Fraction(recomendacion["z_alternativo"])),
                    "pct": float(Fraction(recomendacion["porcentaje"].rstrip("%"))),
                }
            )
    except (ValueError, ZeroDivisionError, KeyError):
        # El detalle guardado del resultado sigue siendo consultable aunque un
        # cambio futuro de catálogo impida reconstruir sus alternativas.
        pass
    return opciones


@bp.get("/resultados/<int:resultado_id>")
@jwt_required()
def obtener_resultado(resultado_id):
    """Devuelve plan, uso de recursos, posibilidades y recomendaciones.
    ---
    tags: [Resultados]
    security: [{Bearer: []}]
    responses:
      200: {description: Resultado detallado}
      401: {description: Token requerido o inválido}
      404: {description: Resultado no encontrado}
    """

    resultado, error = _resultado_propietario(resultado_id)
    if error:
        return error
    escenario = resultado.escenario
    recursos = []
    ajustes = {
        fila.recurso_id: fila.disponible for fila in escenario.escenario_recursos
    }
    filas_guardadas = {fila.recurso_id: fila for fila in resultado.resultado_recursos}
    for recurso in sorted(escenario.empresa.recursos, key=lambda fila: fila.id):
        guardado = filas_guardadas.get(recurso.id)
        disponible = ajustes.get(recurso.id, recurso.disponible)
        if guardado is None:
            continue
        recursos.append(
            {
                "recurso_id": recurso.id,
                "nombre": recurso.nombre,
                "unidad": recurso.unidad,
                "usado": _numero(guardado.usado),
                "disponible": _numero(disponible),
                "holgura": _numero(guardado.holgura),
                "precio_sombra": _numero(guardado.precio_sombra),
            }
        )
    variables = [
        {
            "producto_id": fila.producto_id,
            "codigo": fila.producto.codigo,
            "nombre": fila.producto.nombre,
            "valor": _numero(fila.valor),
            "aporte": _numero(fila.aporte),
        }
        for fila in sorted(
            resultado.resultado_variables, key=lambda fila: fila.producto.id
        )
    ]
    recomendaciones = [
        {
            "titulo": fila.titulo,
            "detalle": fila.detalle,
            "destacada": fila.destacada,
        }
        for fila in sorted(resultado.recomendaciones, key=lambda fila: fila.orden)
    ]
    return jsonify(
        {
            "id": resultado.id,
            "escenario": {
                "id": escenario.id,
                "nombre": escenario.nombre,
                "periodo": escenario.periodo,
                "objetivo": escenario.objetivo,
            },
            "estado": resultado.estado,
            "valor_z": _numero(resultado.valor_z),
            "iteraciones_n": resultado.iteraciones_n,
            "calculado_en": resultado.calculado_en.isoformat()
            if resultado.calculado_en
            else None,
            "variables": variables,
            "recursos": recursos,
            "posibilidades": _posibilidades(resultado),
            "recomendaciones": recomendaciones,
        }
    )


@bp.get("/resultados/<int:resultado_id>/procedimiento")
@jwt_required()
def obtener_procedimiento(resultado_id):
    """Devuelve la forma estándar y cada tableau con su pivote.
    ---
    tags: [Resultados]
    security: [{Bearer: []}]
    responses:
      200: {description: Procedimiento simplex paso a paso}
      401: {description: Token requerido o inválido}
      404: {description: Resultado no encontrado}
    """

    resultado, error = _resultado_propietario(resultado_id)
    if error:
        return error
    try:
        modelo = armar_modelo(resultado.escenario)
        nombres_restricciones = [recurso.nombre for recurso in modelo.recursos]
        productos_modelo = {producto.id for producto in modelo.productos}
        for asociacion in sorted(
            resultado.escenario.escenario_productos,
            key=lambda fila: fila.producto_id,
        ):
            if asociacion.producto_id not in productos_modelo:
                continue
            if asociacion.produccion_min is not None:
                nombres_restricciones.append(
                    f"producción mínima de {asociacion.producto.nombre}"
                )
            if asociacion.demanda_max is not None:
                nombres_restricciones.append(
                    f"demanda máxima de {asociacion.producto.nombre}"
                )
        forma_estandar = {
            "c": [str(valor) for valor in modelo.c],
            "A": [[str(valor) for valor in fila] for fila in modelo.A],
            "b": [str(valor) for valor in modelo.b],
            "tipos": modelo.tipos,
            "objetivo": resultado.escenario.objetivo,
            "variables": [producto.codigo for producto in modelo.productos],
            "restricciones": nombres_restricciones,
        }
    except ValueError as exc:
        return error_response("modelo_invalido", str(exc), 422)
    iteraciones = [
        {
            "numero": fila.numero,
            **fila.tabla_json,
            "entra": fila.entra,
            "sale": fila.sale,
            "explicacion": fila.explicacion,
        }
        for fila in sorted(resultado.iteraciones, key=lambda fila: fila.numero)
    ]
    return jsonify(
        {
            "resultado_id": resultado.id,
            "estado": resultado.estado,
            "valor_z": _numero(resultado.valor_z),
            "forma_estandar": forma_estandar,
            "iteraciones": iteraciones,
        }
    )


def _estilos_pdf():
    estilos = getSampleStyleSheet()
    estilos.add(
        ParagraphStyle(
            name="TituloCentro",
            parent=estilos["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1B2B3F"),
        )
    )
    estilos.add(
        ParagraphStyle(
            name="TablaChica",
            parent=estilos["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
        )
    )
    return estilos


def _tabla_pdf(datos, anchos=None, pivote=None):
    tabla = Table(datos, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    comandos = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B2B3F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C3CBD5")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF1F5")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if pivote:
        fila, columna = pivote
        comandos.append(
            ("BACKGROUND", (columna + 1, fila + 1), (columna + 1, fila + 1), colors.HexColor("#F5A524"))
        )
        comandos.append(
            ("TEXTCOLOR", (columna + 1, fila + 1), (columna + 1, fila + 1), colors.HexColor("#1B2B3F"))
        )
    tabla.setStyle(TableStyle(comandos))
    return tabla


def _crear_pdf(resultado, tipo):
    """Genera en memoria el informe o las tablas del procedimiento."""

    salida = BytesIO()
    pagina = letter if tipo == "reporte" else landscape(letter)
    documento = SimpleDocTemplate(
        salida,
        pagesize=pagina,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=f"Optimizador Simplex - {resultado.escenario.nombre}",
        author="Optimizador Simplex Grupo 2",
    )
    estilos = _estilos_pdf()
    historia = [
        Paragraph(
            "Comprobación paso a paso" if tipo == "comprobacion" else "Reporte de optimización",
            estilos["TituloCentro"],
        ),
        Spacer(1, 10),
        Paragraph(f"Escenario: {escape(resultado.escenario.nombre)}", estilos["Heading2"]),
        Paragraph(
            f"Estado: {resultado.estado} | Objetivo: {resultado.escenario.objetivo} | "
            f"Z: {_numero(resultado.valor_z) if resultado.valor_z is not None else 'No definido'}",
            estilos["BodyText"],
        ),
        Spacer(1, 12),
    ]
    if tipo == "reporte":
        historia.append(Paragraph("Plan de producción", estilos["Heading2"]))
        datos = [["Código", "Producto", "Cantidad", "Aporte"]]
        for fila in sorted(resultado.resultado_variables, key=lambda item: item.producto.id):
            datos.append(
                [fila.producto.codigo, fila.producto.nombre, str(fila.valor), str(fila.aporte)]
            )
        historia.append(_tabla_pdf(datos, [0.8 * inch, 3.3 * inch, 1.1 * inch, 1.1 * inch]))
        historia.extend([Spacer(1, 12), Paragraph("Uso de recursos", estilos["Heading2"])])
        ajustes = {fila.recurso_id: fila.disponible for fila in resultado.escenario.escenario_recursos}
        datos = [["Recurso", "Usado", "Disponible", "Holgura", "Precio sombra"]]
        for fila in sorted(resultado.resultado_recursos, key=lambda item: item.recurso.id):
            disponible = ajustes.get(fila.recurso_id, fila.recurso.disponible)
            datos.append(
                [fila.recurso.nombre, str(fila.usado), str(disponible), str(fila.holgura), str(fila.precio_sombra)]
            )
        historia.append(_tabla_pdf(datos, [2.2 * inch, 1 * inch, 1.1 * inch, 1 * inch, 1.2 * inch]))
        if resultado.recomendaciones:
            historia.extend([Spacer(1, 12), Paragraph("Recomendaciones", estilos["Heading2"])])
            for fila in sorted(resultado.recomendaciones, key=lambda item: item.orden):
                historia.append(
                    Paragraph(
                        f"<b>{escape(fila.titulo)}</b> {escape(fila.detalle)}",
                        estilos["BodyText"],
                    )
                )
                historia.append(Spacer(1, 5))
        posibilidades = _posibilidades(resultado)
        if posibilidades:
            historia.extend([Spacer(1, 10), Paragraph("Posibilidades", estilos["Heading2"])])
            datos = [["Opción", "Producción por producto", "Z", "% del óptimo"]]
            for opcion in posibilidades:
                datos.append(
                    [opcion["opcion"], ", ".join(map(str, opcion["valores"])), str(opcion["z"]), str(opcion["pct"])]
                )
            historia.append(_tabla_pdf(datos))
    else:
        iteraciones = sorted(resultado.iteraciones, key=lambda fila: fila.numero)
        for indice, iteracion in enumerate(iteraciones):
            if indice:
                historia.append(Spacer(1, 14))
            historia.append(Paragraph(f"Iteración {iteracion.numero}", estilos["Heading2"]))
            if iteracion.explicacion:
                historia.append(Paragraph(iteracion.explicacion, estilos["BodyText"]))
            tabla_json = iteracion.tabla_json
            columnas = tabla_json.get("columnas", [])
            base = tabla_json.get("base", [])
            filas = tabla_json.get("filas", [])
            datos = [["Base", *columnas]]
            for indice_fila, fila in enumerate(filas):
                nombre_base = base[indice_fila] if indice_fila < len(base) else ""
                datos.append([nombre_base, *fila])
            datos = [
                [Paragraph(escape(str(celda)), estilos["TablaChica"]) for celda in fila]
                for fila in datos
            ]
            pivote_info = tabla_json.get("pivote") or {}
            pivote = None
            if pivote_info and pivote_info.get("fila") is not None:
                pivote = (pivote_info["fila"], pivote_info["columna"])
            historia.append(_tabla_pdf(datos, pivote=pivote))
            if tabla_json.get("entra") or tabla_json.get("sale"):
                historia.append(
                    Paragraph(
                        f"Entra: {tabla_json.get('entra') or '—'} | Sale: {tabla_json.get('sale') or '—'} | "
                        f"Pivote: {tabla_json.get('elemento_pivote') or '—'}",
                        estilos["BodyText"],
                    )
                )
    documento.build(historia)
    salida.seek(0)
    return salida


@bp.get("/resultados/<int:resultado_id>/pdf")
@jwt_required()
def descargar_pdf(resultado_id):
    """Descarga el reporte o la comprobación simplex como PDF.
    ---
    tags: [Resultados]
    security: [{Bearer: []}]
    parameters:
      - in: path
        name: resultado_id
        type: integer
        required: true
      - in: query
        name: tipo
        type: string
        enum: [reporte, comprobacion]
        default: reporte
    produces: [application/pdf]
    responses:
      200: {description: Archivo PDF}
      400: {description: Tipo de documento inválido}
      404: {description: Resultado no encontrado}
    """

    resultado, error = _resultado_propietario(resultado_id)
    if error:
        return error
    tipo = request.args.get("tipo", "reporte").strip().lower()
    if tipo not in {"reporte", "comprobacion"}:
        return error_response(
            "tipo_pdf_invalido",
            "El parámetro tipo debe ser 'reporte' o 'comprobacion'.",
            400,
        )
    archivo = _crear_pdf(resultado, tipo)
    nombre = f"{tipo}-resultado-{resultado.id}.pdf"
    return send_file(
        archivo,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nombre,
    )
