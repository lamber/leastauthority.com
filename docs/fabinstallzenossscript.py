"""
"""

from cStringIO import StringIO
import simplejson

from fabric import api
from fabric.context_managers import cd

class NotListeningError(Exception):
    pass


NGINXCONFIGFILESTRING = """server {
    listen 443 default ssl;
    server_name lambda4.leastauthority.com;
    ssl on;
    ssl_certificate /home/zenoss/keys/server.crt;
    ssl_certificate_key /home/zenoss/keys/server.key;
    ssl_session_timeout 20m;
    ssl_protocols SSLv3 TLSv1;
    ssl_ciphers RSA:HIGH;
    ssl_prefer_server_ciphers on;

    access_log /home/zenoss/logs/server.log;

    location / {
        rewrite ^(.*)$ /VirtualHostBase/https/lambda4.leastauthority.com:443$1 break;
        proxy_pass http://127.0.0.1:8080;
    }
}"""

SERVERCERTIFICATESTRING = """-----BEGIN CERTIFICATE-----
MIIE1zCCA7+gAwIBAgIDA8pDMA0GCSqGSIb3DQEBBQUAMDwxCzAJBgNVBAYTAlVT
MRcwFQYDVQQKEw5HZW9UcnVzdCwgSW5jLjEUMBIGA1UEAxMLUmFwaWRTU0wgQ0Ew
HhcNMTExMDMxMDM0NTI4WhcNMTIxMTAxMTk0NDE0WjCB6zEpMCcGA1UEBRMgWnlV
RXAzOXhwVkoyUDVZOXk4ZVJjMUZ6ZWh0WUFaV3oxCzAJBgNVBAYTAlVTMRswGQYD
VQQKExJsZWFzdGF1dGhvcml0eS5jb20xEzARBgNVBAsTCkdUMjUzMzIyMDYxMTAv
BgNVBAsTKFNlZSB3d3cucmFwaWRzc2wuY29tL3Jlc291cmNlcy9jcHMgKGMpMTEx
LzAtBgNVBAsTJkRvbWFpbiBDb250cm9sIFZhbGlkYXRlZCAtIFJhcGlkU1NMKFIp
MRswGQYDVQQDExJsZWFzdGF1dGhvcml0eS5jb20wggEiMA0GCSqGSIb3DQEBAQUA
A4IBDwAwggEKAoIBAQC+oljOXgQiZRzeN/9YwYb+fvm8r+8sUDwlCqNmbuI0EtqQ
29Guq0ZaUkgEoWphza/CabRhvULjJs5ulXnKfTp3f1vQnXli3it2dF6IPmSVxPNo
jrmCqgQq318FVrVhdveE3fswguOmVmkYDW3Jr0oqkbqAPDlL7h4QEMzZWHKTRTlR
ViajgxdKO/dOLUNuTXZug07BltLjDRpYU0KvkykfqXwdaoa0z6UJr5KOGN7aI6wL
gySLS9au3vcJiu6ErQ2LEYy2j6S8Ioti5a4H8wn85ofOBmvUa94LoeUnhuPEiWPF
eUXfhXYCVnsGiMbxvCf0hV9SyPjqqyDXUDtNciJJAgMBAAGjggEwMIIBLDAfBgNV
HSMEGDAWgBRraT1qGEJK3Y8CZTn9NSSGeJEWMDAOBgNVHQ8BAf8EBAMCBaAwHQYD
VR0lBBYwFAYIKwYBBQUHAwEGCCsGAQUFBwMCMB0GA1UdEQQWMBSCEmxlYXN0YXV0
aG9yaXR5LmNvbTBDBgNVHR8EPDA6MDigNqA0hjJodHRwOi8vcmFwaWRzc2wtY3Js
Lmdlb3RydXN0LmNvbS9jcmxzL3JhcGlkc3NsLmNybDAdBgNVHQ4EFgQUQINvd3gn
U0OLHaOhX5RlmhDyhRUwDAYDVR0TAQH/BAIwADBJBggrBgEFBQcBAQQ9MDswOQYI
KwYBBQUHMAKGLWh0dHA6Ly9yYXBpZHNzbC1haWEuZ2VvdHJ1c3QuY29tL3JhcGlk
c3NsLmNydDANBgkqhkiG9w0BAQUFAAOCAQEAFsJx47zzl77KKl5gaj1+hEdfG5om
HedkgUPsaW3lBrCFZax5PG+fMb6wtt/SoCCeaV7S7FrXhqcFFOtXEYacWU+5WvxT
UzmZZGGVO/egPNa9dIIbxQ7wNOpa7b522659r/nrTz4wbvPok+CNOagfOcf1kS20
X2ZXJlDeK3yfQwKK7raH9wzLSd2x0cMcvzzBxt1vn9bEObixc2bySzD/7BCQ0Zy8
/K74eFue25wiJnJewAvBQoPm2bpsWMbqcvVHWerwZdYEky+9zV7MQz9AnEI7GXcz
tI6HfFFO1pdPMBrb8FPEMFiFp/ai5pbXYxVcnVxlLMGmWS+uA1+9lJ0xFw==
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIID1TCCAr2gAwIBAgIDAjbRMA0GCSqGSIb3DQEBBQUAMEIxCzAJBgNVBAYTAlVT
MRYwFAYDVQQKEw1HZW9UcnVzdCBJbmMuMRswGQYDVQQDExJHZW9UcnVzdCBHbG9i
YWwgQ0EwHhcNMTAwMjE5MjI0NTA1WhcNMjAwMjE4MjI0NTA1WjA8MQswCQYDVQQG
EwJVUzEXMBUGA1UEChMOR2VvVHJ1c3QsIEluYy4xFDASBgNVBAMTC1JhcGlkU1NM
IENBMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAx3H4Vsce2cy1rfa0
l6P7oeYLUF9QqjraD/w9KSRDxhApwfxVQHLuverfn7ZB9EhLyG7+T1cSi1v6kt1e
6K3z8Buxe037z/3R5fjj3Of1c3/fAUnPjFbBvTfjW761T4uL8NpPx+PdVUdp3/Jb
ewdPPeWsIcHIHXro5/YPoar1b96oZU8QiZwD84l6pV4BcjPtqelaHnnzh8jfyMX8
N8iamte4dsywPuf95lTq319SQXhZV63xEtZ/vNWfcNMFbPqjfWdY3SZiHTGSDHl5
HI7PynvBZq+odEj7joLCniyZXHstXZu8W1eefDp6E63yoxhbK1kPzVw662gzxigd
gtFQiwIDAQABo4HZMIHWMA4GA1UdDwEB/wQEAwIBBjAdBgNVHQ4EFgQUa2k9ahhC
St2PAmU5/TUkhniRFjAwHwYDVR0jBBgwFoAUwHqYaI2J+6sFZAwRfap9ZbjKzE4w
EgYDVR0TAQH/BAgwBgEB/wIBADA6BgNVHR8EMzAxMC+gLaArhilodHRwOi8vY3Js
Lmdlb3RydXN0LmNvbS9jcmxzL2d0Z2xvYmFsLmNybDA0BggrBgEFBQcBAQQoMCYw
JAYIKwYBBQUHMAGGGGh0dHA6Ly9vY3NwLmdlb3RydXN0LmNvbTANBgkqhkiG9w0B
AQUFAAOCAQEAq7y8Cl0YlOPBscOoTFXWvrSY8e48HM3P8yQkXJYDJ1j8Nq6iL4/x
/torAsMzvcjdSCIrYA+lAxD9d/jQ7ZZnT/3qRyBwVNypDFV+4ZYlitm12ldKvo2O
SUNjpWxOJ4cl61tt/qJ/OCjgNqutOaWlYsS3XFgsql0BYKZiZ6PAx2Ij9OdsRu61
04BqIhPSLT90T+qvjF+0OJzbrs6vhB6m9jRRWXnT43XcvNfzc9+S7NIgWW+c+5X4
knYYCnwPLKbK3opie9jzzl9ovY8+wXS7FXI6FoOpC+ZNmZzYV+yoAVHHb1c0XqtK
LEL2TxyJeN4mTvVvk0wVaydWTQBUbHq3tw==
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIDfTCCAuagAwIBAgIDErvmMA0GCSqGSIb3DQEBBQUAME4xCzAJBgNVBAYTAlVT
MRAwDgYDVQQKEwdFcXVpZmF4MS0wKwYDVQQLEyRFcXVpZmF4IFNlY3VyZSBDZXJ0
aWZpY2F0ZSBBdXRob3JpdHkwHhcNMDIwNTIxMDQwMDAwWhcNMTgwODIxMDQwMDAw
WjBCMQswCQYDVQQGEwJVUzEWMBQGA1UEChMNR2VvVHJ1c3QgSW5jLjEbMBkGA1UE
AxMSR2VvVHJ1c3QgR2xvYmFsIENBMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEA2swYYzD99BcjGlZ+W988bDjkcbd4kdS8odhM+KhDtgPpTSEHCIjaWC9m
OSm9BXiLnTjoBbdqfnGk5sRgprDvgOSJKA+eJdbtg/OtppHHmMlCGDUUna2YRpIu
T8rxh0PBFpVXLVDviS2Aelet8u5fa9IAjbkU+BQVNdnARqN7csiRv8lVK83Qlz6c
JmTM386DGXHKTubU1XupGc1V3sjs0l44U+VcT4wt/lAjNvxm5suOpDkZALeVAjmR
Cw7+OC7RHQWa9k0+bw8HHa8sHo9gOeL6NlMTOdReJivbPagUvTLrGAMoUgRx5asz
PeE4uwc2hGKceeoWMPRfwCvocWvk+QIDAQABo4HwMIHtMB8GA1UdIwQYMBaAFEjm
aPkr0rKV10fYIyAQTzOYkJ/UMB0GA1UdDgQWBBTAephojYn7qwVkDBF9qn1luMrM
TjAPBgNVHRMBAf8EBTADAQH/MA4GA1UdDwEB/wQEAwIBBjA6BgNVHR8EMzAxMC+g
LaArhilodHRwOi8vY3JsLmdlb3RydXN0LmNvbS9jcmxzL3NlY3VyZWNhLmNybDBO
BgNVHSAERzBFMEMGBFUdIAAwOzA5BggrBgEFBQcCARYtaHR0cHM6Ly93d3cuZ2Vv
dHJ1c3QuY29tL3Jlc291cmNlcy9yZXBvc2l0b3J5MA0GCSqGSIb3DQEBBQUAA4GB
AHbhEm5OSxYShjAGsoEIz/AIx8dxfmbuwu3UOx//8PDITtZDOLC5MH0Y0FWDomrL
NhGc6Ehmo21/uBPUR/6LWlxz/K7ZGzIZOKuXNBSqltLroxwUCEm2u+WR74M26x1W
b8ravHNjkOR/ez4iyz0H7V84dJzjA1BOoa+Y7mHyhD8S
-----END CERTIFICATE-----"""

SERVERKEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAvqJYzl4EImUc3jf/WMGG/n75vK/vLFA8JQqjZm7iNBLakNvR
rqtGWlJIBKFqYc2vwmm0Yb1C4ybObpV5yn06d39b0J15Yt4rdnReiD5klcTzaI65
gqoEKt9fBVa1YXb3hN37MILjplZpGA1tya9KKpG6gDw5S+4eEBDM2Vhyk0U5UVYm
o4MXSjv3Ti1Dbk12boNOwZbS4w0aWFNCr5MpH6l8HWqGtM+lCa+Sjhje2iOsC4Mk
i0vWrt73CYruhK0NixGMto+kvCKLYuWuB/MJ/OaHzgZr1GveC6HlJ4bjxIljxXlF
34V2AlZ7BojG8bwn9IVfUsj46qsg11A7TXIiSQIDAQABAoIBAQCklHyfDcP7/deC
ck3dTpdBOFZbdHjEhTCnuht/39MiqfRQg7bvWacPa2IJvWGetnk7Gw9EIqWQfnxS
NHJFQwArEqUt4gZeOPjE94p1jYhBVRvf9PhrumSGrvnWHhnR32eqKgsmwpnPjWKG
BXH3YYJiZhXhiBzfVOBXdmmkaxvfz7GKo8uWbsNKu9naO6dQSmWM7WOQ5NLCtBgW
rFEx2G5W/BUxvyi5Zr2RGrTuemW0PQq/bpnOcmj1/NJO2bw7ASCdsG0PMWyDcjEZ
tnPcT6/8HKz6ufvZbmFxogkJFVdr8J6CXpPJEz5D4d7crKum+tkb+WPJASc0Qc2/
xRDJgccRAoGBAOtXj6JFzuTIC1rDikr9blVOpUSHB1347QOZe6vR7DpRfSKisqZL
BMupg3iukirHkiadWnlSSA9PJxQhm1PL0pEl+V8I4K7Rcy5wIMfOlzaTrwNeTFTF
9n3hCAVI2Fw9t0Tcda6fKrKy2NtvkYGuLA5NeDvOL2PDuPQIXCEOZzDrAoGBAM9e
JHSAembXi5IbhkcYooKM7quHPbC2n3Oq5WF79+dVWzklyBA58WcxxF7lA1PHH1gF
BRmisIeKHU7F7dpezvWDjJL1RNoPP9bN7E9qslWOemvzwisYCl2dT2ybINX1b+0y
54K6we0RMiQl49mCJ0rwgDoKG0q+Z+UrGOAs5YybAoGAJvvSJyc5JlycxOQvPEzO
wgLNDZTwe3iIilgaTFPxtZdaCyq4PSOgH7xsssj4HW4Bn7PhEMe4eBC8gHEwsajJ
sJGBxWRLE6pOUhrw0yg9lCTSkNRGAKTqN9/W3Ek8zcrLWPTL6akkAYXutiq9B6Y6
VgQvLnjxEK2TLZlU6YThQxECgYEAwwy+JYcjmtBry8ZwCze0xC9j35uZ/zoHyXiZ
wZQlnka/Q4WyJPEbjAFXwBqRgp/tb5FpNq+8dAEJiCrMi3ZaHLzb4O8rECD/30Ba
YmjtzWPy6s+hd39pYJyzNGjF/fqaiPY0pNadyis+ipnJM7Ik22xUcENJYIiwmPJs
t5ADarkCgYEA6xPntP0hU4PphJIfihDgNjZW2JhYA1CjcdgQS0TDH5Ww9QATTuji
7pGc6tf+cpSdlEe/96WwjBJ81px66KeXI62UQHjrUqYmHQ75GK7bwHNivZbVuL/h
B9jMZYHUHEIZ+fIa1i7zWlV/UBjW+yMdKwN3dxFo0HCTcrCa+LJaAYQ=
-----END RSA PRIVATE KEY-----"""

NGINXCERTFILENAME = """/home/nginx/keys/server.crt"""
NGINXKEYFILENAME = """/home/nginx/keys/server.key"""
NGINXLOGFILENAME = """/home/zenoss/logs"""
NGINXCONFIGFILENAME = """/etc/nginx/sites-enabled/default"""
# The default 'pty=True' behaviour is unsafe because, when we are invoked via flapp,
# we don't want the flapp client to be able to influence the ssh remote command's stdin.
# pty=False will cause fabric to echo stdin, but that's fine.

def run(argstring, **kwargs):
    return api.run(argstring, pty=False, **kwargs)

def sudo(argstring, **kwargs):
    return api.sudo(argstring, pty=False, **kwargs)

def set_host_and_key(public_host, ssh_private_keyfile, username="ubuntu"):
    api.env.host_string = '%s@%s' % (username, public_host)
    api.env.reject_unknown_hosts = False  # FIXME allows MITM attacks
    api.env.key_filename = ssh_private_keyfile
    api.env.abort_on_prompts = True

    try:
        whoami = run('whoami')
    except SystemExit:
        # fabric stupidly aborts if the host is not listening for ssh connections
        # and this is why SystemExit needs to be catchable, zooko ;-)
        raise NotListeningError()
    assert whoami.strip() == username, (whoami, username)

def sudo_apt_get(argstring):
    sudo('apt-get %s' % argstring)

def sudo_easy_install(argstring):
    sudo('easy_install %s' % argstring)

def write(value, remote_path, use_sudo=False, mode=None):
    # There's an incompletely understood interaction between use_sudo and mode.
    # It can result in cryptic remote file names when use_sudo is True and
    # mode is not None.
    return api.put(StringIO(value), remote_path, use_sudo=use_sudo, mode=mode)

def create_account(account_name, account_pubkey, stdout, stderr):
    print >>stdout, "Setting up %s account..." % (account_name,)
    sudo('adduser --disabled-password --gecos "" %s || echo Assuming that %s already exists.' % (2*(account_name,)) )
    sudo('mkdir -p /home/%s/.ssh/' % (account_name,) )
    sudo('chown %s:%s /home/%s/.ssh' % (3*(account_name,)) )
    sudo('chmod u+w /home/%s/.ssh/authorized_keys || echo Assuming there is no existing authorized_keys file.' % (account_name,) )
    if account_pubkey is None:
        sudo('cp /home/ubuntu/.ssh/authorized_keys /home/customer/.ssh/authorized_keys')
    else:
        write(account_pubkey, '/home/%s/.ssh/authorized_keys' % (account_name,), use_sudo=True)
    sudo('chown %s:%s /home/%s/.ssh/authorized_keys' % (3*(account_name,)))
    sudo('chmod 400 /home/%s/.ssh/authorized_keys' % (account_name,))
    sudo('chmod 700 /home/%s/.ssh/' % (account_name,))

def install_nginxandzenoss():
    set_host_and_key(public_host, admin_privkey_path)

    create_account('nginx', None, stdout, stderr)
    with cd('/home/nginx'):
        run('mkdir -p /home/nginx/keys')
        write(SERVERCERTIFICATESTRING, NGINXCERTFILENAME)
        write(SERVERKEY, NGINXKEYFILENAME)
        run('chown nginx:nginx ./*')
        run('chmod 400 ./*')
    print >>stdout, "Updating server..."
    sudo_apt_get('update')
    sudo_apt_get('upgrade -y')
    sudo_apt_get('install -y nginx')

    run('mkdir temp_for_zenossdeb')
    with cd('temp_for_zenossdeb'):
        run('wget http://dev.zenoss.org/deb/dists/main/stable/binary-i386/zenoss-stack_3.2.1_i386.deb')
        run('dpkg -i zenoss-stack_3.2.1_i386.deb')

    #XXX Below here are left--overs...
    run('tar -xzvf txAWS-0.2.1.post2.tar.gz')



    create_account('monitor', monitor_pubkey, stdout, stderr)

    # check that creating the monitor account worked
    set_host_and_key(public_host, monitor_privkey_path, username="monitor")

    # do the rest of the installation as 'customer', customer doesn't actually have its own ssh keys
    # I don't know if creating one would be useful.XXX
    set_host_and_key(public_host, admin_privkey_path, username="customer")

    print >>stdout, "Getting Tahoe-LAFS..."
    run('rm -rf /home/customer/LAFS_source')
    run('darcs get --lazy https://tahoe-lafs.org/source/tahoe/ticket999-S3-backend LAFS_source')

    print >>stdout, "Building Tahoe-LAFS..."
    with cd('/home/customer/LAFS_source'):
        run('python ./setup.py build')

    print >>stdout, "Creating introducer and storage server..."
    run('mkdir -p introducer storageserver')
    run('LAFS_source/bin/tahoe create-introducer introducer || echo Assuming that introducer already exists.')
    run('LAFS_source/bin/tahoe create-node storageserver || echo Assuming that storage server already exists.')

    print >>stdout, "Finished server installation."


def set_up_reboot(stdout, stderr):
    print >>stdout, "Setting up introducer and storage server to run on reboot..."
    write(RESTART_SCRIPT, '/home/customer/restart.sh', mode=0750)
    write('@reboot /home/customer/restart.sh\n', '/home/customer/ctab')
    run('crontab /home/customer/ctab')