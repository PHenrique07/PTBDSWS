from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, BadData
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    email = db.Column(db.String(254), unique=True, index=True)
    password_hash = db.Column(db.String(256))
    confirmed = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, value):
        self.password_hash = generate_password_hash(value)

    def verify_password(self, value):
        return bool(self.password_hash) and check_password_hash(self.password_hash, value)

    def _generate_token(self, purpose, expiration=3600, **values):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=purpose)
        return serializer.dumps(dict(user_id=self.id, expiration=expiration, **values))

    @staticmethod
    def _read_token(token, purpose):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=purpose)
        try:
            data = serializer.loads(token, max_age=3600)
            return serializer.loads(token, max_age=min(data['expiration'], 3600))
        except (BadData, KeyError, TypeError, ValueError):
            return None

    def generate_confirmation_token(self, expiration=3600):
        return self._generate_token('confirm', expiration)

    def confirm(self, token):
        data = self._read_token(token, 'confirm')
        if not data or data.get('user_id') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        return self._generate_token('reset', expiration, password_hash=self.password_hash)

    @staticmethod
    def reset_password(token, new_password):
        data = User._read_token(token, 'reset')
        user = db.session.get(User, data.get('user_id')) if data else None
        if user is None or data.get('password_hash') != user.password_hash:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        return self._generate_token('change-email', expiration, new_email=new_email,
                                    old_email=self.email)

    def change_email(self, token):
        data = self._read_token(token, 'change-email')
        if not data or data.get('user_id') != self.id or data.get('old_email') != self.email:
            return False
        new_email = data.get('new_email')
        if not new_email or User.query.filter_by(email=new_email).first():
            return False
        self.email = new_email
        self.confirmed = True
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username


class Email(db.Model):
    __tablename__ = 'emails'
    id = db.Column(db.Integer, primary_key=True)
    de = db.Column(db.String(64))
    para = db.Column(db.String(256))
    assunto = db.Column(db.String(128))
    texto = db.Column(db.Text)
    data = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Email to %r>' % self.para


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
