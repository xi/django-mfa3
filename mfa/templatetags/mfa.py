from io import BytesIO

import qrcode
import qrcode.image.svg
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='qrcode')
def get_qrcode(url):
    buf = BytesIO()
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
    img.save(buf)
    s = buf.getvalue().decode('utf-8')
    i = s.find('<svg')
    return mark_safe(s[i:])
