import re
import unittest
from unittest.mock import patch

from app import create_app, db
from app.models import Email, Role, User


class UserManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        role = Role(name='User')
        self.user = User(username='Pedro Santos', role=role, confirmed=True)
        self.other_user = User(username='Gabriel', role=role)
        db.session.add_all([
            self.user, self.other_user,
            Email(de='site@example.com', para='destino@example.com',
                  assunto='[Flasky] Novo usuário', texto='Usuário cadastrado: Pedro Santos'),
        ])
        db.session.commit()
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session['_user_id'] = str(self.user.id)
            session['_fresh'] = True
        mail_patch = patch('app.email.requests.post')
        self.mail_request = mail_patch.start()
        self.addCleanup(mail_patch.stop)

    def tearDown(self):
        self.mail_request.assert_not_called()
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def edit_url(self, user_id=None):
        return '/usuarios/{}/editar'.format(self.user.id if user_id is None else user_id)

    def delete_url(self, user_id=None):
        return '/usuarios/{}/excluir'.format(self.user.id if user_id is None else user_id)

    def test_home_has_edit_and_post_delete_actions_for_each_user(self):
        html = self.client.get('/').get_data(as_text=True)
        for user in (self.user, self.other_user):
            self.assertIn('href="{}"'.format(self.edit_url(user.id)), html)
            self.assertIn('method="post" action="{}"'.format(self.delete_url(user.id)), html)
            self.assertIn('aria-label="Excluir {}"'.format(user.username), html)
        self.assertIn('btn btn-danger btn-xs', html)

    def test_edit_form_is_prefilled_and_can_be_cancelled(self):
        response = self.client.get(self.edit_url())
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Relação de usuários cadastrados', html)
        self.assertIn('<td>Gabriel</td>', html)
        self.assertNotIn('<h1>Editar usuário</h1>', html)
        self.assertIn('value="Pedro Santos"', html)
        self.assertIn('Salvar', html)
        self.assertIn('href="/#user-{}">Cancelar</a>'.format(self.user.id), html)
        self.assertIn('form="edit-user-{}"'.format(self.user.id), html)
        edit_form = re.search(r'<form id="edit-user-{}".*?</form>'.format(self.user.id),
                              html, re.DOTALL).group(0)
        self.assertIn('name="name"', edit_form)
        self.assertNotIn('name="email"', edit_form)
        self.assertIn('id="edit-name-{}"'.format(self.user.id), edit_form)
        self.assertIn('autofocus', edit_form)
        self.assertNotIn('id="edit-user-{}"'.format(self.other_user.id), html)
        cancelled = self.client.get('/').get_data(as_text=True)
        self.assertNotIn('id="edit-user-', cancelled)
        self.assertIn('<td>Pedro Santos</td>', cancelled)
        self.assertEqual(db.session.get(User, self.user.id).username, 'Pedro Santos')

    def test_registration_form_keeps_its_action_while_editing(self):
        html = self.client.get(self.edit_url()).get_data(as_text=True)
        registration_form = re.search(r'<form[^>]*class="form".*?</form>', html, re.DOTALL).group(0)
        self.assertIn('action="/"', registration_form)
        self.assertIn('name="email"', registration_form)
        self.assertNotIn('value="Pedro Santos"', registration_form)

    def test_edit_updates_name_and_greeting_but_preserves_role_and_email_history(self):
        user_id, role_id = self.user.id, self.user.role_id
        with self.client.session_transaction() as session:
            session['name'] = 'Pedro Santos'
            session['email_status'] = 'sent'
        response = self.client.post(self.edit_url(), data={'name': '  Pedro Santos 2  '},
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Nome do usuário atualizado com sucesso.', html)
        self.assertIn('Olá, Pedro Santos 2!', html)
        self.assertIn('E-mail enviado para o <strong>Administrador do sistema</strong>', html)
        user = db.session.get(User, user_id)
        self.assertEqual(user.username, 'Pedro Santos 2')
        self.assertEqual(user.role_id, role_id)
        self.assertEqual(User.query.count(), 2)
        self.assertEqual(Email.query.one().texto, 'Usuário cadastrado: Pedro Santos')

    def test_duplicate_name_is_rejected_and_database_remains_usable(self):
        response = self.client.post(self.edit_url(), data={'name': 'Gabriel'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Já existe um usuário com esse nome.', response.get_data(as_text=True))
        self.assertIn('id="edit-user-{}"'.format(self.user.id), response.get_data(as_text=True))
        self.assertIn('value="Gabriel"', response.get_data(as_text=True))
        self.assertEqual(db.session.get(User, self.user.id).username, 'Pedro Santos')
        self.assertEqual(User.query.count(), 2)
        response = self.client.post(self.edit_url(), data={'name': 'Pedro atualizado'})
        self.assertEqual(response.status_code, 302)

    def test_blank_and_oversized_names_are_rejected(self):
        for name in ('', '   ', 'a' * 65):
            with self.subTest(name=name):
                response = self.client.post(self.edit_url(), data={'name': name})
                self.assertEqual(response.status_code, 200)
                self.assertIn('has-error', response.get_data(as_text=True))
                self.assertEqual(db.session.get(User, self.user.id).username, 'Pedro Santos')

    def test_saving_unchanged_name_is_allowed(self):
        response = self.client.post(self.edit_url(), data={'name': 'Pedro Santos'},
                                    follow_redirects=True)
        self.assertIn('Nome do usuário atualizado com sucesso.', response.get_data(as_text=True))
        self.assertEqual(User.query.count(), 2)

    def test_delete_removes_only_selected_user_and_preserves_email_history(self):
        user_id = self.user.id
        with self.client.session_transaction() as session:
            session['name'] = 'Gabriel'
        response = self.client.post(self.delete_url(), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Usuário removido com sucesso.', html)
        self.assertIn('Olá, Gabriel!', html)
        self.assertNotIn('<td>Pedro Santos</td>', html)
        self.assertIsNone(db.session.get(User, user_id))
        self.assertEqual(User.query.one().username, 'Gabriel')
        self.assertEqual(Email.query.count(), 1)
        self.assertEqual(Role.query.count(), 1)

    def test_deleting_current_user_clears_their_greeting(self):
        with self.client.session_transaction() as session:
            session['name'] = 'Pedro Santos'
            session['known'] = True
            session['email_status'] = 'sent'
        response = self.client.post(self.delete_url(), follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn('Olá, Desconhecido!', html)
        self.assertNotIn('E-mail enviado', html)

    def test_get_cannot_delete_a_user(self):
        self.assertEqual(self.client.get(self.delete_url()).status_code, 405)
        self.assertEqual(User.query.count(), 2)

    def test_missing_users_return_404(self):
        self.assertEqual(self.client.get(self.edit_url(99999)).status_code, 404)
        self.assertEqual(self.client.post(self.edit_url(99999), data={'name': 'Novo'}).status_code, 404)
        self.assertEqual(self.client.post(self.delete_url(99999)).status_code, 404)

    def test_edit_requires_csrf_token(self):
        self.app.config['WTF_CSRF_ENABLED'] = True
        response = self.client.post(self.edit_url(), data={'name': 'Alterado'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Sessão do formulário inválida ou expirada.', response.get_data(as_text=True))
        self.assertEqual(db.session.get(User, self.user.id).username, 'Pedro Santos')
        html = self.client.get(self.edit_url()).get_data(as_text=True)
        token = re.search(r'id="edit-csrf-{}"[^>]*value="([^"]+)"'.format(self.user.id), html).group(1)
        response = self.client.post(self.edit_url(), data={'name': 'Alterado', 'csrf_token': token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(db.session.get(User, self.user.id).username, 'Alterado')

    def test_delete_requires_csrf_token(self):
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.assertEqual(self.client.post(self.delete_url()).status_code, 400)
        self.assertEqual(User.query.count(), 2)
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('id="delete-csrf-{}"'.format(self.user.id), html)
        token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)
        response = self.client.post(self.delete_url(), data={'csrf_token': token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.query.count(), 1)
