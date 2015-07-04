#!/usr/bin/env python

import yaml
import argparse
import sys
import logging
import pdb
import ConfigParser
import os

class Unit(object):
    pass


def main():
    if len(sys.argv)<2:
        logging.warning("You need to supply the yaml conf file as a parameter")
        sys.exit(1)
    
    fleetdef = ""

    try:
        fp = open(sys.argv[1],'r')
        fleetdef = yaml.load(fp)
    except:
        logging.error("Unable to open or parse file %s" % (sys.argv[1]))

    servicegroups_names = [i for i in fleetdef['servicegroups']]
    for containerdef in fleetdef['servicegroups'][servicegroups_names[0]]['containers']:
        unitstring = create_unit_from_containerdef(containerdef, fleetdef['servicegroups'][servicegroups_names[0]]['containers'][containerdef])

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
    unit_section_clauses = ["Description","After","Requires","BindsTo"]
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
    portarray=["-p %s" % (i,) for i in container_conf["ports"]]
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
 
## TODO Use argparse instead
def parseargs():
    parser = argparse.ArgumentParser(prog='fleetscheduler', usage='%(prog)s [options]')
    parser.add_argument()

if __name__ == '__main__':
    main()
