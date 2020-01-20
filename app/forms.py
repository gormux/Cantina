from flask_wtf import FlaskForm
from wtforms import (BooleanField, PasswordField, StringField, SubmitField,
                     TextAreaField)
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se rappeler de moi')
    submit = SubmitField('Connexion')


class UserAddForm(FlaskForm):
    userlist = TextAreaField('Utilisateurs à ajouter')
    submit = SubmitField('Créer les utilisateurs')
