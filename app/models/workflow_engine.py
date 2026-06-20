from app.extensions import db
from datetime import datetime, timedelta
from .base import BaseModel, TimestampMixin


class WorkflowModele(BaseModel):
    __tablename__ = 'workflow_modele'
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    module_cible = db.Column(db.String(50), nullable=False)
    statut = db.Column(db.String(20), default='actif')

    entreprise = db.relationship('Entreprise')
    etapes = db.relationship('WorkflowEtape', backref='modele', lazy='dynamic',
                             cascade='all, delete-orphan', order_by='WorkflowEtape.ordre')

    def to_dict(self):
        d = super().to_dict()
        d['nb_etapes'] = self.etapes.count()
        return d


class WorkflowEtape(db.Model, TimestampMixin):
    __tablename__ = 'workflow_etape'
    modele_id = db.Column(db.Integer, db.ForeignKey('workflow_modele.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ordre = db.Column(db.Integer, nullable=False)
    role_requis = db.Column(db.String(50))
    action_requise = db.Column(db.String(50), default='approuver')
    delai_jours = db.Column(db.Integer, nullable=True)
    statut = db.Column(db.String(20), default='active')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class WorkflowInstance(BaseModel):
    __tablename__ = 'workflow_instance'
    modele_id = db.Column(db.Integer, db.ForeignKey('workflow_modele.id'), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    etape_courante_id = db.Column(db.Integer, db.ForeignKey('workflow_etape.id'))
    demandeur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    statut = db.Column(db.String(20), default='en_cours')
    date_debut = db.Column(db.DateTime, default=datetime.utcnow)
    date_fin = db.Column(db.DateTime)
    date_deadline = db.Column(db.DateTime, nullable=True)
    commentaire = db.Column(db.Text)

    entreprise = db.relationship('Entreprise')
    modele = db.relationship('WorkflowModele')
    etape_courante = db.relationship('WorkflowEtape', foreign_keys=[etape_courante_id])
    demandeur = db.relationship('Utilisateur', foreign_keys=[demandeur_id])
    historique = db.relationship('WorkflowHistorique', backref='instance', lazy='dynamic',
                                 cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_wf_entity', 'entity_type', 'entity_id'),
        db.Index('idx_wf_statut', 'statut'), # entreprise_id is already indexed by BaseModel
    )

    def compute_deadline(self):
        if self.etape_courante and self.etape_courante.delai_jours:
            return self.date_debut + timedelta(days=self.etape_courante.delai_jours)
        return None

    def is_en_retard(self):
        if self.statut != 'en_cours' or not self.date_deadline:
            return False
        return datetime.utcnow() > self.date_deadline

    def progress_pct(self):
        etapes = list(self.modele.etapes.order_by(WorkflowEtape.ordre).all())
        if not etapes:
            return 0
        current_idx = next((i for i, e in enumerate(etapes) if e.id == self.etape_courante_id), -1)
        if self.statut == 'termine':
            return 100
        if current_idx < 0:
            return 0
        return int((current_idx / len(etapes)) * 100)

    def to_dict(self):
        return {
            'id': self.id,
            'modele': self.modele.nom if self.modele else '',
            'modele_id': self.modele_id,
            'entity_type': self.entity_type, 'entity_id': self.entity_id,
            'etape_courante': self.etape_courante.nom if self.etape_courante else '',
            'etape_courante_id': self.etape_courante_id,
            'statut': self.statut,
            'demandeur': f'{self.demandeur.prenom} {self.demandeur.nom}' if self.demandeur else '',
            'date_debut': self.date_debut.isoformat() if self.date_debut else None,
            'date_fin': self.date_fin.isoformat() if self.date_fin else None,
            'date_deadline': self.date_deadline.isoformat() if self.date_deadline else None,
            'en_retard': self.is_en_retard(),
            'progress': self.progress_pct(),
            'nb_etapes': self.modele.etapes.count() if self.modele else 0,
        }


class WorkflowHistorique(db.Model, TimestampMixin):
    __tablename__ = 'workflow_historique'
    instance_id = db.Column(db.Integer, db.ForeignKey('workflow_instance.id'), nullable=False)
    etape_id = db.Column(db.Integer, db.ForeignKey('workflow_etape.id'), nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    commentaire = db.Column(db.Text)
    date_action = db.Column(db.DateTime, default=datetime.utcnow)

    etape = db.relationship('WorkflowEtape')
    utilisateur = db.relationship('Utilisateur')

    def to_dict(self):
        return {
            'id': self.id, 'etape': self.etape.nom if self.etape else '',
            'utilisateur': f'{self.utilisateur.prenom} {self.utilisateur.nom}' if self.utilisateur else '',
            'action': self.action, 'commentaire': self.commentaire,
            'date_action': self.date_action.isoformat() if self.date_action else None,
        }
