from app.extensions import db
from datetime import datetime
from enum import Enum
from .base import BaseModel, TimestampMixin


class ExigenceType(Enum):
    DEFINITION = 'Definition'
    OBLIGATION = 'Obligation'
    INTERDICTION = 'Interdiction'
    RECOMMANDATION = 'Recommandation'
    INFORMATION = 'Information'

    @classmethod
    def choices(cls):
        return [(m.name, m.value.title()) for m in cls]


class NiveauRisqueType(Enum):
    FAIBLE = 'Faible'
    MOYEN = 'Moyen'
    ELEVE = 'Eleve'
    CRITIQUE = 'Critique'

    @classmethod
    def choices(cls):
        return [(m.name, m.value) for m in cls]


class ApplicabiliteEnum(Enum):
    APPLICABLE = "Applicable"
    NON_APPLICABLE = "Non applicable"
    INFORMATION = "Information"
    A_CONFIRMER = "À confirmer"

    @classmethod
    def choices(cls):
        return [(m.name, m.value) for m in cls]


class ConformiteEnum(Enum):
    CONFORME = "Conforme"
    NON_CONFORME = "Non conforme"
    EN_COURS = "En cours"

    @classmethod
    def choices(cls):
        return [(m.name, m.value) for m in cls]


class EntrepriseTexte(BaseModel):
    __tablename__ = 'entreprise_texte'
    texte_version_id = db.Column(db.Integer, db.ForeignKey('texte_version.id', ondelete='CASCADE'))
    date_attribution = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    score_conformite = db.Column(db.Float)
    statut_evaluation = db.Column(db.String(50))
    statut_obligation = db.Column(db.String(30))
    motif_obligation = db.Column(db.String(255))
    mode_evaluation = db.Column(db.String(30))
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))

    entreprise = db.relationship('Entreprise')
    version = db.relationship('TexteVersion')
    responsable = db.relationship('Utilisateur')
    evaluations = db.relationship('EvaluationArticle', back_populates='entreprise_texte', cascade='all, delete-orphan')


class EvaluationArticle(db.Model, TimestampMixin): # No entreprise_id here, as it belongs to EntrepriseTexte
    __tablename__ = 'evaluation_article'
    entreprise_texte_id = db.Column(db.Integer, db.ForeignKey('entreprise_texte.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    applicable = db.Column(db.Enum(ApplicabiliteEnum), nullable=True)
    conforme = db.Column(db.Enum(ConformiteEnum), nullable=True)
    observation = db.Column(db.Text)
    evalue_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_evaluation = db.Column(db.DateTime, default=datetime.utcnow)

    entreprise_texte = db.relationship('EntrepriseTexte', back_populates='evaluations')
    article = db.relationship('Article')
    evaluateur = db.relationship('Utilisateur', foreign_keys=[evalue_par])
    historique = db.relationship('HistoriqueEvaluation', back_populates='evaluation', cascade='all, delete-orphan')
    actions = db.relationship('ActionCorrective',
                              primaryjoin="and_(ActionCorrective.source_type=='evaluation_article', "
                                          "foreign(ActionCorrective.source_id)==EvaluationArticle.id)",
                              viewonly=True)

    proof_references = db.relationship(
        'ProofReference',
        primaryjoin="and_(foreign(ProofReference.entity_id)==EvaluationArticle.id, "
                    "ProofReference.entity_type=='evaluation_article')",
        viewonly=True
    )


class HistoriqueEvaluation(db.Model, TimestampMixin):
    __tablename__ = 'historique_evaluation'
    evaluation_article_id = db.Column(db.Integer, db.ForeignKey('evaluation_article.id'))
    ancienne_valeur = db.Column(db.JSON)
    nouvelle_valeur = db.Column(db.JSON)
    modifie_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    commentaire = db.Column(db.Text)

    evaluation = db.relationship('EvaluationArticle', back_populates='historique')
    modificateur = db.relationship('Utilisateur')
