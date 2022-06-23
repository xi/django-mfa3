import pyotp

from .. import settings

name = 'TOTP'


def register_begin(user):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    url = totp.provisioning_uri(
        user.get_username(),
        issuer_name=settings.SITE_TITLE,
    )
    return {'url': url, 'secret': secret}, secret


def register_complete(state, request_data):
    totp = pyotp.TOTP(state)
    if not totp.verify(request_data):
        raise ValueError
    return state


def authenticate_begin(user):
    return None, None


def authenticate_complete(state, user, request_data):
    keys = user.mfakey_set.filter(method=name)
    for key in keys:
        totp = pyotp.TOTP(key.secret)
        if (totp.verify(request_data, valid_window=settings.TOTP_VALID_WINDOW)
                and request_data != key.last_code):
            key.last_code = request_data
            key.save()
            return
    raise ValueError
