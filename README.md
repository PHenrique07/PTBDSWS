# ⚠️ WARNING: O E-MAIL PRECISA ESTAR NA LISTA DE PERMITIDOS DO MAILGUN

> [!WARNING]
> **NO MODO SANDBOX DO MAILGUN, O E-MAIL DO DESTINATÁRIO PRECISA SER ADICIONADO MANUALMENTE À LISTA DE PERMITIDOS (AUTHORIZED RECIPIENTS) NO PAINEL DO MAILGUN.**
>
> **O destinatário também precisa confirmar a autorização pelo e-mail recebido. Sem isso, o Mailgun não permite o envio para esse endereço, mesmo que ele tenha sido preenchido corretamente no formulário do site.**
>
> **Confira também a caixa de spam, tanto para a confirmação quanto para as mensagens enviadas pelo site.**


# PTBDSWS - Desenvolvimento Web Servidor

Repositório criado para armazenar os códigos, atividades e projetos desenvolvidos para a matéria de **Desenvolvimento de Sistemas Web**.

## 🛠️ Tecnologias Utilizadas
* **Python**
* **Flask**
* **Flask-Bootstrap**
* **Flask-WTF**
* **Flask-Moment**
* **HTML5 / CSS3**

## 📚 Sobre o Repositório
Este espaço centraliza os códigos e exercícios práticos abordados nas aulas.


## Aula 090 - Autenticação



Inclui Flask-Login, senhas com hash, cadastro, confirmação da conta,
recuperação de senha e alteração de senha e e-mail. Tokens expiram em uma hora.

Execute no PowerShell:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m flask --app flasky db upgrade
.\venv\Scripts\python.exe -m flask --app flasky run
```

Cadastre-se em `/auth/register`, entre em `/auth/login` e confirme a conta pelo
link recebido por e-mail. A página `/auth/unconfirmed` permite reenviar o link.
Edição, exclusão e histórico de e-mails exigem login e confirmação da conta.

Configure `SECRET_KEY`, `API_URL`, `API_KEY` e `API_FROM` no `.env` ou no ambiente.
O envio usa a integração Mailgun existente. Links de autenticação são enviados
apenas ao titular; falhas de envio são informadas na tela.

A migração preserva usuários antigos, que não possuem e-mail e senha. O formulário
da Aula 080 continua na Home para o exercício anterior e não autentica usuários.
Use o novo cadastro com um nome de usuário disponível para criar uma conta.

Testes sem envio real de e-mails:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```
