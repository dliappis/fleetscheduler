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
    #servicegroups_names = [i for i in fleetdef['servicegroups']]
    for sgroup in fleetdef['servicegroups']:
        process_service_group(servicegroups_name=sgroup,
                              copies=fleetdef['servicegroups'][sgroup]['copies'],
                              env=fleetdef['servicegroups'][sgroup]['env'],
                              container_list=fleetdef['servicegroups'][sgroup]['containers'])

def process_service_group(servicegroups_name, copies, env, container_list):
    for containerdef in container_list:
        service_params = create_unit_from_containerdef(containerdef, container_list[containerdef], env)

        if sys.argv[1] == "start":
            call(["fleet/bin/fleetctl","submit","tmp/%s-%s.service" % (env,containerdef,)])
            call(["fleet/bin/fleetctl","start","tmp/%s-%s.service" % (env,containerdef,)])
        elif sys.argv[1] == "destroy":
            call(["fleet/bin/fleetctl","destroy","tmp/%s-%s.service" % (env,containerdef,)])
 
def create_unit_from_containerdef(originalunitname, container_conf="", env=""):
    if env != "":
        unitname = "%s-%s" % (env,originalunitname)
    else:
        unitname = originalunitname

    unit_filename = "tmp/%s.service" % (unitname,)
    
    # Check if there is already a configuration file
    # if not os.path.isfile(unit_filename):
    cfgfile = open(unit_filename, 'w')

    # Add content to the file
    
    print >>cfgfile, "[Unit]"
    unit_section_clauses = ["Description","After","Requires","BindsTo","Wants","Before"]
    for unitclause in unit_section_clauses:
        try:
            values = container_conf[unitclause.lower()]
            if type(values) == type([]):
                values = ",".join(values)
            print >>cfgfile, "%s = %s" % (unitclause, values)
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
    domainenv = ""
    if "domain" in container_conf:
        domainenv = "-e SERVICE_ID=%s" % (container_conf['domain'],)

    print >>cfgfile, "ExecStart = /usr/bin/docker run --name %s %s %s %s" % (unitname,domainenv,portarray[0],container_conf["image"])
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
