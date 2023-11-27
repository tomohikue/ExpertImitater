from django.conf import settings
from django.contrib.auth.decorators import login_required

def login_required_conditional(function=None):
    if settings.LOGIN_REQUIRED:
        if function is not None:
            return login_required(function)
    return function
