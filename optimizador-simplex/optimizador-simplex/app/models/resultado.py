from app.extensions import db
from app.models.serialization import serialize_model


class Resultado(db.Model):
    __tablename__ = "resultados"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    escenario_id = db.Column(
        db.Integer,
        db.ForeignKey("escenarios.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    estado = db.Column(
        db.Enum(
            "optimo",
            "infactible",
            "no_acotado",
            "multiple",
            "degenerado",
            name="estado_resultado",
        ),
        nullable=False,
    )
    valor_z = db.Column(db.Numeric(16, 4))
    iteraciones_n = db.Column(db.Integer, nullable=False, server_default="0")
    calculado_en = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    escenario = db.relationship("Escenario", back_populates="resultado")
    resultado_variables = db.relationship(
        "ResultadoVariable",
        back_populates="resultado",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    resultado_recursos = db.relationship(
        "ResultadoRecurso",
        back_populates="resultado",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    recomendaciones = db.relationship(
        "Recomendacion",
        back_populates="resultado",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    iteraciones = db.relationship(
        "Iteracion",
        back_populates="resultado",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self):
        return serialize_model(self)
