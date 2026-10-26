import unittest
from unittest.mock import Mock, patch

from requests.exceptions import Timeout

from app import create_app, db
from app.email import send_simple_message
from app.models import Email, Role, User


class RegistrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config.update(
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI='sqlite://',
            API_URL='https://mail.example.com/messages',
            API_KEY='test-key',
            API_FROM='Site <site@example.com>',
        )
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def register(self, email='pedro@example.com', name='Pedro 2'):
        return self.client.post('/', data={'name': name, 'email': email}, follow_redirects=True)

    @patch('app.email.requests.post')
    def test_registration_sends_to_all_three_recipients_and_lists_user(self, post):
        post.return_value = Mock(status_code=200)
        response = self.register()
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Olá, Pedro 2!', html)
        self.assertIn('Aula 080', html)
        self.assertIn('name="email"', html)
        self.assertIn('Relação de usuários cadastrados', html)
        self.assertIn('<td>Pedro 2</td>', html)
        self.assertIn('<td>User</td>', html)
        self.assertIn('E-mail enviado', html)
        post.assert_called_once()
        payload = post.call_args.kwargs['data']
        self.assertEqual(payload['to'], [
            'flaskaulasweb@zohomail.com',
            'santos.pedro4@aluno.ifsp.edu.br',
            'pedro@example.com',
        ])
        self.assertIn('Prontuário: PT3037347', payload['text'])
        self.assertIn('Nome: Pedro Henrique Santos da Silva', payload['text'])
        self.assertIn('Usuário cadastrado: Pedro 2', payload['text'])
        email = Email.query.one()
        self.assertEqual(email.para, ', '.join(payload['to']))
        self.assertEqual(email.de, payload['from'])
        self.assertEqual(email.texto, payload['text'])

    @patch('app.email.requests.post')
    def test_fixed_recipients_are_not_duplicated(self, post):
        for recipient in ('flaskaulasweb@zohomail.com', 'SANTOS.PEDRO4@ALUNO.IFSP.EDU.BR'):
            with self.subTest(recipient=recipient):
                send_simple_message('Pedro', recipient)
                self.assertEqual(post.call_args.kwargs['data']['to'], [
                    'flaskaulasweb@zohomail.com',
                    'santos.pedro4@aluno.ifsp.edu.br',
                ])

    @patch('app.email.requests.post')
    def test_invalid_or_missing_email_does_not_register_or_send(self, post):
        for email in ('', 'invalido', 'nome@', 'nome@example.com\noutro@example.com'):
            with self.subTest(email=email):
                response = self.register(email=email)
                self.assertEqual(response.status_code, 200)
                self.assertIn('has-error', response.get_data(as_text=True))
        self.assertEqual(User.query.count(), 0)
        self.assertEqual(Email.query.count(), 0)
        post.assert_not_called()

    @patch('app.email.requests.post')
    def test_blank_or_oversized_name_is_rejected(self, post):
        for name in ('   ', 'a' * 65):
            self.register(name=name)
        self.assertEqual(User.query.count(), 0)
        post.assert_not_called()

    @patch('app.email.requests.post')
    def test_existing_user_does_not_duplicate_registration_or_email(self, post):
        db.session.add(User(username='Pedro 2'))
        db.session.commit()
        response = self.register()
        self.assertIn('Feliz em vê-lo novamente!', response.get_data(as_text=True))
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(Email.query.count(), 0)
        post.assert_not_called()

    @patch('app.email.requests.post')
    def test_api_failure_keeps_user_without_logging_success(self, post):
        post.return_value = Mock(status_code=401)
        response = self.register()
        self.assertIn('não confirmou o envio', response.get_data(as_text=True))
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(Email.query.count(), 0)

    @patch('app.email.requests.post', side_effect=Timeout)
    def test_timeout_keeps_user_without_logging_success(self, post):
        response = self.register()
        self.assertEqual(response.status_code, 200)
        self.assertIn('não confirmou o envio', response.get_data(as_text=True))
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(Email.query.count(), 0)

    @patch('app.email.requests.post')
    def test_missing_configuration_is_reported_without_sending(self, post):
        self.app.config['API_KEY'] = None
        response = self.register()
        self.assertIn('não está configurado', response.get_data(as_text=True))
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(Email.query.count(), 0)
        post.assert_not_called()

    @patch('app.email.requests.post')
    def test_accepted_response_is_logged(self, post):
        post.return_value = Mock(status_code=202)
        self.register()
        self.assertEqual(Email.query.count(), 1)

    @patch('app.email.requests.post')
    def test_api_request_uses_credentials_and_timeout(self, post):
        send_simple_message('Pedro', 'destino@example.com')
        self.assertEqual(post.call_args.args, ('https://mail.example.com/messages',))
        self.assertEqual(post.call_args.kwargs['auth'], ('api', 'test-key'))
        self.assertEqual(post.call_args.kwargs['timeout'], 15)

    def test_list_escapes_names_and_handles_missing_roles(self):
        db.session.add_all([
            User(username='<script>alert(1)</script>', role=Role(name='Administrator')),
            User(username='Sem função'),
        ])
        db.session.commit()
        response = self.client.get('/')
        html = response.get_data(as_text=True)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('<td>Admin</td>', html)
        self.assertIn('<td>—</td>', html)
