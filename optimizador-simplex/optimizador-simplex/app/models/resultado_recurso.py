from app.extensions import db
from app.models.serialization import serialize_model


class ResultadoRecurso(db.Model):
    __tablename__ = "resultado_recursos"

    resultado_id = db.Column(
        db.Integer,
        db.ForeignKey("resultados.id", ondelete="CASCADE"),
        primary_key=True,
    )
    recurso_id = db.Column(db.Integer, db.ForeignKey("recursos.id"), primary_key=True)
    usado = db.Column(db.Numeric(16, 4), nullable=False)
    holgura = db.Column(db.Numeric(16, 4), nullable=False)
    precio_sombra = db.Column(db.Numeric(16, 6), nullable=False)

    resultado = db.relationship("Resultado", back_populates="resultado_recursos")
    recurso = db.relationship("Recurso", back_populates="resultado_recursos")

    def to_dict(self):
        return serialize_model(self)
