BANNED_EMAIL_ADDRESSES = ['email@address.tst', 'sample@email.tst', 'was@qualys.com']

def email_address_is_allowed(email_address):

    return (not email_address in BANNED_EMAIL_ADDRESSES)

