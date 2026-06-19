from app import db
from datetime import datetime


class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'))
    domaine = db.Column(db.String(20), default='hse', nullable=False, index=True)
    type = db.Column(db.String(50))
    date_audit = db.Column(db.Date)
    auditeur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    resultat_global = db.Column(db.String(50))
    commentaire = db.Column(db.Text)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseur_partage.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    entreprise = db.relationship('Entreprise')
    auditeur = db.relationship('Utilisateur')
    observations = db.relationship('AuditObservation', back_populates='audit')
    checklist_reponses = db.relationship('AuditChecklistReponse', backref='audit', lazy='dynamic')


class AuditObservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'))
    texte_id = db.Column(db.Integer, db.ForeignKey('texte_reglementaire.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    constat = db.Column(db.Text)
    niveau_conformite = db.Column(db.String(50))
    action_recommandee = db.Column(db.Text)

    audit = db.relationship('Audit', back_populates='observations')
    texte = db.relationship('TexteReglementaire')
    article = db.relationship('Article')


class ChecklistModele(db.Model):
    __tablename__ = 'checklist_modele'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type_audit = db.Column(db.String(30))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    items = db.relationship('ChecklistItem', backref='modele', lazy='dynamic',
                            cascade='all, delete-orphan')


class ChecklistItem(db.Model):
    __tablename__ = 'checklist_item'
    id = db.Column(db.Integer, primary_key=True)
    modele_id = db.Column(db.Integer, db.ForeignKey('checklist_modele.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    categorie = db.Column(db.String(100))
    ordre = db.Column(db.Integer, default=0)


class AuditChecklistReponse(db.Model):
    __tablename__ = 'audit_checklist_reponse'
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('checklist_item.id'), nullable=False)
    conforme = db.Column(db.Boolean)
    observation = db.Column(db.Text)
    item = db.relationship('ChecklistItem')
