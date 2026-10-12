from datetime import datetime
from flask import render_template, session, redirect, url_for
from . import main
from .forms import NameForm
from .. import db
from ..models import User, Role, Email
from ..email import send_simple_message


@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()

    # Verifica se existem roles no banco, se não existir, cria.
    if Role.query.count() == 0:
        db.session.add_all([
            Role(name='Administrator'),
            Role(name='Moderator'),
            Role(name='User')
        ])
        db.session.commit()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user_role = Role.query.filter_by(name='User').first()
            user = User(username=form.name.data, role=user_role)
            db.session.add(user)
            db.session.commit()
            session['known'] = False

            # ==========================================================
            # REGISTRO E ENVIO DO E-MAIL
            # ==========================================================
            recipients = ["flaskaulasweb@zohomail.com", "santos.pedro4@aluno.ifsp.edu.br"]
            para_str = ', '.join([f"'{r}'" for r in recipients])
            assunto = "[Flasky] Novo usuário"
            texto = f"Prontuário: PT3037347\nNome: Pedro Henrique Santos da Silva\nUsuário cadastrado: {form.name.data}"

            # Registra no banco de dados para a relação de e-mails enviados
            email_log = Email(
                de=form.name.data,
                para=para_str,
                assunto=assunto,
                texto=texto,
                data=datetime.utcnow()
            )
            db.session.add(email_log)
            db.session.commit()

            try:
                response = send_simple_message(form.name.data)
                if response and response.status_code == 200:
                    print("E-mail enviado com sucesso!")
                elif response:
                    print(f"Falha ao enviar e-mail (Status {response.status_code}): {response.text}")
            except Exception as e:
                print(f"Erro ao enviar e-mail: {e}")

        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('.index'))

    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False))


@main.route('/emailsEnviados', endpoint='emailsEnviados')
@main.route('/emails_enviados', endpoint='emails_enviados')
def emailsEnviados():
    emails = Email.query.order_by(Email.data.desc()).all()
    return render_template('emails_enviados.html', emails=emails)
