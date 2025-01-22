from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from emac.recaptcha_auth_forms import RecaptchaAuthenticationForm, RecaptchaPasswordResetForm, RecaptchaSetPasswordForm



TOOLS_SITE_URL = settings.EMAC_PROTOCOL + "://tools." + settings.EMAC_DOMAIN

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('website.urls')),
    re_path(r'^CGP/.*$', RedirectView.as_view(url=TOOLS_SITE_URL + "/CGP")),
    re_path(r'^exovista/.*$', RedirectView.as_view(url=TOOLS_SITE_URL + "/exovista")),
    re_path(r'^EBC/.*$', RedirectView.as_view(url=TOOLS_SITE_URL + "/EBC")),
    re_path(r'^ECI/.*$', RedirectView.as_view(url=TOOLS_SITE_URL + "/ECI")),
    re_path(r'^PyATMOS/.*$', RedirectView.as_view(url=TOOLS_SITE_URL + "/PyATMOS")),
    re_path(r'^REPAST/.*$', RedirectView.as_view(url=TOOLS_SITE_URL + "/REPAST")),
    re_path(r'^tpfplotter/.*$', RedirectView.as_view(url=TOOLS_SITE_URL + "/tpfplotter")),
    path('accounts/login/', LoginView.as_view(form_class=RecaptchaAuthenticationForm), name='login'),
    path('accounts/password_reset/', PasswordResetView.as_view(
         form_class=RecaptchaPasswordResetForm,
         html_email_template_name="registration/html_password_reset_email.html"), name='password_reset'),
    path('accounts/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(form_class=RecaptchaSetPasswordForm), name='password_reset_confirm'),
    path('accounts/', include('django.contrib.auth.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
