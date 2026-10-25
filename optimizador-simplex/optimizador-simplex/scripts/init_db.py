"""Crea las tablas mapeadas por SQLAlchemy en la base configurada."""

from app import create_app
from app.extensions import db


def main():
    """Crea tablas faltantes; no borra ni modifica las existentes."""

    app = create_app("development")
    with app.app_context():
        db.create_all()
        print("Tablas de la aplicación creadas o ya existentes.")


if __name__ == "__main__":
    main()
