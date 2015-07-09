# fleetscheduler
Scheduler and orchestrator for fleet

# Quick setup

1. Clone coreos-vagrant

2. Get your etcd discovery token ` curl -i -L https://discovery.etcd.io/new`

3. Edit user.data, paste the token in the discovery: variable

4. Copy config.rb.sample to config.rb and edit num of instance to whatever you want e.g. 3

5. Start your coreos cluster `vagrant up`

6. On your workstation, compile + run skydns2:

```bash
go get github.com/skynetservices/skydns
cd <gosourcepath> skydns2
go build -v
export ETCD_MACHINES='http://172.17.8.102:4001' # use any coreos ip here
./skydns2
```

7. On a coreos machine or using etcd http api calls create a skydns2 conf:

```
etcdctl set /skydns/config '{"dns_addr":"127.0.0.1:5354","ttl":3600, "domain":"dimitris.io","nameservers": ["8.8.8.8:53","8.8.4.4:53"]}'
```

This will force skydns to look for auto registered (gliderlabs/registrator) data under /skydns/local/io/dimitris

8. Use the following fleet unit file to start gliderlabs/registrator, located in this repo as `registrator-skydns2.service`

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

9. Run `./fleetscheduler create test.yaml`

Note: test.yaml defines two services helloworld (to use domainname: mytestapp.dimitris.io) and redis

10. Run `sudo ./hosts_updater.py #` to update your /etc/hosts

Note: (TODO) this will be converted to a daemon to get triggered when etcd skydns dir gets updated

11. check /etc/hosts. Visit <defineddomainname>.dimitris.io on your browser. e.g. mytestapp.dimitris.io

12. Destroy services using `./fleetscheduler destroy test.yaml`
