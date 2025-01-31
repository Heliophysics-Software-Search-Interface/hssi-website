import os

ADMIN_USERNAME = None if 'ADMIN_USERNAME' not in os.environ else os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = None if 'ADMIN_PASSWORD' not in os.environ else os.environ.get('ADMIN_PASSWORD')

ADMIN_EMAIL = "Update@This.Email"

DEFAULT_FROM_EMAIL = ADMIN_EMAIL

EMAIL_HOST = 'PLACEHOLDER URL'
EMAIL_PORT = 25
EMAIL_SUBJECT_PREFIX = "[HSSI] "

SUBMISSION_SLACK_URL = "PLACEHOLDER URL"
SUBMISSION_TEST_SLACK_URL = "PLACEHOLDER URL"

ADS_DEV_KEY = "PLACEHOLDER ADS KEY"

ANALYTICS_SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
ANALYTICS_KEY_FILE = {
  "type": "service_account",
  "project_id": "PLACEHOLDER id",
  "private_key_id": "PLACEHOLDER KEY",
  "private_key": "PLACEHOLDER KEY",
  "client_email": "PLACEHOLDER analytics email",
  "client_id": "PLACEHOLDER KEY",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "PLACEHOLDER URL"
}
ANALYTICS_VIEW_ID = "PLACEHOLDER KEY"

HSSI_TWITTER_BOT_ACCESS_TOKEN = "PLACEHOLDER KEY"
HSSI_TWITTER_BOT_ACCESS_TOKEN_SECRET = "PLACEHOLDER KEY"
HSSI_TWITTER_BOT_CONSUMER_KEY = "PLACEHOLDER KEY"
HSSI_TWITTER_BOT_CONSUMER_SECRET = "PLACEHOLDER KEY"

YT_KEY = "PLACEHOLDER KEY"

SECRET_KEY = "TEST"
RECAPTCHA_PUBLIC_KEY_LVH = "TEST"
RECAPTCHA_PRIVATE_KEY_LVH = "TEST"