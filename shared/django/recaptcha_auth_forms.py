from .emac_utils import get_recaptcha_keys
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

emac_public_key, emac_private_key = get_recaptcha_keys()
# print(f'Public key: {emac_public_key}')
# print(f'Private key: {emac_private_key}')

class RecaptchaAuthenticationForm(AuthenticationForm):
    captcha = ReCaptchaField(
        public_key=emac_public_key,
        private_key=emac_private_key,
        widget=ReCaptchaV3(
            attrs={
                'required_score':0.7
            },
            action='login'
        )
    )


class RecaptchaPasswordResetForm(PasswordResetForm):
    captcha = ReCaptchaField(
        public_key=emac_public_key,
        private_key=emac_private_key,
        widget=ReCaptchaV3(
            attrs={
                'required_score':0.7
            },
            action='password_reset_request'
        )
    )


class RecaptchaSetPasswordForm(SetPasswordForm):
    captcha = ReCaptchaField(
        public_key=emac_public_key,
        private_key=emac_private_key,
        widget=ReCaptchaV3(
            attrs={
                'required_score':0.7
            },
            action='set_password_form'
        )
    )

