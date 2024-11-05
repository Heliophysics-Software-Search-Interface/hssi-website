from django.conf import settings

import tweepy

BANNED_EMAIL_ADDRESSES = ['email@address.tst', 'sample@email.tst', 'was@qualys.com']

def email_address_is_allowed(email_address):

    return (not email_address in BANNED_EMAIL_ADDRESSES)

def authenticate_to_twitter():

    auth = tweepy.OAuthHandler(settings.EMAC_TWITTER_BOT_CONSUMER_KEY, settings.EMAC_TWITTER_BOT_CONSUMER_SECRET)
    auth.set_access_token(settings.EMAC_TWITTER_BOT_ACCESS_TOKEN, settings.EMAC_TWITTER_BOT_ACCESS_TOKEN_SECRET)

    api = tweepy.API(auth)

    return api

twitter_api = authenticate_to_twitter()


def get_recaptcha_keys():

    # default to lvh.me dev environment
    public_key = settings.RECAPTCHA_PUBLIC_KEY_LVH
    private_key = settings.RECAPTCHA_PRIVATE_KEY_LVH

    if settings.EMAC_DOMAIN.startswith("emac.gsfc"):

        public_key = settings.RECAPTCHA_PUBLIC_KEY_PROD
        private_key = settings.RECAPTCHA_PRIVATE_KEY_PROD

    elif settings.EMAC_DOMAIN.startswith("emac-dev"):

        public_key = settings.RECAPTCHA_PUBLIC_KEY_DEV
        private_key = settings.RECAPTCHA_PRIVATE_KEY_DEV
    
    return public_key, private_key

