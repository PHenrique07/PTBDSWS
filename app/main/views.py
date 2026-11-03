from flask import abort, current_app, flash, render_template, session, redirect, url_for
from requests.exceptions import RequestException
from sqlalchemy.exc import IntegrityError
from . import main
from .forms import DeleteUserForm, EditUserForm, NameForm
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

    return _render_index(form=form)


def _render_index(form=None, edit_form=None, editing_user_id=None):
    return render_template('index.html',
                           form=form if form is not None else NameForm(formdata=None),
                           delete_form=DeleteUserForm(),
                           edit_form=edit_form, editing_user_id=editing_user_id,
                           name=session.get('name'),
                           known=session.get('known', False),
                           email_status=session.get('email_status'),
                           users=User.query.order_by(User.id).all())


@main.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
def edit_user(user_id):
    user = db.get_or_404(User, user_id)
    form = EditUserForm()

    if form.validate_on_submit():
        previous_name = user.username
        user.username = form.name.data
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.name.errors.append('Já existe um usuário com esse nome.')
        else:
            if session.get('name') == previous_name:
                session['name'] = user.username
            flash('Nome do usuário atualizado com sucesso.')
            return redirect(url_for('.index'))
    elif not form.is_submitted():
        form.name.data = user.username

    return _render_index(edit_form=form, editing_user_id=user.id)


@main.route('/usuarios/<int:user_id>/excluir', methods=['POST'])
def delete_user(user_id):
    user = db.get_or_404(User, user_id)
    form = DeleteUserForm()
    if not form.validate_on_submit():
        abort(400)

    username = user.username
    db.session.delete(user)
    db.session.commit()
    if session.get('name') == username:
        session.pop('name', None)
        session.pop('known', None)
        session.pop('email_status', None)
    flash('Usuário removido com sucesso.')
    return redirect(url_for('.index'))


@main.route('/emailsEnviados', endpoint='emailsEnviados')
@main.route('/emails_enviados', endpoint='emails_enviados')
def emailsEnviados():
    emails = Email.query.order_by(Email.data.desc()).all()
    return render_template('emails_enviados.html', emails=emails)
