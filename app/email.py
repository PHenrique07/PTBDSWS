import requests
from flask import current_app


def send_simple_message(novo_usuario):
    # O corpo do email exigido pelo enunciado da atividade
    corpo_email = f"Prontuário: PT3037347\nNome: Pedro Henrique Santos da Silva\nUsuário cadastrado: {novo_usuario}"

    recipients = ["flaskaulasweb@zohomail.com", "santos.pedro4@aluno.ifsp.edu.br"]

    if not (current_app.config.get('API_URL') and current_app.config.get('API_KEY') and current_app.config.get('API_FROM')):
        return None

    # Faz a requisição usando as variáveis salvas nas configurações do app
    return requests.post(
        current_app.config['API_URL'],
        auth=("api", current_app.config['API_KEY']),
        data={"from": current_app.config['API_FROM'],
              "to": recipients,
              "subject": "[Flasky] Novo usuário",
              "text": corpo_email}
    )
