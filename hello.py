# A very simple Flask Hello World app for you to get started with...
from datetime import datetime
from flask import Flask, request, make_response, redirect, abort, render_template
from flask_moment import Moment

app = Flask(__name__)
moment = Moment(app)

# Rota principal
@app.route('/')
def hello_world():
    return render_template('index.html', current_time=datetime.utcnow())

# Rota com variável na URL
@app.route('/user/<name>')
def user(name):
    return render_template(
        'user.html',
        name=name,
        prontuario='PT3037347',
        instituicao='IFSP'
    )

# Rota de contexto de requisição
@app.route('/contextorequisicao/<name>')
def contexto_requisicao(name):
    user_agent = request.headers.get('User-Agent')
    return render_template(
        'contexto.html',
        name=name,
        user_agent=user_agent,
        remote_addr=request.remote_addr,
        host=request.host
    )

# rota com código de status HTTP diferente
@app.route('/codigostatusdiferente')
def codigo_status_diferente():
    # retorna uma mensagem de erro e o código HTTP 400
    return '<h1>Bad request</h1>', 400

# Rota usando objeto de resposta para criar um cookie
@app.route('/objetoresposta')
def objeto_resposta():
    # resposta personalizada para embutir um cookie
    response = make_response('<h1>This document carries a cookie!</h1>')
    response.set_cookie('meu_cookie', 'valor_do_cookie')
    return response

# rota de redirecionamento
@app.route('/redirecionamento')
def redirecionamento():
    # redireciona para o site do IF
    return redirect('https://ptb.ifsp.edu.br')

# rota para abortar a requisição
@app.route('/abortar')
def abortar():
    # força um erro 404
    abort(404)