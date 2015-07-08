# fleetscheduler
Scheduler and orchestrator for fleet

# Quick setup

1. Compile + run skydns2:

go get github.com/skynetservices/skydns
cd <gosourcepath> skydns2
go build -v
export ETCD_MACHINES='http://172.17.8.102:4001' # use any coreos ip here

On a coreos machine or with etcd api calls create a skydns2 conf:

etcdctl set /skydns/config '{"dns_addr":"127.0.0.1:5354","ttl":3600, "domain":"dimitris.io","nameservers": ["8.8.8.8:53","8.8.4.4:53"]}'

This will force skydns to look for auto registered (gliderlabs/registrator) data under /skydns/local/io/dimitris

2. Use the fleet unit file to start gliderlabs/registrator:
```ini
[Unit]
Description=Gliderlabs registrator for skydns2
Requires=docker.service etcd.service
After=docker.service etcd.service

[Service]
Restart=always
RestartSec=5s
TimeoutStartSec=120
TimeoutStopSec=25

EnvironmentFile=/etc/environment

# remove old container
ExecStartPre=/bin/sh -c "docker ps -a | grep %p 1>/dev/null && docker rm %p || true"

# Start the container
ExecStart=/bin/sh -c "\
  /usr/bin/docker run \
    --rm \
    --name=%p \
    -v /var/run/docker.sock:/tmp/docker.sock \
    -h %H \
    gliderlabs/registrator \
    -ip ${COREOS_PRIVATE_IPV4} \
    skydns2://${COREOS_PRIVATE_IPV4}:4001/dimitris.io"

ExecStop=/usr/bin/docker stop %p


[X-Fleet]
Global=true
```

5. Ensure that your app unit files have SERVICE_ID=desiredhostname e.g.
```ini
ExecStart = /usr/bin/docker run --name helloworld -e SERVICE_ID=helloworld -p 80:80 tutum/hello-world
```
4. Run sudo ./hosts_updater.py to get your /etc/hosts updated

5. check /etc/hosts. Visit <desiredhostname>.dimitris.io on your browser. e.g. helloworld.dimitris.io
