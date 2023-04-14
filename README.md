# django-mfa3

An opinionated Django app that handles multi factor authentication (MFA) via
FIDO2, TOTP, and recovery codes.

## Features

-   Two factor authentication is required on login (if the user has registered a key)
-   Stuff just works without much configuration
-   The UI allows to add new keys and to remove keys that have been compromised
-   You can optionally enforce MFA for all users
-   You can (and should) customize the templates
-   Simple code, few dependencies

## Installation

```
pip install django-mfa3
```

## Usage

1.  Add `'mfa'` to `INSTALLED_APPS`
2.  Use `mfa.views.LoginView` instead of the regular login view. (Be sure to
    remove any other login routes, otherwise the multi factor authentication
    can be circumvented. The admin login will automatically be patched to
    redirect to the regular login.)
3.  Set `MFA_DOMAIN = 'example.com'` and `MFA_SITE_TITLE = 'My site'`
4.  Register URLs: `path('mfa/', include('mfa.urls', namespace='mfa')`
5.  The included templates are just examples, so you should [replace them](https://docs.djangoproject.com/en/stable/howto/overriding-templates/) with your own
6.  FIDO2 requires client side code. You can either implement it yourself or use the included fido2.js (in which case you will have to provide the third party library [cbor-js](https://www.npmjs.com/package/cbor-js)).
7.  Somewhere in your app, add a link to `'mfa:list'`

## Enforce MFA

Optionally, you can add `'mfa.middleware.MFAEnforceMiddleware'` to `MIDDLEWARE`
(after `AuthenticationMiddleware`!). It will force users to setup two factor
authentication by redirecting all authenticated requests to `'mfa:list'` as
long as the user has no MFAKeys. You can use `mfa.decorators.public` to add
exceptions.

## Send email on failed login attempt

If someone failes to login on the second factor that might indicate that the
first factor (password) has been compromised. django-mfa3 will automatically
send a warning to affected users under the following conditions:

-   Django needs to be [configured for sending email](https://docs.djangoproject.com/en/4.1/topics/email/)
-   There must be an email address associated with the user account
-   You need to provide some templates
    -   `mfa/login_failed_subject.txt`: optional, a default is included
    -   `mfa/login_failed_email.txt`: required, an example is included in the
        [tests](https://github.com/xi/django-mfa3/blob/main/tests/templates/mfa/login_failed_email.txt)
    -   `mfa/login_failed_email.html`: optional

All templates have access to the following context data: `email`, `domain`,
`site_name`, `user`, `method`.

## Status

I am not sure whether I will be able to maintain this library long-term. If you
would like to help or even take ownership of this project, please contact me!

## Related projects

django-mfa3 is based on [pyotp](https://github.com/pyauth/pyotp) and
[python-fido2](https://github.com/Yubico/python-fido2).

It is inspired by but not otherwise affiliated with
[django-mfa2](https://github.com/mkalioby/django-mfa2).
A big difference between the two projects is that django-mfa2 supports many
methods, while django-mfa3 only supports FIDO2 and TOTP. U2F was dropped
because it is now superseded by FIDO2. Email and Trusted Devices were dropped
because I felt like they have inferior security properties compared to FIDO2
and TOTP.

Another major inspiration is
[django-otp](https://github.com/django-otp/django-otp). It is probably the most
mature library when it comes to two factor authentication in django. However,
its [basic structure is not compatible with
FIDO2](https://github.com/django-otp/django-otp/issues/40).

It is recommended to use django-mfa3 with
[django-axes](https://github.com/jazzband/django-axes) for rate limiting. It is
also compatible with
[django-stronghold](https://github.com/mgrouchy/django-stronghold/).

## Security considerations

The actual cryptography is handled by pyotp and python-fido2. This library only
provides the glue code for django. Still, there could be issues in the glue.

A notable attack surface is server state: The authentication consists of three
separate HTTP requests: The regular login, fetching a challenge, and a
response. The server keeps some state in the session across these requests. For
example, the user is temporarily stored in the session until the second factor
authentication is done. The logic for handling this state is not as straight
forward as I would like and there might be issues hidden in there.

Please also be careful when implementing and using this library in your project
to prevent higher level security or usability issues. Please refer to other
guidelines like the
[OWASP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html)
for more informaton on that topic.
