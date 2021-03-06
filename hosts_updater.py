#!/usr/bin/env python
from subprocess import check_output
from subprocess import call
import urllib2
import random
import time
import string
import pdb
import re
import httplib

def update_hosts_file():

    # Assume that skydns2 is running on port 5354
    allrecords = check_output(["dig","@127.0.0.1","-p","5354","+noall","+answer","+additional","*.dimitris.io","SRV"]).split('\n')

    dnsdict = {}

    for i in allrecords:
        if 'SRV' in i:
            domainname = re.split('\t| ',i)[-1]
            portnum = re.split('\t| ',i)[-2]
            try:
                dnsdict[domainname]['port'] = portnum
            except KeyError:
                dnsdict[domainname] = {'port': portnum }
        else:
            domainname = re.split('\t| ',i)[0]
            ipaddr = re.split('\t| ',i)[-1]
            try:
                dnsdict[domainname]['host'] = ipaddr
            except KeyError:
                dnsdict[domainname] = {'host' : ipaddr}


    random_filename_suffix = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))

    backup_hosts = call(["cp","/etc/hosts","/etc/hosts.back-%s" % (random_filename_suffix,)])

    hostsfile = ""
    newhostsfile = []
    with open('/etc/hosts','r') as p:
        hostsfile = p.readlines()

    appendnewcontentflag = False
    for i in hostsfile:
        if re.search('''## skydns2''',i):
            newhostsfile.append(i)
            appendnewcontentflag = True
            break
        newhostsfile.append(i)

    if appendnewcontentflag:
        for fqdn,fqdnvals in dnsdict.iteritems():
            # Our dns name has an unwanted service name (docker container name)
            # as the second . element. This is because of gliderlabs/registrator.
            # Remove it
            newfqdn = fqdn.split('.')
            newdottedfqdn = '.'.join([newfqdn[0]]+newfqdn[2:-1])
            try:
                #newhostsfile.append("%s\t%s:%s\n" % (newdottedfqdn,fqdnvals['host'],fqdnvals['port']))
                newhostsfile.append("%s\t%s\n" % (fqdnvals['host'],newdottedfqdn))
            except KeyError:
                continue

    # Warning! Writing new hosts file here!

    with open('/etc/hosts','w') as fp:
        [fp.write(i) for i in newhostsfile]

    print "Updated hosts file with: "
    print dnsdict


if __name__ == '__main__':
    while True:
        update_hosts_file()
        # The following is a blocking operation
        try:
            etcdresponse = urllib2.urlopen("http://172.17.8.101:4001/v2/keys/skydns/?wait=true&recursive=true" ).read()
        except httplib.IncompleteRead:
            continue
        time.sleep(6)


