from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template import loader

from . import settings

SUBJECT_TEMPLATE = 'mfa/login_failed_subject.txt'
BODY_TEMPLATE = 'mfa/login_failed_email.txt'
HTML_TEMPLATE = 'mfa/login_failed_email.html'


def send_mail(user, method):
    email_field_name = user.get_email_field_name()
    user_email = getattr(user, email_field_name)
    if not user_email:
        return 0

    context = {
        'email': user_email,
        'domain': settings.DOMAIN,
        'site_name': settings.SITE_TITLE,
        'user': user,
        'method': method.name,
    }

    try:
        subject = loader.render_to_string(SUBJECT_TEMPLATE, context)
        subject = ' '.join(subject.splitlines()).strip()
        body = loader.render_to_string(BODY_TEMPLATE, context)
    except TemplateDoesNotExist:
        return 0

    message = EmailMultiAlternatives(subject, body, to=[user_email])

    try:
        html_body = loader.render_to_string(HTML_TEMPLATE, context)
        message.attach_alternative(html_body, 'text/html')
    except TemplateDoesNotExist:
        pass

    return message.send()
