import os

EMAC_ADMIN_USERNAME = None if 'EMAC_ADMIN_USERNAME' not in os.environ else os.environ.get('EMAC_ADMIN_USERNAME')
EMAC_ADMIN_PASSWORD = None if 'EMAC_ADMIN_PASSWORD' not in os.environ else os.environ.get('EMAC_ADMIN_PASSWORD')

EMAC_ADMIN_EMAIL = "REDACTED@nasa.gov" # JPR Redacted Oct. 2024

DEFAULT_FROM_EMAIL = EMAC_ADMIN_EMAIL

EMAIL_HOST = 'REDACTED URL' # JPR Redacted Oct. 2024
EMAIL_PORT = 25
EMAIL_SUBJECT_PREFIX = "[EMAC] "

EMAC_SUBMISSION_SLACK_URL = "REDACTED URL" # JPR Redacted Oct. 2024
EMAC_SUBMISSION_TEST_SLACK_URL = "REDACTED URL" # JPR Redacted Oct. 2024

ADS_DEV_KEY = "REDACTED KEY" # JPR Redacted Oct. 2024

ANALYTICS_SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
ANALYTICS_KEY_FILE = {
  "type": "service_account",
  "project_id": "emac-analytics",
  "private_key_id": "REDACTED KEY", # JPR Redacted Oct. 2024
  "private_key": "REDACTED KEY", # JPR Redacted Oct. 2024
  "client_email": "emac-analytics@emac-analytics.iam.gserviceaccount.com",
  "client_id": "REDACTED KEY", # JPR Redacted Oct. 2024
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "REDACTED URL" # JPR Redacted Oct. 2024
}
ANALYTICS_VIEW_ID = "REDACTED KEY" # JPR Redacted Oct. 2024

EMAC_TWITTER_BOT_ACCESS_TOKEN = "REDACTED KEY" # JPR Redacted Oct. 2024
EMAC_TWITTER_BOT_ACCESS_TOKEN_SECRET = "REDACTED KEY" # JPR Redacted Oct. 2024
EMAC_TWITTER_BOT_CONSUMER_KEY = "REDACTED KEY" # JPR Redacted Oct. 2024
EMAC_TWITTER_BOT_CONSUMER_SECRET = "REDACTED KEY" # JPR Redacted Oct. 2024

YT_KEY = "REDACTED KEY" # JPR Redacted Oct. 2024

SECRET_KEY = "TEST"
RECAPTCHA_PUBLIC_KEY_LVH = "TEST"
RECAPTCHA_PRIVATE_KEY_LVH = "TEST"