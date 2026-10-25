from app.extensions import db
from app.models.serialization import serialize_model


class Producto(db.Model):
    __tablename__ = "productos"
    __table_args__ = (
        db.UniqueConstraint("empresa_id", "codigo", name="uq_productos_empresa_codigo"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
    )
    codigo = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    beneficio_unitario = db.Column(db.Numeric(12, 4), nullable=False)
    activo = db.Column(db.Boolean, server_default=db.true())

    empresa = db.relationship("Empresa", back_populates="productos")
    consumos = db.relationship(
        "Consumo",
        back_populates="producto",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    escenario_productos = db.relationship(
        "EscenarioProducto",
        back_populates="producto",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    resultado_variables = db.relationship(
        "ResultadoVariable",
        back_populates="producto",
        passive_deletes="all",
    )

    def to_dict(self):
        return serialize_model(self)
