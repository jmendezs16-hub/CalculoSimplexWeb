from app.extensions import db
from app.models.serialization import serialize_model


class ResultadoVariable(db.Model):
    __tablename__ = "resultado_variables"

    resultado_id = db.Column(
        db.Integer,
        db.ForeignKey("resultados.id", ondelete="CASCADE"),
        primary_key=True,
    )
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), primary_key=True)
    valor = db.Column(db.Numeric(16, 4), nullable=False)
    aporte = db.Column(db.Numeric(16, 4), nullable=False)

    resultado = db.relationship("Resultado", back_populates="resultado_variables")
    producto = db.relationship("Producto", back_populates="resultado_variables")

    def to_dict(self):
        return serialize_model(self)
