from app.extensions import db
from app.models.serialization import serialize_model


class Consumo(db.Model):
    __tablename__ = "consumos"
    __table_args__ = (
        db.CheckConstraint("cantidad >= 0", name="ck_consumos_cantidad_no_negativa"),
    )

    producto_id = db.Column(
        db.Integer,
        db.ForeignKey("productos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    recurso_id = db.Column(
        db.Integer,
        db.ForeignKey("recursos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    cantidad = db.Column(db.Numeric(14, 4), nullable=False)

    producto = db.relationship("Producto", back_populates="consumos")
    recurso = db.relationship("Recurso", back_populates="consumos")

    def to_dict(self):
        return serialize_model(self)
