import requests
from flask import current_app


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
