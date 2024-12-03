from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm

# TODO prune this module

class RecaptchaAuthenticationForm(AuthenticationForm):
    pass


class RecaptchaPasswordResetForm(PasswordResetForm):
    pass


class RecaptchaSetPasswordForm(SetPasswordForm):
    pass

