import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Carrega as variáveis do arquivo .env criado localmente (pra n dar ban)
basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv(os.path.join(basedir, '.env'), override=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#config das api
app.config['API_KEY'] = os.environ.get('API_KEY')
app.config['API_URL'] = os.environ.get('API_URL')
app.config['API_FROM'] = os.environ.get('API_FROM')

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


class NameForm(FlaskForm):
    # Formulário limpo apenas com o campo Nome, para bater com a imagem da tarefa
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')

# ==========================================
# FUNÇÃO PARA ENVIAR O E-MAIL 
# =========================================
def send_simple_message(novo_usuario):
    # O corpo do email exigido pelo enunciado da atividade
    corpo_email = f"Prontuário: PT3037347\nNome: Pedro Henrique Santos da Silva\nUsuário cadastrado: {novo_usuario}"
    
    # Faz a requisição usando as variáveis salvas nas configurações do app
    return requests.post(
        app.config['API_URL'],
        auth=("api", app.config['API_KEY']),
        data={"from": app.config['API_FROM'],
              "to": ["flaskaulasweb@zohomail.com", "santos.pedro4@aluno.ifsp.edu.br"],
              "subject": "Novo Cadastro na Aplicação WEB",
              "text": corpo_email}
    )


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
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
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            # Salva apenas o nome do usuário, sem o campo role_id que foi removido da tela
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
            
            # ==========================================================
            # EMAIL
            # ==========================================================
            try:
                response = send_simple_message(form.name.data)
                if response.status_code == 200:
                    print("E-mail enviado com sucesso!")
                else:
                    print(f"Falha ao enviar e-mail (Status {response.status_code}): {response.text}")
            except Exception as e:
                print(f"Erro ao enviar e-mail: {e}")
                
        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('index'))
    
    # Faz a busca de todos os usuários cadastrados no banco
    users = User.query.all()
    roles = Role.query.all()
    
    # Passa a lista de usuários (users) para o template
    return render_template('index.html', form=form, name=session.get('name'),
                           known=session.get('known', False), users=users, roles=roles)