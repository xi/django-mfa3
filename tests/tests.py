import pyotp
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from fido2.server import _verify_origin_for_rp

from mfa.mail import send_mail
from mfa.methods import fido2
from mfa.models import MFAKey
from mfa.templatetags.mfa import get_qrcode


class MFATestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', password='password')

    def login(self):
        return self.client.post('/login/', {
            'username': 'test',
            'password': 'password',
        })

    def assert_not_logged_in(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/login/?next=/')


class TOTPAuthViewTest(MFATestCase):
    def setUp(self):
        super().setUp()
        self.key = MFAKey.objects.create(
            user=self.user,
            method='TOTP',
            name='test',
            secret=pyotp.random_base32(),
        )
        self.totp = pyotp.TOTP(self.key.secret)

    def test_happy_flow(self):
        res = self.login()
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/mfa/auth/TOTP/')

        res = self.client.get('/mfa/auth/TOTP/')
        self.assertEqual(res.status_code, 200)

        res = self.client.post('/mfa/auth/TOTP/', {'code': self.totp.now()})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/')

        res = self.client.get('/')
        self.assertEqual(res.status_code, 204)

    def test_invalid_method(self):
        self.login()
        res = self.client.get('/mfa/auth/INVALID/')
        self.assertEqual(res.status_code, 404)

    def test_not_logged_in_before_mfa_auth(self):
        self.login()
        self.assert_not_logged_in()

    def test_no_auth_without_login(self):
        res = self.client.get('/mfa/auth/TOTP/')
        self.assertEqual(res.status_code, 404)

    def test_no_auth_without_challenge(self):
        self.login()

        res = self.client.post('/mfa/auth/TOTP/', {'code': self.totp.now()})
        self.assertEqual(res.status_code, 404)
        self.assert_not_logged_in()

    def test_wrong_code(self):
        self.login()

        res = self.client.get('/mfa/auth/TOTP/')
        self.assertEqual(res.status_code, 200)

        res = self.client.post('/mfa/auth/TOTP/', {'code': 'invalid'})
        self.assertEqual(res.status_code, 200)
        self.assert_not_logged_in()


class TOTPCreateViewTest(MFATestCase):
    def test_happy_flow(self):
        self.client.force_login(self.user)

        res = self.client.get('/mfa/create/TOTP/')
        self.assertEqual(res.status_code, 200)
        totp = pyotp.TOTP(res.context['mfa_data']['secret'])

        res = self.client.post('/mfa/create/TOTP/', {
            'name': 'test',
            'code': totp.now()
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/mfa/')

        self.assertEqual(MFAKey.objects.count(), 1)

    def test_not_logged_in(self):
        res = self.client.get('/mfa/create/TOTP/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/login/?next=/mfa/create/TOTP/')

    def test_no_create_without_challenge(self):
        self.client.force_login(self.user)

        res = self.client.post('/mfa/create/TOTP/', {
            'name': 'test',
            'code': 'invalid',
        })
        self.assertEqual(res.status_code, 404)
        self.assertEqual(MFAKey.objects.count(), 0)

    def test_wrong_code(self):
        self.client.force_login(self.user)

        res = self.client.get('/mfa/create/TOTP/')

        res = self.client.post('/mfa/create/TOTP/', {
            'name': 'test',
            'code': 'invalid',
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(MFAKey.objects.count(), 0)

    def test_new_challenge_on_get(self):
        self.client.force_login(self.user)

        res = self.client.get('/mfa/create/TOTP/')
        secret1 = res.context['mfa_data']['secret']

        res = self.client.get('/mfa/create/TOTP/')
        secret2 = res.context['mfa_data']['secret']

        self.assertNotEqual(secret1, secret2)

        totp = pyotp.TOTP(secret1)
        self.client.post('/mfa/create/TOTP/', {
            'name': 'test',
            'code': totp.now()
        })
        self.assertEqual(MFAKey.objects.count(), 0)

    def test_keep_challenge_on_validation(self):
        self.client.force_login(self.user)

        res = self.client.get('/mfa/create/TOTP/')
        secret1 = res.context['mfa_data']['secret']

        res = self.client.post('/mfa/create/TOTP/', {
            'name': 'test',
            'code': 'invalid',
        })
        secret2 = res.context['mfa_data']['secret']
        self.assertEqual(secret1, secret2)

        totp = pyotp.TOTP(secret1)
        self.client.post('/mfa/create/TOTP/', {
            'name': 'test',
            'code': totp.now()
        })
        self.assertEqual(MFAKey.objects.count(), 1)


class FIDO2Test(MFATestCase):
    # I have no clue how to simulate a FIDO2 authenticator,
    # so these are just some smoke tests.

    def test_login_redirect(self):
        self.key = MFAKey.objects.create(
            user=self.user,
            method='FIDO2',
            name='test',
            secret='mock',
        )
        res = self.login()
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/mfa/auth/FIDO2/')

    def test_create(self):
        self.client.force_login(self.user)
        res = self.client.get('/mfa/create/FIDO2/')
        self.assertEqual(res.status_code, 200)

    def test_encode(self):
        self.assertEqual(fido2.encode({'foo': [1, 2]}), 'a163666f6f820102')

    def test_decode(self):
        self.assertEqual(fido2.decode('a163666f6f820102'), {'foo': [1, 2]})

    def test_origin_https(self):
        for domain, value, expected in [
            ('example.com', 'https://example.com', True),
            ('example.com', 'http://example.com', False),
            ('example.com', 'http://localhost:8000', False),
            ('localhost', 'https://example.com', False),
            ('localhost', 'http://localhost:8000', True),
            ('localhost', 'http://127.0.0.1', False),
            ('localhost', 'http://foo.localhost', True),
            ('127.0.0.1', 'http://127.0.0.1', False),
            ('foo.localhost', 'http://foo.localhost', True),
        ]:
            with self.subTest(domain=domain, value=value):
                verify = _verify_origin_for_rp(domain)
                self.assertEqual(verify(value), expected)


class RecoveryTest(MFATestCase):
    def test_create(self):
        self.client.force_login(self.user)

        res = self.client.get('/mfa/create/recovery/')
        self.assertEqual(res.status_code, 200)
        code = res.context['mfa_data']['code']
        self.assertEqual(len(code), 11)

        res = self.client.post('/mfa/create/recovery/', {
            'name': 'test',
            'code': 'invalid',
        })
        self.assertEqual(res.status_code, 200)

        res = self.client.post('/mfa/create/recovery/', {
            'name': 'test',
            'code': code,
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/mfa/')

        self.assertEqual(MFAKey.objects.count(), 1)

    def test_authenticate(self):
        MFAKey.objects.create(
            user=self.user,
            method='FIDO2',
            name='test',
            secret='mock',
        )
        MFAKey.objects.create(
            user=self.user,
            method='recovery',
            name='recovery',
            secret=make_password('123456'),
        )

        res = self.login()
        self.assertEqual(res.status_code, 302)

        res = self.client.get('/mfa/auth/recovery/')
        self.assertEqual(res.status_code, 200)

        res = self.client.post('/mfa/auth/recovery/', {'code': 'invalid'})
        self.assertEqual(res.status_code, 200)

        res = self.client.post('/mfa/auth/recovery/', {'code': '123456'})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/mfa/')

        res = self.client.get('/')
        self.assertEqual(res.status_code, 204)

        self.assertEqual(MFAKey.objects.count(), 1)


class MFAEnforceMiddlewareTest(MFATestCase):
    def test_redirect(self):
        self.login()
        res = self.client.get('/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/mfa/')

    def test_public(self):
        self.login()
        res = self.client.post('/logout/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/')


class PatchAdminTest(TestCase):
    def test_root(self):
        res = self.client.get('/admin/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/admin/login/?next=/admin/')

        res = self.client.get(res.url)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/login/?next=/admin/')

    def test_app(self):
        res = self.client.get('/admin/mfa/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/admin/login/?next=/admin/mfa/')

        res = self.client.get(res.url)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/login/?next=/admin/mfa/')

    def test_login(self):
        res = self.client.get('/admin/login/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/login/?next=/admin/')


class ListViewTest(MFATestCase):
    def test_list_view(self):
        self.client.force_login(self.user)
        MFAKey.objects.create(
            user=self.user,
            method='recovery',
            name='recovery',
            secret=make_password('123456'),
        )
        res = self.client.get('/mfa/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content.count(b'<li>'), 1)


class DeleteViewTest(MFATestCase):
    def test_delete_view(self):
        self.client.force_login(self.user)
        key = MFAKey.objects.create(
            user=self.user,
            method='recovery',
            name='recovery',
            secret=make_password('123456'),
        )
        res = self.client.post(f'/mfa/{key.pk}/delete/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/mfa/')
        self.assertEqual(MFAKey.objects.filter(pk=key.pk).count(), 0)


class QRCodeTest(TestCase):
    def test_is_svg(self):
        code = get_qrcode('some_data')
        self.assertTrue(code.startswith('<svg'))
        self.assertTrue(code.endswith('</svg>'))


class MailTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', password='password', email='test@example.com'
        )

    def test_send_mail(self):
        count = send_mail(self.user, fido2)
        self.assertEqual(count, 1)

        message = mail.outbox[0]
        self.assertEqual(message.to, ['test@example.com'])
        self.assertEqual(message.subject, 'Attempted login to Tests using a wrong two-factor authentication code')  # noqa
        self.assertEqual(message.body, """Dear test,

We detected an attempt to log in to your account on Tests
(localhost) using a wrong two-factor authentication code. This means someone
managed to enter the correct password, but failed at FIDO2.

If this was you and you entered a wrong two-factor authentication code by
accident, you may ignore this email.

If this was not you, we strongly recommend to change your password.
""")
