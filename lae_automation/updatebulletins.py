
from twisted.internet import defer

from lae_util.send_email import send_plain_email, FROM_EMAIL, FROM_ADDRESS, PGP_NOTIFICATION_EMAIL


bulletinsubject_01 = "LAE Enterprises Now Provides Server Monitoring Data"
bulletinbody_01 = """Hello %(customer_name)s

  Least Authority Enterprises prides itself on a maximally transparent
  operations model.  In keeping with this philosophy we are pleased to
  provide public access to server data.  The public may view current server
  operations by following the instructions on our website at:

  https://leastauthority.com/support

You can monitor the behavior of your specific server by following this link:

  https://monitoring.leastauthority.com/server/%(publichost)s

Log in with username "guest" and password "guest", then click on the "Graphs"
button in the left-hand menu.

We hope our commitment to transparency gives you confidence that you know how
your data is being handled.  We look forward to providing more insight in the
future and welcome suggestions as to how we can better keep you informed.

--\x20
The Least Authority Enterprises team
"""


def send_bulletin(publichost, customer_name, customer_email, customer_keyinfo, stdout, stderr):
    # TODO: the name is URL-escaped UTF-8. It should be OK to unescape it since the email is plain text,
    # but I'm being cautious for now since I haven't reviewed email.mime.text.MIMEText to make sure that's safe.
    content = bulletinbody_01 % {
               "customer_name": customer_name,
               "publichost": publichost
              }
    headers = {
               "From": FROM_ADDRESS,
               "Subject": bulletinsubject_01,
               }

    d = defer.succeed(None)
    if customer_keyinfo:
        print >>stdout, "Notifying one of our staff to send an update bulletin e-mail to <%s>..." % (customer_email,)
        headers["Subject"] = "PGP key enabled: "+bulletinsubject_01
        d.addCallback(lambda ign:
                      send_plain_email(FROM_EMAIL, PGP_NOTIFICATION_EMAIL,
                                       "Please send an update bulletin, e-mail to %r at %r." % (customer_name, customer_email),
                                       headers))
    else:
        print >>stdout, "Sending update bulletin e-mail to <%s>..." % (customer_email)
        d.addCallback(lambda ign:
                      send_plain_email(FROM_EMAIL, customer_email, content, headers))

    def _sent(ign):
        if customer_keyinfo:
            print >>stdout, "PGP Encrypted Bulletin sent."
        else:
            print >>stdout, "Bulletin sent."
    def _error(f):
        print >>stdout, "Sending of bulletin e-mail failed."
        print >>stderr, str(f)
        return f
    d.addCallbacks(_sent, _error)
    return d
