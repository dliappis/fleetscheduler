#!/usr/bin/env python

import yaml
import argparse
import sys
import logging
import pdb

from subprocess import call

class Unit(object):
    pass


def main():
    args = parseargs()

    fleetdef = ""

    try:
        fp = open(args.yamldeffile,'r')
        fleetdef = yaml.load(fp)
    except:
        logging.error("Unable to open or parse file %s" % (sys.argv[1]))

    # Has the user limited processing to a specific service group
    if args.servicegroup:
        sgroup = args.servicegroup
        process_service_group(servicegroups_name=sgroup,
                              copies=fleetdef['servicegroups'][sgroup]['copies'],
                              env=fleetdef['servicegroups'][sgroup]['env'],
                              container_list=fleetdef['servicegroups'][sgroup]['containers'],
                              action=args.subparser_name)
    else:
        for sgroup in fleetdef['servicegroups']:
            process_service_group(servicegroups_name=sgroup,
                                  copies=fleetdef['servicegroups'][sgroup]['copies'],
                                  env=fleetdef['servicegroups'][sgroup]['env'],
                                  container_list=fleetdef['servicegroups'][sgroup]['containers'],
                                  action=args.subparser_name)

def process_service_group(servicegroups_name, copies, env, container_list, action=""):
    for containerdef in container_list:
        # TODO parse results for success/fail
        service_params = create_unit_from_containerdef(containerdef, container_list[containerdef], env)

        if action == 'start':
            call(["fleet/bin/fleetctl","submit","tmp/%s-%s.service" % (env,containerdef,)])
            call(["fleet/bin/fleetctl","start","tmp/%s-%s.service" % (env,containerdef,)])
        elif action == "destroy":
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
    parser = argparse.ArgumentParser(prog='fleetscheduler', usage='%(prog)s')
    subparsers = parser.add_subparsers(title="actions", dest="subparser_name")
    parser_start = subparsers.add_parser("start",
                                         help="submit and launch all servicegroups in the yaml file")
    parser_start.add_argument("-s","--servicegroup",
                              help="limit action on specific service group in the yaml file")

    parser_start.add_argument("yamldeffile",
                              help="MANDATORY: the yaml def file")

    parser_destroy = subparsers.add_parser("destroy",
                                           help="destroy all servicesgroups specified in the yaml file")
    parser_destroy.add_argument("-sg","--servicegroup",
                                help="limit action on specific service group in the yaml file")
    parser_destroy.add_argument("yamldeffile",
                                help="MANDATORY: the yaml def file")


    args = parser.parse_args()

    ## TODO this is ugly need to create a proper class to encapsulate things
    return args


if __name__ == '__main__':
    main()
