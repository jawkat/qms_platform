from app.extensions import db
from .base import BaseModel
from datetime import datetime, date


class ChangeRequest(BaseModel):
    __tablename__ = 'change_request'
    reference = db.Column(db.String(50))
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type_changement = db.Column(db.String(50), nullable=False)
    priorite = db.Column(db.String(20), default='moyenne')
    statut = db.Column(db.String(30), default='brouillon')
    demandeur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    date_demande = db.Column(db.Date, nullable=False, default=date.today)
    date_souhaitee = db.Column(db.Date)
    raison = db.Column(db.Text)
    impact_description = db.Column(db.Text)
    impact_secteurs = db.Column(db.Text)
    impact_utilisateurs = db.Column(db.Text)
    impact_documents = db.Column(db.Text)
    impact_delai = db.Column(db.String(100))
    impact_cout = db.Column(db.String(100))
    risques_identifies = db.Column(db.Text)
    mesures_mitigation = db.Column(db.Text)
    approbateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_approbation = db.Column(db.DateTime)
    commentaire_approbation = db.Column(db.Text)
    date_realisation = db.Column(db.Date)
    date_verification = db.Column(db.Date)
    resultat_verification = db.Column(db.Text)
    source_type = db.Column(db.String(50))
    source_id = db.Column(db.Integer)

    entreprise = db.relationship('Entreprise')
    demandeur = db.relationship('Utilisateur', foreign_keys=[demandeur_id])
    approbateur = db.relationship('Utilisateur', foreign_keys=[approbateur_id])

    def generate_reference(self):
        from datetime import datetime
        count = ChangeRequest.query.filter_by(entreprise_id=self.entreprise_id).count() + 1
        return f"CR-{datetime.now().strftime('%Y%m')}-{count:04d}"
