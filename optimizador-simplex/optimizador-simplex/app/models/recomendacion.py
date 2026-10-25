from app.extensions import db
from app.models.serialization import serialize_model


class Recomendacion(db.Model):
    __tablename__ = "recomendaciones"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resultado_id = db.Column(
        db.Integer,
        db.ForeignKey("resultados.id", ondelete="CASCADE"),
        nullable=False,
    )
    orden = db.Column(db.Integer, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    detalle = db.Column(db.String(500), nullable=False)
    destacada = db.Column(db.Boolean, server_default=db.false())

    resultado = db.relationship("Resultado", back_populates="recomendaciones")

    def to_dict(self):
        return serialize_model(self)
