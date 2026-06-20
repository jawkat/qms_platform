from app.extensions import db
from .base import BaseModel


class EmployeQHSE(BaseModel):
    __tablename__ = 'employe_qhse'
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    matricule = db.Column(db.String(50))
    poste = db.Column(db.String(100))
    department = db.Column(db.String(100))
    date_embauche = db.Column(db.Date)
    date_visite_medicale = db.Column(db.Date)
    date_prochaine_visite = db.Column(db.Date)
    habilitations = db.Column(db.JSON, default=list)  # liste des habilitations
    epi_attribues = db.Column(db.JSON, default=list)
    statut = db.Column(db.String(20), default='actif')
    
    entreprise = db.relationship('Entreprise')
    utilisateur = db.relationship('Utilisateur')
