0.5.0 (2022-04-15)
------------------

-   Security fix: The admin login was not adapted, so it could be used to
    bypass MFA. As a fix, django-mfa3 will now automatically patch `AdminSite`
    so the admin login redirects to regular login.
-   Drop support for django 2.2
-   Use a more efficient string encoding for FIDO2 messages


0.4.0 (2022-01-25)
------------------

-   Drop support for python 3.6, add support for python 3.10
-   Drop support for django 3.1, add support for django 4.0
-   No longer include MFA code in credentials for `user_login_failed`


0.3.0 (2021-08-25)
------------------

-   Add recovery codes. Check the example templates for references to
    "recovery" to see what needs to be changed.
-   Add new setting `MFA_METHODS` to change the set of enabled methods.


0.2.5 (2021-07-18)
------------------

-   Fix usage with custom User models that use a different username field
    (thanks to Ashok Argent-Katwala)


0.2.4 (2021-07-07)
------------------

-   Security fix: Do not allow users to see the names of/delete other user's
    keys (secrets were not leaked)


0.2.3 (2021-07-05)
------------------

-   Fix packaging: include .mo files


0.2.2 (2021-07-05)
------------------

-   Fix packaging: include templatetags


0.2.1 (2021-07-02)
------------------

-   Fix packaging: exclude tests


0.2.0 (2021-07-02)
------------------

-   Convert qrcode to template filter. In templates, change
    `{{ mfa_data.qrcode|safe }}` to `{% load mfa %} {{ mfa_data.url|qrcode }}`.
-   Fix form validation on missing code
-   Add german translation
-   Use `never_cache` and `sensitive_post_parameters` decorators
-   Do not generate a new challenge on validation errors


0.1.0 (2021-06-29)
------------------

-   Trigger `user_login_failed` on failed second factor. This can be used to
    integrating with external rate limiting solutions such as django-axes.
-   Fix: include JS files in python package
-   Render qrcode server-side
-   Convenience: redirect to TOTP auth if no FIDO2 key exists
-   Add optional `MFAEnforceMiddleware`
-   Tweak admin UI
-   Tweak example templates


0.0.0 (2021-06-21)
------------------

initial release
