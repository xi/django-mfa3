from urllib.parse import urlparse

from django.conf import settings as django_settings
from django.utils.http import is_same_domain
from fido2 import cbor
from fido2.server import Fido2Server
from fido2.utils import websafe_decode
from fido2.utils import websafe_encode
from fido2.webauthn import AttestationObject
from fido2.webauthn import AttestedCredentialData
from fido2.webauthn import AuthenticatorData
from fido2.webauthn import CollectedClientData
from fido2.webauthn import PublicKeyCredentialRpEntity

from .. import settings

name = 'FIDO2'

def _get_verify_origin_fn(domain):
    """Do not require https on localhost in DEBUG mode.

    See https://github.com/Yubico/python-fido2/issues/122
    """

    def is_localhost(hostname):
        allowed_hosts = ['.localhost', '127.0.0.1', '[::1]']
        return any(is_same_domain(hostname, h) for h in allowed_hosts)

    def verify_localhost_origin(origin):
        return urlparse(origin).hostname == domain

    if django_settings.DEBUG and is_localhost(domain):
        return verify_localhost_origin
    else:
        return None


fido2 = Fido2Server(
    PublicKeyCredentialRpEntity(id=settings.DOMAIN, name=settings.SITE_TITLE),
    verify_origin=_get_verify_origin_fn(settings.DOMAIN),
)


def encode(data):
    return cbor.encode(data).hex()


def decode(s):
    return cbor.decode(bytes.fromhex(s))


def get_credentials(user):
    keys = user.mfakey_set.filter(method=name)
    return [AttestedCredentialData(websafe_decode(key.secret)) for key in keys]


def register_begin(user):
    registration_data, state = fido2.register_begin(
        {
            'id': str(user.id).encode('utf-8'),
            'name': user.get_username(),
            'displayName': user.get_full_name(),
        },
        get_credentials(user),
    )
    return encode(registration_data), state


def register_complete(state, request_data):
    data = decode(request_data)
    auth_data = fido2.register_complete(
        state,
        CollectedClientData(data['clientData']),
        AttestationObject(data['attestationObject']),
    )
    return websafe_encode(auth_data.credential_data)


def authenticate_begin(user):
    credentials = get_credentials(user)
    auth_data, state = fido2.authenticate_begin(credentials)
    return encode(auth_data), state


def authenticate_complete(state, user, request_data):
    data = decode(request_data)
    fido2.authenticate_complete(
        state,
        get_credentials(user),
        data['credentialId'],
        CollectedClientData(data['clientData']),
        AuthenticatorData(data['authenticatorData']),
        data['signature'],
    )
