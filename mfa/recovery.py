import pyotp
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password

name = 'recovery'


def register_begin(user):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret, digits=10)
    code = totp.now()
    code = '%s-%s' % (code[:5], code[5:])
    state = make_password(code)
    return {'code': code}, state


def register_complete(state, request_data):
    if not check_password(request_data, state):
        raise ValueError
    return state


def authenticate_begin(user):
    return None, None


def authenticate_complete(state, user, request_data):
    keys = user.mfakey_set.filter(method=name)
    for key in keys:
        if check_password(request_data, key.secret):
            key.delete()
            return
    raise ValueError
