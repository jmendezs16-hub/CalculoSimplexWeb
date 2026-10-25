from app.extensions import db
from app.models.serialization import serialize_model


class EscenarioRecurso(db.Model):
    __tablename__ = "escenario_recursos"

    escenario_id = db.Column(
        db.Integer,
        db.ForeignKey("escenarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    recurso_id = db.Column(
        db.Integer,
        db.ForeignKey("recursos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    disponible = db.Column(db.Numeric(14, 4), nullable=False)

    escenario = db.relationship("Escenario", back_populates="escenario_recursos")
    recurso = db.relationship("Recurso", back_populates="escenario_recursos")

    def to_dict(self):
        return serialize_model(self)
