from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, DateField, IntegerField, HiddenField
from wtforms.validators import Optional


class EvaluationForm(FlaskForm):
    conforme = SelectField('Conformité', choices=[
        ('', '-- Sélectionner --'),
        ('CONFORME', 'Conforme'),
        ('NON_CONFORME', 'Non conforme'),
        ('SANS_OBJET', 'Sans objet'),
    ], validators=[Optional()])
    applicable = SelectField('Applicable', choices=[
        ('', '-- Sélectionner --'),
        ('APPLICABLE', 'Applicable'),
        ('NON_APPLICABLE', 'Non applicable'),
    ], validators=[Optional()])
    observation = TextAreaField('Observation', validators=[Optional()])


class AttribuerTexteForm(FlaskForm):
    texte_version_id = IntegerField('Version du texte', validators=[DataRequired()])
    responsable_id = SelectField('Responsable', coerce=int, validators=[Optional()])
    mode_evaluation = SelectField('Mode évaluation', choices=[
        ('manuel', 'Manuelle'),
        ('PERIMETRE_GLOBAL', 'Périmètre global'),
        ('EVALUATION_ADHOC', 'Évaluation ad-hoc'),
    ], default='manuel')


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
    responsable_id = SelectField('Responsable', coerce=int, validators=[Optional()])
    date_echeance = DateField('Date échéance', validators=[Optional()])
