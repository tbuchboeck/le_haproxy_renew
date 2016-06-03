#!/usr/bin/python

import os
import datetime
import logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S - ')

le_path='/opt/letsencrypt/'
config_file='/usr/local/etc/le-renew-haproxy.ini'
certs_location='/etc/haproxy/certs/'
http_01_port='54321'
renew_threshold = 7


logging.warning("Starting Let's Encrypt Renewal Script...")

if not os.path.exists(config_file):
    logging.warning('[ERROR] config file does not exist: {0}'.format(config_file))
    exit()

renew = 0
for filename in os.listdir(certs_location):
    tmp = os.popen('openssl x509 -text < %s%s | grep DNS: ' % (certs_location,filename)).read()
    domains = tmp.strip().lstrip("DNS:").split(", DNS:")
    exp = os.popen('openssl x509 -in %s%s -text -noout|grep "Not After"|cut -c 25-' % (certs_location,filename)).read().strip()
    exp2 = datetime.datetime.strptime(exp, '%b %d %H:%M:%S %Y %Z')
    remaining = (exp2 - datetime.datetime.now()).days
    if remaining > renew_threshold:
        logging.warning('The certificate for %s is up to date, no need for renewal (%d days left).',filename.rstrip('.pem'),remaining)
    else:
        logging.warning('The certificate for %s is about to expire soon. Starting Let\'s Encrypt (HAProxy:%s) renewal script...',filename.rstrip('.pem'),http_01_port)
        renew = renew + 1
        le_crypt = "%sletsencrypt-auto certonly --standalone --agree-tos --renew-by-default --config %s --http-01-port %s" % (le_path, config_file, http_01_port)
        for domain in domains:
            logging.warning('Using domain: %s', domain)
            le_crypt = "%s -d %s" % (le_crypt, domain)
        logging.warning('Lets Encrypt: Executing renewal')
        le_exe = os.popen(le_crypt).read().split("\n")
        for line in le_exe:
            logging.warning(line)
        os.popen('cat /etc/letsencrypt/live/%s/fullchain.pem /etc/letsencrypt/live/%s/privkey.pem > %s%s' % (filename.rstrip('.pem'),filename.rstrip('.pem'),certs_location,filename))
        logging.warning('Creating %s with latest certs...',filename)

if renew > 0:
    logging.warning('%s Certificates renewed',renew)
    tmp = os.popen('service haproxy reload').read().strip()
    logging.warning(tmp)
else:
    logging.warning('No certificates renewed so no reload necessary')
