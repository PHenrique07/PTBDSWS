import unittest
from unittest.mock import Mock, patch
from app import create_app, db
from app.models import User


class AuthenticationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config.update(WTF_CSRF_ENABLED=False, API_URL='https://mail.example/messages',
                               API_KEY='test', API_FROM='site@example.com')
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.mail = patch('app.email.requests.post', return_value=Mock(status_code=200))
        self.post = self.mail.start()

    def tearDown(self):
        self.mail.stop()
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def account(self, confirmed=True):
        user = User(username='Pedro', email='pedro@example.com', password='cat', confirmed=confirmed)
        db.session.add(user)
        db.session.commit()
        return user

    def login(self, **data):
        return self.client.post('/auth/login', data=dict(email='pedro@example.com', password='cat', **data))

    def test_password_hash_and_random_salt(self):
        user = self.account()
        other = User(password='cat')
        self.assertNotEqual(user.password_hash, 'cat')
        self.assertNotEqual(user.password_hash, other.password_hash)
        self.assertTrue(user.verify_password('cat'))
        self.assertFalse(user.verify_password('dog'))
        self.assertFalse(User().verify_password('cat'))
        with self.assertRaises(AttributeError):
            _ = user.password

    def test_registration_and_private_confirmation_email(self):
        response = self.client.post('/auth/register', data=dict(
            email='PEDRO@example.com', username='Pedro', password='cat', password2='cat'))
        self.assertEqual(response.status_code, 302)
        user = User.query.one()
        self.assertEqual(user.email, 'pedro@example.com')
        self.assertEqual(user.role.name, 'User')
        self.assertFalse(user.confirmed)
        payload = self.post.call_args.kwargs['data']
        self.assertEqual(payload['to'], ['pedro@example.com'])
        self.assertIn('/auth/confirm/', payload['text'])
        self.assertNotIn('/auth/confirm/', self.client.get('/auth/login').get_data(as_text=True))

    def test_duplicate_and_mismatched_registration(self):
        self.account()
        for email, username, password2 in [('pedro@example.com', 'Other', 'cat'),
                                            ('other@example.com', 'Pedro', 'cat'),
                                            ('other@example.com', 'Other', 'dog')]:
            response = self.client.post('/auth/register', data=dict(
                email=email, username=username, password='cat', password2=password2))
            self.assertEqual(response.status_code, 200)
        self.assertEqual(User.query.count(), 1)
        self.post.assert_not_called()

    def test_login_logout_and_protection(self):
        self.account()
        self.assertEqual(self.client.get('/emails_enviados').status_code, 302)
        self.assertEqual(self.login().status_code, 302)
        self.assertEqual(self.client.get('/emails_enviados').status_code, 200)
        self.assertIn('Pedro', self.client.get('/').get_data(as_text=True))
        self.client.get('/auth/logout')
        self.assertEqual(self.client.get('/emails_enviados').status_code, 302)

    def test_invalid_login_and_csrf(self):
        self.account()
        response = self.client.post('/auth/login', data=dict(email='pedro@example.com', password='wrong'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/emails_enviados').status_code, 302)
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.assertEqual(self.login().status_code, 200)
        self.assertEqual(self.client.get('/emails_enviados').status_code, 302)

    def test_remember_me(self):
        self.account()
        response = self.login(remember_me='y')
        self.assertTrue(any('remember_token=' in value for value in response.headers.getlist('Set-Cookie')))

    def test_external_next_is_rejected(self):
        self.account()
        for target in ('//example.com', 'https://example.com', '/\\example.com'):
            response = self.client.post('/auth/login', query_string={'next': target},
                                        data=dict(email='pedro@example.com', password='cat'))
            self.assertEqual(response.location, '/')
            self.client.get('/auth/logout')

    def test_confirmation_access_and_invalid_tokens(self):
        user = self.account(confirmed=False)
        token = user.generate_confirmation_token()
        self.login()
        self.assertEqual(self.client.get('/').location, '/auth/unconfirmed')
        self.assertEqual(self.client.get('/auth/unconfirmed').status_code, 200)
        self.assertFalse(user.confirm('invalid'))
        other = User(id=999)
        self.assertFalse(other.confirm(token))
        self.assertFalse(user.confirm(user.generate_confirmation_token(expiration=-1)))
        self.client.get('/auth/confirm/' + token)
        self.assertTrue(user.confirmed)
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_reset_and_email_change_tokens_are_scoped_and_expire(self):
        user = self.account()
        token = user.generate_reset_token()
        self.assertFalse(user.confirm(token))
        self.assertFalse(User.reset_password(user.generate_reset_token(-1), 'new'))
        self.assertTrue(User.reset_password(token, 'new'))
        db.session.commit()
        self.assertFalse(User.reset_password(token, 'reused'))
        self.assertTrue(user.verify_password('new'))
        token = user.generate_email_change_token('new@example.com')
        self.assertTrue(user.change_email(token))
        self.assertFalse(user.change_email(token))
        self.assertEqual(user.email, 'new@example.com')

    def test_reset_unknown_address_does_not_crash(self):
        response = self.client.post('/auth/reset', data={'email': 'unknown@example.com'})
        self.assertEqual(response.status_code, 302)
        self.post.assert_not_called()

    def test_mail_failure_keeps_account_for_retry(self):
        self.post.return_value.status_code = 401
        response = self.client.post('/auth/register', data=dict(
            email='pedro@example.com', username='Pedro', password='cat', password2='cat'),
                                   follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.query.count(), 1)
        self.assertFalse(User.query.one().confirmed)

    def test_pages_render(self):
        for path in ('/auth/login', '/auth/register', '/auth/reset'):
            self.assertEqual(self.client.get(path).status_code, 200)
        self.account()
        self.login()
        for path in ('/auth/change-password', '/auth/change_email'):
            self.assertEqual(self.client.get(path).status_code, 200)
