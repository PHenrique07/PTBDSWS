from flask_wtf import FlaskForm
from wtforms import EmailField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class NameForm(FlaskForm):
    name = StringField('Qual é o seu nome?', filters=[lambda value: value.strip() if value else value],
                       validators=[DataRequired(message='Informe o seu nome.'), Length(max=64)])
    email = EmailField('Qual é o seu email (Envio de notificação do novo usuário)?',
                       filters=[lambda value: value.strip() if value else value],
                       validators=[DataRequired(message='Informe o seu e-mail.'),
                                   Email(message='Informe um e-mail válido.'), Length(max=254)])
    submit = SubmitField('Submit')
