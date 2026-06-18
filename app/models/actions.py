from app import db
from datetime import datetime
from enum import Enum


class ActionStatusEnum(Enum):
    A_FAIRE = "À faire"
    EN_COURS = "En cours"
    REALISE = "Réalisé"
    SOLDE = "Soldé"
    ANNULE = "Annulé"

    @classmethod
    def choices(cls):
        return [(m.name, m.value) for m in cls]


class ActionCorrective(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    domaine = db.Column(db.String(20), default='hse', nullable=False, index=True)

    description = db.Column(db.Text)
    cause_identifiee = db.Column(db.Text)
    type_action = db.Column(db.String(50), default='corrective')
    priorite = db.Column(db.String(20), default='moyenne')
    statut = db.Column(db.String(50), default='A_FAIRE')

    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_echeance = db.Column(db.Date)
    date_realisation = db.Column(db.Date)

    efficacite = db.Column(db.Float)
    commentaire_efficacite = db.Column(db.Text)
    critere_efficacite = db.Column(db.Text)

    rca_pourquoi1 = db.Column(db.Text)
    rca_pourquoi2 = db.Column(db.Text)
    rca_pourquoi3 = db.Column(db.Text)
    rca_pourquoi4 = db.Column(db.Text)
    rca_pourquoi5 = db.Column(db.Text)
    rca_conclusion = db.Column(db.Text)

    est_recurrente = db.Column(db.Boolean, default=False)
    frequence = db.Column(db.String(50))
    parent_action_id = db.Column(db.Integer, db.ForeignKey('action_corrective.id'))

    source_type = db.Column(db.String(50), nullable=True, index=True)
    source_id = db.Column(db.Integer, nullable=True)

    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    entreprise = db.relationship('Entreprise')
    responsable = db.relationship('Utilisateur', foreign_keys=[responsable_id])
    evaluation = db.relationship('EvaluationArticle', foreign_keys='ActionCorrective.source_id',
                                  primaryjoin="and_(ActionCorrective.source_type=='evaluation_article', "
                                              "foreign(ActionCorrective.source_id)==EvaluationArticle.id)",
                                  viewonly=True)

    proof_references = db.relationship(
        'ProofReference',
        primaryjoin="and_(foreign(ProofReference.entity_id)==ActionCorrective.id, "
                    "ProofReference.entity_type=='action_corrective')",
        viewonly=True
    )

    @property
    def statut_label(self):
        try:
            return ActionStatusEnum[self.statut].value
        except Exception:
            return self.statut
