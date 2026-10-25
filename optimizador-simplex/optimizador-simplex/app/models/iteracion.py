from app.extensions import db
from app.models.serialization import serialize_model


class Iteracion(db.Model):
    __tablename__ = "iteraciones"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resultado_id = db.Column(
        db.Integer,
        db.ForeignKey("resultados.id", ondelete="CASCADE"),
        nullable=False,
    )
    numero = db.Column(db.Integer, nullable=False)
    tabla_json = db.Column(db.JSON, nullable=False)
    entra = db.Column(db.String(20))
    sale = db.Column(db.String(20))
    explicacion = db.Column(db.Text)

    resultado = db.relationship("Resultado", back_populates="iteraciones")

    def to_dict(self):
        return serialize_model(self)
