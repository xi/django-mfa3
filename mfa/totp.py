from io import BytesIO

import pyotp
import qrcode
import qrcode.image.svg
from django.conf import settings

name = 'TOTP'


def get_qrcode(url):
    buf = BytesIO()
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
    img.save(buf)
    s = buf.getvalue().decode('utf-8')
    i = s.find('<svg')
    return s[i:]


def register_begin(user):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    url = totp.provisioning_uri(
        user.username,
        issuer_name=settings.MFA_SITE_TITLE,
    )
    context_data = {
        'url': url,
        'secret': secret,
        'qrcode': get_qrcode(url),
    }
    return context_data, secret


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
        if totp.verify(request_data) and request_data != key.last_code:
            key.last_code = request_data
            key.save()
            return
    raise ValueError
