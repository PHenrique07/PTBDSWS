from datetime import datetime
from flask import Flask, request, make_response, redirect, abort, render_template, session, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
# Configuração da chave secreta
app.config['SECRET_KEY'] = 'Chave forte'

bootstrap = Bootstrap(app)
moment = Moment(app)

# Criação da classe do formulário
class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Rota principal 
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        # Verifica se o nome mudou para disparar a mensagem flash
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        
        # Salva o nome na sessão e redireciona (Padrão PRG)
        session['name'] = form.name.data
        return redirect(url_for('index'))
    
    return render_template('index.html', form=form, name=session.get('name'))

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

# Rota com código de status HTTP diferente
@app.route('/codigostatusdiferente')
def codigo_status_diferente():
    return '<h1>Bad request</h1>', 400

# Rota usando objeto de resposta para criar um cookie
@app.route('/objetoresposta')
def objeto_resposta():
    response = make_response('<h1>This document carries a cookie!</h1>')
    response.set_cookie('meu_cookie', 'valor_do_cookie')
    return response

# Rota de redirecionamento
@app.route('/redirecionamento')
def redirecionamento():
    return redirect('https://ptb.ifsp.edu.br')

# Rota para abortar a requisição
@app.route('/abortar')
def abortar():
    abort(404)
