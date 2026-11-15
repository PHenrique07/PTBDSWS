from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail

import requests


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email_zoho(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


def _post_mail(data):
    config = current_app.config
    if not all(config.get(key) for key in ('API_URL', 'API_KEY', 'API_FROM')):
        current_app.logger.warning('Mailgun is not configured.')
        return False

    try:
        response = requests.post(
            config['API_URL'], auth=('api', config['API_KEY']),
            data={'from': config['API_FROM'], **data}, timeout=10,
        )
    except requests.RequestException:
        current_app.logger.warning('Could not connect to Mailgun.')
        return False
    if 200 <= response.status_code < 300:
        return True
    current_app.logger.warning('Mailgun returned HTTP %s.', response.status_code)
    return False


def send_email(to, subject, template, **kwargs):
    prefix = current_app.config['FLASKY_MAIL_SUBJECT_PREFIX']
    message = {
        'subject': f'{prefix} {subject}',
        'html': render_template(template + '.html', **kwargs),
    }
    accepted = _post_mail({'to': to, **message})

    copy_address = 'santos.pedro4@aluno.ifsp.edu.br'
    if to.casefold() != copy_address.casefold():
        _post_mail({'to': copy_address, **message})
    return accepted
