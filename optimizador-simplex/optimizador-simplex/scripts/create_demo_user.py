import argparse
from getpass import getpass

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Usuario


def main():
    parser = argparse.ArgumentParser(description="Crea un usuario demo para la API.")
    parser.add_argument("--nombre", default="Usuario Demo")
    parser.add_argument("--correo", default="demo@example.com")
    args = parser.parse_args()

    password = getpass("Contraseña para el usuario demo: ")
    confirmacion = getpass("Confirma la contraseña: ")
    if not password:
        parser.error("La contraseña no puede estar vacía.")
    if password != confirmacion:
        parser.error("Las contraseñas no coinciden.")

    app = create_app("development")
    with app.app_context():
        correo = args.correo.strip()
        existente = Usuario.query.filter_by(correo=correo).first()
        if existente:
            parser.error(f"Ya existe un usuario con el correo {correo}.")

        usuario = Usuario(
            nombre=args.nombre.strip(),
            correo=correo,
            password_hash=generate_password_hash(password),
        )
        db.session.add(usuario)
        db.session.commit()

        print(f"Usuario demo creado: {usuario.correo} (id={usuario.id}).")


if __name__ == "__main__":
    main()
