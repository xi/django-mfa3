def public(view_func):
    view_func.mfa_public = True
    return view_func
