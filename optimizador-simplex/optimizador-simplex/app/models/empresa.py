from app.extensions import db
from app.models.serialization import serialize_model


class Empresa(db.Model):
    __tablename__ = "empresas"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre = db.Column(db.String(150), nullable=False)
    rubro = db.Column(db.String(100))
    moneda = db.Column(db.String(10), server_default="Q")
    periodo = db.Column(
        db.Enum("diario", "semanal", "mensual", "anual", name="periodo_empresa"),
        server_default=db.text("'mensual'"),
    )
    activa = db.Column(db.Boolean, server_default=db.true())

    usuario = db.relationship("Usuario", back_populates="empresas")
    productos = db.relationship(
        "Producto",
        back_populates="empresa",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    recursos = db.relationship(
        "Recurso",
        back_populates="empresa",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    escenarios = db.relationship(
        "Escenario",
        back_populates="empresa",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self):
        return serialize_model(self)
