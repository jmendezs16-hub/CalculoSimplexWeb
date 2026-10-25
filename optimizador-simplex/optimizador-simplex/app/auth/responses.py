from flask import jsonify


def error_response(codigo, mensaje, status_code):
    return jsonify({"error": {"codigo": codigo, "mensaje": mensaje}}), status_code
