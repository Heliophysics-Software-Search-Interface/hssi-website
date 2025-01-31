import os

ADMIN_USERNAME = None if 'ADMIN_USERNAME' not in os.environ else os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = None if 'ADMIN_PASSWORD' not in os.environ else os.environ.get('ADMIN_PASSWORD')

ADMIN_EMAIL = "REDACTED@nasa.gov"

DEFAULT_FROM_EMAIL = ADMIN_EMAIL

EMAIL_HOST = 'REDACTED URL'
EMAIL_PORT = 25
EMAIL_SUBJECT_PREFIX = "[HSSI] "

SUBMISSION_SLACK_URL = "REDACTED URL"
SUBMISSION_TEST_SLACK_URL = "REDACTED URL"

ADS_DEV_KEY = "REDACTED KEY"

ANALYTICS_SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
ANALYTICS_KEY_FILE = {
  "type": "service_account",
  "project_id": "placholder id",
  "private_key_id": "REDACTED KEY",
  "private_key": "REDACTED KEY",
  "client_email": "placeholder analytics address",
  "client_id": "REDACTED KEY",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "REDACTED URL"
}
ANALYTICS_VIEW_ID = "REDACTED KEY"

HSSI_TWITTER_BOT_ACCESS_TOKEN = "REDACTED KEY"
HSSI_TWITTER_BOT_ACCESS_TOKEN_SECRET = "REDACTED KEY"
HSSI_TWITTER_BOT_CONSUMER_KEY = "REDACTED KEY"
HSSI_TWITTER_BOT_CONSUMER_SECRET = "REDACTED KEY"

YT_KEY = "REDACTED KEY"