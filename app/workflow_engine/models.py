from app import db
from datetime import datetime


class WorkflowModele(db.Model):
    __tablename__ = 'workflow_modele'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    module_cible = db.Column(db.String(50), nullable=False)
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    entreprise = db.relationship('Entreprise')
    etapes = db.relationship('WorkflowEtape', backref='modele', lazy='dynamic',
                             cascade='all, delete-orphan', order_by='WorkflowEtape.ordre')


class WorkflowEtape(db.Model):
    __tablename__ = 'workflow_etape'
    id = db.Column(db.Integer, primary_key=True)
    modele_id = db.Column(db.Integer, db.ForeignKey('workflow_modele.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ordre = db.Column(db.Integer, nullable=False)
    role_requis = db.Column(db.String(50))
    action_requise = db.Column(db.String(50), default='approuver')
    statut = db.Column(db.String(20), default='active')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class WorkflowInstance(db.Model):
    __tablename__ = 'workflow_instance'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    modele_id = db.Column(db.Integer, db.ForeignKey('workflow_modele.id'), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    etape_courante_id = db.Column(db.Integer, db.ForeignKey('workflow_etape.id'))
    statut = db.Column(db.String(20), default='en_cours')
    date_debut = db.Column(db.DateTime, default=datetime.utcnow)
    date_fin = db.Column(db.DateTime)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    entreprise = db.relationship('Entreprise')
    modele = db.relationship('WorkflowModele')
    etape_courante = db.relationship('WorkflowEtape')
    historique = db.relationship('WorkflowHistorique', backref='instance', lazy='dynamic',
                                 cascade='all, delete-orphan')


class WorkflowHistorique(db.Model):
    __tablename__ = 'workflow_historique'
    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.Integer, db.ForeignKey('workflow_instance.id'), nullable=False)
    etape_id = db.Column(db.Integer, db.ForeignKey('workflow_etape.id'), nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    commentaire = db.Column(db.Text)
    date_action = db.Column(db.DateTime, default=datetime.utcnow)

    etape = db.relationship('WorkflowEtape')
    utilisateur = db.relationship('Utilisateur')
