from app.extensions import db
from app.models.serialization import serialize_model


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    creado_en = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    empresas = db.relationship(
        "Empresa",
        back_populates="usuario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self):
        # El hash nunca se devuelve en una serialización de usuario.
        return serialize_model(self, exclude={"password_hash"})
