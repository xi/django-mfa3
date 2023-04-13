from typing import Union
from urllib.parse import urlparse

from django.conf import settings as django_settings
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


def _get_verify_origin_fn():
    """
    Returns a custom verify_origin function which allows HTTP if using localhost.
    Why: browsers are allowed to consider localhost as a secure context, which is helpful for development.
    Setting a custom verify_origin like this is the solution suggested by python-fido2.
    See https://github.com/Yubico/python-fido2/issues/122
    """

    def is_localhost(hostname: Union[str,bytes]):
        return hostname == 'localhost' or hostname.endswith('.localhost')

    # This is the custom verify_origin function
    def verify_localhost_origin(origin):
        return is_localhost(urlparse(origin).hostname)

    # This custom function is only helpful if configured to use localhost in development
    if django_settings.DEBUG and is_localhost(settings.DOMAIN):
        return verify_localhost_origin

    # If custom function is not needed, fallback to using the python-fido2 default function.
    return None


fido2 = Fido2Server(
    rp=PublicKeyCredentialRpEntity(id=settings.DOMAIN, name=settings.SITE_TITLE),
    verify_origin=_get_verify_origin_fn(),
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
