#!/usr/bin/env python

import yaml
import argparse
import sys
import logging
import pdb
import ConfigParser
import os
import json
import urllib2
from subprocess import call

class Unit(object):
    pass


def main():
    if len(sys.argv)!=3:
        logging.warning("Use arguments like start <yamlfile> or destroy <yaml.file")
        sys.exit(1)
    
    fleetdef = ""

    try:
        fp = open(sys.argv[2],'r')
        fleetdef = yaml.load(fp)
    except:
        logging.error("Unable to open or parse file %s" % (sys.argv[1]))

    servicegroups_names = [i for i in fleetdef['servicegroups']]
    for containerdef in fleetdef['servicegroups'][servicegroups_names[0]]['containers']:
        service_params = create_unit_from_containerdef(containerdef, fleetdef['servicegroups'][servicegroups_names[0]]['containers'][containerdef])

        # Check if we need to register the domain locally
        if service_params != None:
            #etcdresponse = urllib2.urlopen("http://172.17.8.101:4001/v1/keys/services/%s" % (service_params["servicename"],) ).read()
        
            #servicekeys = etcdresponse["value"]
            #print servicekeys
            fp = open('domains/domains.txt',"r")
            # File is <domain> <serviceparamname>
            # e.g. www.mytestapp.org hello-world
            domainfilecontents = fp.readlines()
            fp.close()
            domainfilecontents = [i.strip() for i in domainfilecontents]
            domaintable = {}

            try:
                for entries in domainfilecontents:
                    domain,servicename=entries.split(' ')
                    domaintable[domain]=servicename
                domaintable[service_params["domain"]]=service_params["servicename"]
            except ValueError:
                # Empty file
                domaintable[service_params['domain']]=service_params['servicename']
            if len(domainfilecontents)==0:
                #pdb.set_trace()

                # Empty file
                domaintable[service_params['domain']]=service_params['servicename']

            fp = open('domains/domains.txt','w')
            print domaintable
            for domain,servicename in domaintable.iteritems():
                fp.write("%s %s\n" % (domain,servicename) )
            fp.close()
        if sys.argv[1] == "start":
            call(["fleet/bin/fleetctl","submit","tmp/%s.service" % (containerdef,)])
            call(["fleet/bin/fleetctl","start","tmp/%s.service" % (containerdef,)])
        elif sys.argv[1] == "destroy":
            call(["fleet/bin/fleetctl","destroy","tmp/%s.service" % (containerdef,)])
 
def create_unit_from_containerdef(unitname, container_conf=""):
    unit_filename = "tmp/%s.service" % (unitname,)
    
    # Check if there is already a configuration file
    # if not os.path.isfile(unit_filename):
    cfgfile = open(unit_filename, 'w')

    # Add content to the file
    
    # Config = ConfigParser.ConfigParser()
    # Config.optionxform=str
    # Config.add_section('Unit')

    print >>cfgfile, "[Unit]"
    unit_section_clauses = ["Description","After","Requires","BindsTo","Wants","Before"]
    for unitclause in unit_section_clauses:
        try:
            values = container_conf[unitclause.lower()]
            if type(values) == type([]):
                values = ",".join(values)
            print >>cfgfile, "%s = %s" % (unitclause, values)
            # Config.set('Unit', unitclause, container_conf[unitclause.lower()])
        except KeyError:
            continue

    print >>cfgfile, "\n[Service]"
    print >>cfgfile, "TimeoutStartSec = 0"
    print >>cfgfile, "KillMode = none"
    print >>cfgfile, "ExecStartPre = -/usr/bin/docker kill %s" % (unitname,)
    print >>cfgfile, "ExecStartPre = -/usr/bin/docker rm %s" % (unitname,)
    print >>cfgfile, "ExecStartPre = /usr/bin/docker pull %s" % (container_conf["image"],)
    if "ports" in container_conf:
        portarray=["-p %s" % (i,) for i in container_conf["ports"]]
    else:
        # Allow docker to auto assign external ports to exposed ports
        portarray = ["-P"]

    print >>cfgfile, "ExecStart = /usr/bin/docker run --name %s %s %s" % (unitname,portarray[0],container_conf["image"])
    print >>cfgfile, "ExecStop = /usr/bin/docker stop %s" % (unitname,)

    print >>cfgfile, "\n[X-Fleet]"
    x_fleet_section_clauses = [ "MachineID", "MachineOf", "MachineMetadata", "Conflicts", "Global" ]
    for xfleetclause in x_fleet_section_clauses:
        try:
            values = container_conf[xfleetclause.lower()]
            if type(values) == type([]):
                values = ",".join(values)
            print >>cfgfile, "%s = %s" % (xfleetclause, values)
        except KeyError:
            continue
    
    # Config.add_section('Service')
    # Config.set('Service',"TimeoutStartSec",0)
    # Config.set('Service',"KillMode","none")
    # Config.set('Service',"ExecStartPre",'-/usr/bin/docker kill %s' % (unitname,))
    # Config.set('Service',"ExecStartPre",'-/usr/bin/docker rm %s' % (unitname,))
    # Config.set('Service',"ExecStartPre","/usr/bin/docker pull %s" % (unitname,))
    # portarray=["-p %s" % (i,) for i in container_conf["ports"]]
    # Config.set('Service',"ExecStart","/usr/bin/docker run --name %s %s %s" % (unitname,portarray[0],container_conf["image"]))
    # Config.set('Service',"ExecStop","/usr/bin/docker stop %s" % (unitname,))

    # Config.write(cfgfile)
    cfgfile.close()

    ''' 
    Return the container name suffix, which is defined as service name by registrator
    if the container defines a domain
    '''
    if "domain" in container_conf:
        return { "servicename" : container_conf["image"].split('/')[-1], "domain" : container_conf["domain"] }
    else:
        return None
 
## TODO Use argparse instead
def parseargs():
    parser = argparse.ArgumentParser(prog='fleetscheduler', usage='%(prog)s [options]')
    parser.add_argument()

if __name__ == '__main__':
    main()
