
from twisted.internet import defer
from twisted.python.filepath import FilePath

from lae_util.send_email import send_plain_email


CONFIRMATION_EMAIL_SUBJECT = "Your sign-up to Tahoe-LAFS-on-S3 is complete"

CONFIRMATION_EMAIL_BODY = """Hello %(customer_name)s,

Welcome to the alpha programme!  Please go to

  https://leastauthority.com/howtoconfigure

for instructions on how to set up and configure your Tahoe-LAFS gateway
and start using the service.

The settings for your gateway's tahoe.cfg are:


[client]
introducer.furl = %(external_introducer_furl)s

shares.needed = 1
shares.happy = 1
shares.total = 1

[storage]
enabled = false


(The introducer.furl setting should be on one line.)

We hope you enjoy using our service and find it useful.

--\x20
The Least Authority Enterprises team
"""

SENDER_DOMAIN = "leastauthority.com"
FROM_EMAIL = "info@leastauthority.com"
FROM_ADDRESS = "Least Authority Enterprises <%s>" % (FROM_EMAIL,)
USER_AGENT = "Least Authority Enterprises e-mail sender"

SMTP_HOST = "smtp.googlemail.com"
SMTP_PORT = 25
SMTP_USERNAME = FROM_EMAIL

PGP_NOTIFICATION_EMAIL = "davidsarah@leastauthority.com"


def send_signup_confirmation(customer_name, customer_email, external_introducer_furl, customer_keyinfo, stdout, stderr, password_path='../smtppassword'):
    password = FilePath(password_path).getContent().strip()

    content = CONFIRMATION_EMAIL_BODY % {
               "customer_name": customer_name,
               "external_introducer_furl": external_introducer_furl,
              }
    headers = {
               "From": FROM_ADDRESS,
               "Subject": CONFIRMATION_EMAIL_SUBJECT,
               "User-Agent": USER_AGENT,
              }

    d = defer.succeed(None)
    if customer_keyinfo:
        print >>stdout, "Notifying one of our staff to send the confirmation e-mail to <%s>..." % (customer_email,)
        # Don't send the introducer furl; they're supposed to log in to the automation server to get it.
        headers["Subject"] = "Sign-up with PGP key"
        d.addCallback(lambda ign:
                      send_plain_email(SMTP_HOST, SMTP_USERNAME, password, FROM_EMAIL, PGP_NOTIFICATION_EMAIL,
                                       "Please send a confirmation e-mail to %r at %r." % (customer_name, customer_email),
                                       headers, SENDER_DOMAIN, SMTP_PORT))
    else:
        print >>stdout, "Sending confirmation e-mail to <%s>..." % (customer_email,)
        d.addCallback(lambda ign:
                      send_plain_email(SMTP_HOST, SMTP_USERNAME, password, FROM_EMAIL, customer_email,
                                       content, headers, SENDER_DOMAIN, SMTP_PORT))

    def _sent(ign):
        if customer_keyinfo:
            print >>stdout, "Notification sent."
        else:
            print >>stdout, "Confirmation e-mail sent."
    def _error(f):
        print >>stdout, "Sending of e-mail failed."
        print >>stdout, "Please contact <info@leastauthority.com> to make sure that we have your correct e-mail address."
        print >>stderr, str(f)
        return f
    d.addCallbacks(_sent, _error)
    return d
