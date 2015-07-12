#!/bin/bash
export ETCD_MACHINES='http://172.17.8.102:4001'

curl -L http://172.17.8.102:4001/v2/keys/skydns -XPUT -d dir=true
curl -L http://172.17.8.102:4001/v2/keys/skydns/config -XPUT -d value='{"dns_addr":"127.0.0.1:5354","ttl":3600, "domain":"dimitris.io","nameservers": ["8.8.8.8:53","8.8.4.4:53"]}'
skydns

