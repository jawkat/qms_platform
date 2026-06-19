from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, BooleanField
from wtforms.validators import DataRequired, Optional


class ActionForm(FlaskForm):
    description = TextAreaField('Description', validators=[DataRequired()])
    type_action = SelectField('Type', choices=[
        ('corrective', 'Corrective'),
        ('preventive', 'Préventive'),
        ('curative', 'Curative'),
    ], default='corrective')
    priorite = SelectField('Priorité', choices=[
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ], default='moyenne')
    statut = SelectField('Statut', choices=[
        ('A_FAIRE', 'À faire'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('CLOTURE', 'Clôturé'),
        ('ANNULE', 'Annulé'),
    ], default='A_FAIRE')
    responsable_id = SelectField('Responsable', coerce=int, validators=[Optional()])
    date_echeance = DateField('Date échéance', validators=[Optional()])
    est_recurrente = BooleanField('Action récurrente')
    frequence = SelectField('Fréquence', choices=[
        ('', 'Non récurrente'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('mensuel', 'Mensuelle'),
        ('trimestriel', 'Trimestrielle'),
        ('annuel', 'Annuelle'),
    ], default='')
    commentaire = TextAreaField('Commentaire', validators=[Optional()])
