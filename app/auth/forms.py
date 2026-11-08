from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField('E-mail', filters=[lambda value: value.strip().lower() if value else value], validators=[DataRequired(), Length(1, 254),
                                             Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Manter conectado')
    submit = SubmitField('Entrar')


class RegistrationForm(FlaskForm):
    email = StringField('E-mail', filters=[lambda value: value.strip().lower() if value else value], validators=[DataRequired(), Length(1, 254),
                                             Email()])
    username = StringField('Usuário', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    password = PasswordField('Senha', validators=[
        DataRequired(), EqualTo('password2', message='As senhas devem ser iguais.')])
    password2 = PasswordField('Confirme a senha', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('E-mail já cadastrado.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Nome de usuário já utilizado.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Senha atual', validators=[DataRequired()])
    password = PasswordField('Nova senha', validators=[
        DataRequired(), EqualTo('password2', message='As senhas devem ser iguais.')])
    password2 = PasswordField('Confirme a nova senha',
                              validators=[DataRequired()])
    submit = SubmitField('Atualizar senha')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('E-mail', filters=[lambda value: value.strip().lower() if value else value], validators=[DataRequired(), Length(1, 254),
                                             Email()])
    submit = SubmitField('Redefinir senha')


class PasswordResetForm(FlaskForm):
    password = PasswordField('Nova senha', validators=[
        DataRequired(), EqualTo('password2', message='As senhas devem ser iguais.')])
    password2 = PasswordField('Confirme a senha', validators=[DataRequired()])
    submit = SubmitField('Redefinir senha')


class ChangeEmailForm(FlaskForm):
    email = StringField('Novo e-mail', filters=[lambda value: value.strip().lower() if value else value], validators=[DataRequired(), Length(1, 254),
                                                 Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Atualizar e-mail')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('E-mail já cadastrado.')
