from app.extensions import db
from app.models.serialization import serialize_model


class Recurso(db.Model):
    __tablename__ = "recursos"
    __table_args__ = (
        db.CheckConstraint("disponible >= 0", name="ck_recursos_disponible_no_negativa"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre = db.Column(db.String(150), nullable=False)
    unidad = db.Column(db.String(30), nullable=False)
    disponible = db.Column(db.Numeric(14, 4), nullable=False)

    empresa = db.relationship("Empresa", back_populates="recursos")
    consumos = db.relationship(
        "Consumo",
        back_populates="recurso",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    escenario_recursos = db.relationship(
        "EscenarioRecurso",
        back_populates="recurso",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    resultado_recursos = db.relationship(
        "ResultadoRecurso",
        back_populates="recurso",
        passive_deletes="all",
    )

    def to_dict(self):
        return serialize_model(self)
