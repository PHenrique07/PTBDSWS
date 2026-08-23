from datetime import datetime
from flask import Flask, request, make_response, redirect, abort, render_template, session, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired

app = Flask(__name__)
# Configuração da chave secreta
app.config['SECRET_KEY'] = 'Chave forte'

bootstrap = Bootstrap(app)
moment = Moment(app)

# Criação da classe do formulário principal
class NameForm(FlaskForm):
    name = StringField('Informe o seu nome', validators=[DataRequired()])
    sobrenome = StringField('Informe o seu sobrenome:')
    instituicao = StringField('Informe a sua Insituição de ensino:')
    disciplina = SelectField('Informe a sua disciplina:', choices=[('DSWA5', 'DSWA5'), ('DWBA4', 'DWBA4'), ('Gestão de projetos', 'Gestão de projetos')])
    submit = SubmitField('Submit')

# criação da classe do formulário de Login
class LoginForm(FlaskForm):
    username = StringField('', validators=[DataRequired()], render_kw={"placeholder": "Usuário ou e-mail"})
    password = PasswordField('', validators=[DataRequired()], render_kw={"placeholder": "Informe a sua senha"})
    submit = SubmitField('Enviar')

# Rota principal 
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        # salvando os dados do formulário
        session['name'] = form.name.data
        session['sobrenome'] = form.sobrenome.data
        session['instituicao'] = form.instituicao.data
        session['disciplina'] = form.disciplina.data
        
        # salvando IP e host na sessão
        session['remote_addr'] = request.remote_addr
        session['host'] = request.host
        
        return redirect(url_for('index'))
    
    return render_template('index.html', form=form, 
                           name=session.get('name'),
                           sobrenome=session.get('sobrenome'),
                           instituicao=session.get('instituicao'),
                           # o '' no final faz a disciplina virar uma string vazia se não existir, tirando o "None"
                           disciplina=session.get('disciplina', ''), 
                           # puxar da sessão
                           remote_addr=session.get('remote_addr'), 
                           host=session.get('host'), 
                           current_time=datetime.utcnow())

# Rota do Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session['username'] = form.username.data
        return redirect(url_for('login_response'))
        
    return render_template('login.html', form=form, current_time=datetime.utcnow())

# Rota de Resposta do Login
@app.route('/loginResponse')
def login_response():
    username = session.get('username')
    return render_template('loginResponse.html', username=username, current_time=datetime.utcnow())

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