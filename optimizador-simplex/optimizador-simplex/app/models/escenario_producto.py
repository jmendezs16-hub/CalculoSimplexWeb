from app.extensions import db
from app.models.serialization import serialize_model


class EscenarioProducto(db.Model):
    __tablename__ = "escenario_productos"

    escenario_id = db.Column(
        db.Integer,
        db.ForeignKey("escenarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    producto_id = db.Column(
        db.Integer,
        db.ForeignKey("productos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    incluido = db.Column(db.Boolean, server_default=db.true())
    produccion_min = db.Column(db.Numeric(14, 4))
    demanda_max = db.Column(db.Numeric(14, 4))

    escenario = db.relationship("Escenario", back_populates="escenario_productos")
    producto = db.relationship("Producto", back_populates="escenario_productos")

    def to_dict(self):
        return serialize_model(self)
