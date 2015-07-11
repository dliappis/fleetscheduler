# fleetscheduler
Scheduler and orchestrator for fleet

# Quick setup

## coreos

1. Clone coreos-vagrant

2. Get your etcd discovery token ` curl -i -L https://discovery.etcd.io/new`

3. Edit user.data, paste the token in the discovery: variable

4. Copy config.rb.sample to config.rb and edit num of instance to whatever you want e.g. 3

5. Start your coreos cluster `vagrant up`

6. Install fleetctl on your workstation.

7. Before all next steps ensure you have an env var pointing to a coreos working ssh endpoint:

```bash
ssh-agent bash
ssh-add ~/.vagrant.d/insecure_private_key
export FLEETCTL_TUNNEL=127.0.0.1:2222 # Use vagrant ssh-config to figure out the ip:port for any coreos vm
```

## skydns2

* On your workstation, compile + run skydns2:

```bash
go get github.com/skynetservices/skydns
cd <gosourcepath> skydns2
go build -v
export ETCD_MACHINES='http://172.17.8.102:4001' # use any coreos ip here
./skydns2
```

* On a coreos machine or using etcd http api calls create a skydns2 conf:

```
etcdctl set /skydns/config '{"dns_addr":"127.0.0.1:5354","ttl":3600, "domain":"dimitris.io","nameservers": ["8.8.8.8:53","8.8.4.4:53"]}'
```

This will force skydns to look for auto registered (gliderlabs/registrator) data under /skydns/local/io/dimitris

## start registrator

* Use the following fleet unit file to start gliderlabs/registrator, located in this repo as `registrator-skydns2.service`

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

## start fleet units
* Run `./fleetscheduler create test.yaml`

Note: test.yaml defines two services helloworld (to use domainname: mytestapp.dimitris.io) and redis

* Run `sudo ./hosts_updater.py #` to update your /etc/hosts

Note: (TODO) this will be converted to a daemon to get triggered when etcd skydns dir gets updated

* check /etc/hosts. Visit `<defineddomainname>.dimitris.io` on your browser. e.g. [mytestapp.dimitris.io](http://mytestapp.dimitris.io)

* Destroy services using `./fleetscheduler destroy test.yaml`

### Options for fleetscheduler

1. specify service group.

e.g. start containers associated with prod-webapp1 servicegroup only:

```bash
./fleetscheduler.py start test.yaml -s prod-webapp1
```
destroy containers in staging servicegroup:

```bash
./fleetscheduler.py destroy test.yaml -s staging-webapp1
```

2. if you don't specify -s (--servicegroup) all servicegroups will be affected

