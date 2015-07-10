#!/usr/bin/env python
import urllib2
import json
import sys
import pdb
import time

'''
{"action":"delete","node":{"key":"/services/hello-world/core-01:helloworld:80","modifiedIndex":69852,"createdIndex":69722},"prevNode":{"key":"/services/hello-world/core-01:helloworld:80","value":"172.17.8.101:32770","modifiedIndex":69722,"createdIndex":69722}}

{"action":"set","node":{"key":"/services/hello-world/core-01:helloworld:80","value":"172.17.8.101:32771","modifiedIndex":69972,"createdIndex":69972}}
'''

fp = open('domains/domains.txt','r')
domainfilecontents = fp.readlines()
domainfilecontents = [i.strip() for i in domainfilecontents] # Remove LF at end of each line
fp.close()

domaintable = {}

# Parse columns of text file 'domains.txt'
try:
    for entries in domainfilecontents:
        domain,servicename=entries.split(' ')
        domaintable[servicename]=domain
except ValueError:
    # Empty file
    sys.exit(1)
if len(domainfilecontents)==0:
    sys.exit(1)

etcdresponse = urllib2.urlopen("http://172.17.8.101:4001/v2/keys/services/?wait=true&recursive=true" ).read()

jsonresponse = json.loads(etcdresponse)
time.sleep(8)
etcdstatus = urllib2.urlopen("http://172.17.8.101:4001/v2/keys/services?recursive=true" ).read()
json_etcd_dir = json.loads(etcdstatus)

current_etcd_struct = {}

print "Updated hosttable:"
#pdb.set_trace()
for itr in json_etcd_dir["node"]["nodes"]:
    servicekey = itr["key"].split('/')[-1] # e.g. /service/redis --> redis
    current_etcd_struct[servicekey] = {}
    #print itr
    try:
        for children in itr["nodes"]:
            uniqkey = children["key"]
            uniqvalue = children["value"]
            current_etcd_struct[servicekey][uniqkey]=uniqvalue

            if servicekey in domaintable.keys():
                #print "etcd key: %s identified inside %s" % (servicekey,domaintable.keys())
                print "Domain %s = %s" % (domaintable[servicekey], uniqvalue)
    except:
        # Entry removed
        continue
