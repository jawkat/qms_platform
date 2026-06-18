from app import db
from datetime import datetime
from .conformite import ExigenceType, NiveauRisqueType


class Domaine(db.Model):
    __tablename__ = 'domaine'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    textes = db.relationship('TexteReglementaire', back_populates='domaine_ref', foreign_keys='TexteReglementaire.domaine_id')


texte_secteur = db.Table('texte_secteur',
    db.Column('texte_id', db.Integer, db.ForeignKey('texte_reglementaire.id'), primary_key=True),
    db.Column('secteur_id', db.Integer, db.ForeignKey('secteur.id'), primary_key=True)
)


class TexteReglementaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50))
    titre = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50))
    domaine = db.Column(db.String(100))
    domaine_id = db.Column(db.Integer, db.ForeignKey('domaine.id', ondelete='SET NULL'), nullable=True)
    sousdomaine = db.Column(db.String(100))
    theme = db.Column(db.String(100))
    referentiel = db.Column(db.String(50))
    version_active_id = db.Column(db.Integer, db.ForeignKey('texte_version.id', ondelete='SET NULL'), nullable=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    domaine_ref = db.relationship('Domaine', back_populates='textes', foreign_keys=[domaine_id])
    version_active = db.relationship('TexteVersion', foreign_keys=[version_active_id])
    versions = db.relationship('TexteVersion', back_populates='texte', foreign_keys='TexteVersion.texte_id')
    secteurs = db.relationship('Secteur', secondary=texte_secteur, back_populates='textes')


class TexteVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texte_id = db.Column(db.Integer, db.ForeignKey('texte_reglementaire.id'))
    numero_version = db.Column(db.String(20))
    date_publication = db.Column(db.Date)
    statut = db.Column(db.String(20))
    pdf_key = db.Column(db.String(255))
    preambule = db.Column(db.Text)
    commentaire_version = db.Column(db.Text)
    cree_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    version_precedente_id = db.Column(db.Integer, db.ForeignKey('texte_version.id', ondelete='SET NULL'), nullable=True)

    texte = db.relationship('TexteReglementaire', back_populates='versions', foreign_keys=[texte_id])
    createur = db.relationship('Utilisateur')
    version_precedente = db.relationship('TexteVersion', foreign_keys=[version_precedente_id])
    entreprise_textes = db.relationship('EntrepriseTexte', back_populates='version')


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texte_version_id = db.Column(db.Integer, db.ForeignKey('texte_version.id'))
    numero_article = db.Column(db.Integer)
    contenu = db.Column(db.Text)
    exigence_type = db.Column(db.Enum(ExigenceType), nullable=False)
    niveau_risque = db.Column(db.Enum(NiveauRisqueType), nullable=False)
    resume_article = db.Column(db.Text)
    acteur = db.Column(db.String(100))
    domaine = db.Column(db.String(100))
    mots_cles = db.Column(db.JSON)
    hash_contenu = db.Column(db.String(64))

    version = db.relationship('TexteVersion')
    evaluations = db.relationship('EvaluationArticle', back_populates='article')

