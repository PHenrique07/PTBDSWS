from flask import current_app, render_template, session, redirect, url_for
from requests.exceptions import RequestException
from . import main
from .forms import NameForm
from .. import db
from ..models import User, Role, Email
from ..email import registration_message, send_simple_message


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
        session.pop('email_status', None)
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user_role = Role.query.filter_by(name='User').first()
            user = User(username=form.name.data, role=user_role)
            db.session.add(user)
            db.session.commit()
            session['known'] = False

            session['email_status'] = 'failed'
            try:
                response = send_simple_message(form.name.data, form.email.data)
                if response is None:
                    session['email_status'] = 'unconfigured'
                elif 200 <= response.status_code < 300:
                    message = registration_message(form.name.data, form.email.data)
                    db.session.add(Email(
                        de=message['from'], para=', '.join(message['to']),
                        assunto=message['subject'], texto=message['text']
                    ))
                    db.session.commit()
                    session['email_status'] = 'sent'
                else:
                    current_app.logger.warning('Falha ao enviar e-mail (status %s).', response.status_code)
            except RequestException:
                current_app.logger.warning('Falha de conexão com o serviço de e-mail.')

        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('.index'))

    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False),
                           email_status=session.get('email_status'),
                           users=User.query.order_by(User.id).all())


@main.route('/emailsEnviados', endpoint='emailsEnviados')
@main.route('/emails_enviados', endpoint='emails_enviados')
def emailsEnviados():
    emails = Email.query.order_by(Email.data.desc()).all()
    return render_template('emails_enviados.html', emails=emails)
