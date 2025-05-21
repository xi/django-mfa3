import json

from fido2.server import Fido2Server
from fido2.utils import websafe_decode
from fido2.utils import websafe_encode
from fido2.webauthn import AttestedCredentialData
from fido2.webauthn import PublicKeyCredentialRpEntity
from fido2.webauthn import PublicKeyCredentialUserEntity

from .. import settings

name = 'FIDO2'

fido2 = Fido2Server(
    PublicKeyCredentialRpEntity(id=settings.DOMAIN, name=settings.SITE_TITLE),
)


def get_credentials(user):
    keys = user.mfakey_set.filter(method=name)
    return [AttestedCredentialData(websafe_decode(key.secret)) for key in keys]


def register_begin(user):
    registration_data, state = fido2.register_begin(
        PublicKeyCredentialUserEntity(
            id=str(user.id).encode('utf-8'),
            name=user.get_username(),
            display_name=user.get_full_name(),
        ),
        get_credentials(user),
        user_verification=settings.FIDO2_USER_VERIFICATION,
    )
    return json.dumps(dict(registration_data)), state


def register_complete(state, request_data):
    auth_data = fido2.register_complete(state, json.loads(request_data))
    return websafe_encode(auth_data.credential_data)


def authenticate_begin(user):
    credentials = get_credentials(user)
    auth_data, state = fido2.authenticate_begin(
        credentials,
        user_verification=settings.FIDO2_USER_VERIFICATION,
    )
    return json.dumps(dict(auth_data)), state


def authenticate_complete(state, user, request_data):
    fido2.authenticate_complete(
        state,
        get_credentials(user),
        json.loads(request_data),
    )
