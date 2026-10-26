# ⚠️ WARNING: CADASTRE O E-MAIL NA LISTA DE PERMITIDOS DO MAILGUN!

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

## Aula 080 — Cadastro com notificação por e-mail

A página inicial recebe nome e e-mail, cadastra o novo usuário com a função
`User` e envia para o endereço informado uma mensagem com o prontuário, o nome
do aluno e o usuário cadastrado. Abaixo do formulário, exibe os usuários e suas
funções. Nomes já cadastrados mostram a saudação de retorno e não geram outro
cadastro ou envio.

Instale as dependências com `python -m pip install -r requirements.txt`.
Configure no arquivo `.env` as variáveis `API_URL` (endpoint de mensagens),
`API_KEY` (chave da API) e `API_FROM` (remetente autorizado pelo provedor).
O envio mantém a API HTTP já utilizada pelo projeto, com autenticação
`api`/chave e os campos `from`, `to`, `subject` e `text`.

O histórico em `/emailsEnviados` ou `/emails_enviados` registra apenas mensagens
aceitas pela API. A aceitação não garante a entrega na caixa de entrada.
Se a configuração estiver ausente ou o envio falhar, a página informa o problema
e mantém o usuário cadastrado. Não é necessário alterar o esquema do banco.

Execute os testes com `python -m unittest discover -s tests -v`.
Os testes de envio simulam a API e não enviam e-mails reais.
