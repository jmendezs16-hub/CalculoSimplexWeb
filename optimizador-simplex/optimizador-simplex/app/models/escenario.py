from app.extensions import db
from app.models.serialization import serialize_model


class Escenario(db.Model):
    __tablename__ = "escenarios"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre = db.Column(db.String(150), nullable=False)
    periodo = db.Column(db.String(60))
    objetivo = db.Column(
        db.Enum("max", "min", name="objetivo_escenario"),
        nullable=False,
        server_default=db.text("'max'"),
    )
    creado_en = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    empresa = db.relationship("Empresa", back_populates="escenarios")
    escenario_productos = db.relationship(
        "EscenarioProducto",
        back_populates="escenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    escenario_recursos = db.relationship(
        "EscenarioRecurso",
        back_populates="escenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    resultado = db.relationship(
        "Resultado",
        back_populates="escenario",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self):
        return serialize_model(self)
