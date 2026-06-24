from app.extensions import db
from .base import BaseModel


class EquipementMaintenance(BaseModel):
    __tablename__ = 'maintenance_equipement'
    nom = db.Column(db.String(100), nullable=False)
    reference = db.Column(db.String(50))
    description = db.Column(db.Text)
    localisation = db.Column(db.String(100))
    categorie = db.Column(db.String(50))
    frequence_maintenance = db.Column(db.String(50))
    date_acquisition = db.Column(db.Date)
    date_derniere_maintenance = db.Column(db.Date)
    date_prochaine_maintenance = db.Column(db.Date)
    statut = db.Column(db.String(20), default='actif')
    
    entreprise = db.relationship('Entreprise')


class InterventionMaintenance(BaseModel):
    __tablename__ = 'maintenance_intervention'
    equipement_id = db.Column(db.Integer, db.ForeignKey('maintenance_equipement.id'), nullable=False)
    type_intervention = db.Column(db.String(20))  # preventive, curative
    date_intervention = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    intervenant = db.Column(db.String(100))
    cout = db.Column(db.Float)
    duree_heures = db.Column(db.Float)
    pieces_changees = db.Column(db.Text)
    statut = db.Column(db.String(20), default='termine')
    
    entreprise = db.relationship('Entreprise')
    equipement = db.relationship('EquipementMaintenance')
