from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[EqualTo('password')])
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    entreprise = StringField('Entreprise', validators=[DataRequired()])
    telephone = StringField('Téléphone', validators=[Optional()])
    pays = StringField('Pays', default='Maroc')
    taille = SelectField('Taille', choices=[('TPE', 'TPE'), ('PME', 'PME'), ('ETI', 'ETI'), ('GE', 'Grande entreprise')], default='PME')


class UserForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role_id = SelectField('Rôle', coerce=int, validators=[Optional()])
    actif = BooleanField('Actif', default=True)


class ProfileForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mot de passe actuel', validators=[DataRequired()])
    new_password = PasswordField('Nouveau mot de passe', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirmer', validators=[EqualTo('new_password')])


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nouveau mot de passe', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirmer', validators=[EqualTo('password')])
