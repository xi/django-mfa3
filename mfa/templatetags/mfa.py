import qrcode
import qrcode.image.svg
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='qrcode')
def get_qrcode(url):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
    s = img.to_string().decode('utf-8')
    i = s.find('<svg')
    return mark_safe(s[i:])
