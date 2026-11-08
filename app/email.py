import requests
from flask import current_app, render_template, flash


def registration_message(novo_usuario, destinatario):
    recipients = ['flaskaulasweb@zohomail.com', 'santos.pedro4@aluno.ifsp.edu.br']
    if destinatario.casefold() not in (email.casefold() for email in recipients):
        recipients.append(destinatario)

    return {
        'from': current_app.config.get('API_FROM'),
        'to': recipients,
        'subject': '[Flasky] Novo usuário',
        'text': (f'Prontuário: PT3037347\nNome: Pedro Henrique Santos da Silva\n'
                 f'Usuário cadastrado: {novo_usuario}')
    }


def send_simple_message(novo_usuario, destinatario):
    if not (current_app.config.get('API_URL') and current_app.config.get('API_KEY') and current_app.config.get('API_FROM')):
        return None

    # Faz a requisição usando as variáveis salvas nas configurações do app
    return requests.post(
        current_app.config['API_URL'],
        auth=("api", current_app.config['API_KEY']),
        data=registration_message(novo_usuario, destinatario),
        timeout=15
    )


def send_email(to, subject, template, **context):
    """Send private account links only to their intended recipient."""
    if not all(current_app.config.get(key) for key in ('API_URL', 'API_KEY', 'API_FROM')):
        flash('O serviço de e-mail não está configurado. Configure-o e solicite um novo envio.')
        return False
    try:
        response = requests.post(
            current_app.config['API_URL'],
            auth=('api', current_app.config['API_KEY']),
            data={'from': current_app.config['API_FROM'], 'to': [to],
                  'subject': '[Flasky] ' + subject,
                  'text': render_template(template + '.txt', **context),
                  'html': render_template(template + '.html', **context)},
            timeout=15,
        )
        if 200 <= response.status_code < 300:
            flash('E-mail enviado. Confira sua caixa de entrada e a pasta de spam.')
            return True
    except requests.RequestException:
        current_app.logger.warning('Falha de conexão ao enviar e-mail de autenticação.')
    flash('Não foi possível enviar o e-mail. Tente novamente mais tarde.')
    return False
