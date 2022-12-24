## POC host-based SRv6 and SR-MPLS SDN 

Todo:
1. Build and test this lab
2. Writeup lab guide

### Login to the Amsterdam VM
```
ssh cisco@198.18.128.102
```
The Amsterdam VM has VPP pre-installed. VPP (also known as fd.io) is a very flexible and high performance open source software dataplane. In our lab the Amsterdam VM represents a content server whose application owners wish to provide optimal user experience, while balancing out the need for bulk content replication.  They've chose VPP as their host-based SR/SRv6 forwarding engine, and have subscribed to the network services made available by our Jalapeno system.

Like the Rom VM, Amsterdam has the same client script that will query Jalapeno for SR/SRv6 path data, and then program its local VPP dataplane with ip route with SR/SRv6 encapsulation

For more information on VPP/fd.io: https://fd.io/

1. On the Amsterdam VM cd into the lab_6 directory:
```
cd ~/SRv6_dCloud_Lab/lab_6
```
2. Everything is the same as on the Rome VM. Note the 
```
cat amsterdam.json
ls netservice
cat client.py

```
3. Amsterdam has a Linux veth pair connecting kernel forwarding to its onboard VPP instance. The VM has preconfigured ip routes (see /etc/netplan/00-installer-config.yaml) pointing to VPP via its "ams-out" interface:
```
cisco@amsterdam:~/SRv6_dCloud_Lab/lab_6$ ip link | grep ams-out
4: vpp-in@ams-out: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000
5: ams-out@vpp-in: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000

cisco@amsterdam:~/SRv6_dCloud_Lab/lab_6$ ip route
default via 198.18.128.1 dev ens160 proto static 
default via 198.18.128.1 dev ens160 proto static metric 100 
10.0.0.0/24 via 10.101.2.2 dev ams-out proto static 
10.101.2.0/24 dev ams-out proto kernel scope link src 10.101.2.1 
10.107.0.0/20 via 10.101.2.2 dev ams-out proto static 
198.18.128.0/18 dev ens160 proto kernel scope link src 198.18.128.102 
```
4. VPP has been given a startup config which establishes IP connectivity to the network as a whole on bootup.
```
cat /etc/vpp/startup.conf
```
 - Note the 'unix' and 'dpdk' sections of the config:
```
unix {
  nodaemon
  log /var/log/vpp/vpp.log
  full-coredump
  cli-listen /run/vpp/cli.sock
  gid vpp
  startup-config /home/cisco/SRv6_dCloud_Lab/lab_0/config/vpp.conf
}
dpdk {
  dev 0000:0b:00.0
}
```
 - VPP startup-config file: https://github.com/jalapeno/SRv6_dCloud_Lab/blob/main/lab_0/config/vpp.conf

5. VPP's CLI may be invoked directly:
```
cisco@amsterdam:~/SRv6_dCloud_Lab/lab_6$ sudo vppctl
    _______    _        _   _____  ___ 
 __/ __/ _ \  (_)__    | | / / _ \/ _ \
 _/ _// // / / / _ \   | |/ / ___/ ___/
 /_/ /____(_)_/\___/   |___/_/  /_/    

vpp# show interface address
GigabitEthernetb/0/0 (up):
  L3 10.101.1.1/24
  L3 fc00:0:101:1::1/64
host-vpp-in (up):
  L3 10.101.2.2/24
local0 (dn):
vpp# 
```
6. Or driven from the Linux command line:
```
cisco@amsterdam:~/SRv6_dCloud_Lab/lab_6$ sudo vppctl show interface address
GigabitEthernetb/0/0 (up):
  L3 10.101.1.1/24
  L3 fc00:0:101:1::1/64
host-vpp-in (up):
  L3 10.101.2.2/24
local0 (dn):
```
7. Other handy VPP commands:
```
quit                     # exit VPP CLI
show ip fib              # show VPP's forwarding table, which will include SR and SRv6 policy/encap info later
sudo vppctl show ip fib  # same command but executed from Linux
show interface           # interface status and stats
```

### Jalapeno SDN client:
The client operates on Amsterdam the same way it operates on the Rome VM. amsterdam.json specifies to the use of a VPP dataplane, therefore the client construct a VPP SR or SRv6 route/policy upon completing its path calculation.

Client help:
```
python3 client.py -h
```

## Network Services
### Get All Paths Service 

No need to specify encapsulation type:
``` 
python3 client.py -f amsterdam.json -s gp
```
 - log output will be appended to log/get_paths.json. SR/SRv6 label stacks and SIDs should be roughly the reverse of those generated by the Rome VM:
```
cat log/get_paths.json
```
### Data Sovereignty Service 
#### DS and Segment Routing
1. Run the client
``` 
python3 client.py -f rome.json -e sr -s ds
```
 - check log output:
 ```
cat log/data_sovereignty.json
```
2. Ping test 
 - Open up a second ssh session to Rome VM
 - Start tcpdump:
```
sudo tcpdump -ni ens192
```
 - Start ping on first Rome ssh session:
```
ping 10.0.0.1 -i .4
```
 - Validate traffic is encapsulated in the SR label stack. Expected output:
```
cisco@rome:~$ sudo tcpdump -ni ens192
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on ens192, link-type EN10MB (Ethernet), capture size 262144 bytes
23:30:45.565960 MPLS (label 100004, exp 0, ttl 64) (label 100005, exp 0, ttl 64) (label 100001, exp 0, [S], ttl 64) IP 10.107.1.1 > 10.0.0.1: ICMP echo request, id 3, seq 1, length 64
23:30:45.571246 IP 10.0.0.1 > 10.107.1.1: ICMP echo reply, id 3, seq 1, length 64
23:30:45.966843 MPLS (label 100004, exp 0, ttl 64) (label 100005, exp 0, ttl 64) (label 100001, exp 0, [S], ttl 64) IP 10.107.1.1 > 10.0.0.1: ICMP echo request, id 3, seq 2, length 64
23:30:45.971546 IP 10.0.0.1 > 10.107.1.1: ICMP echo reply, id 3, seq 2, length 64
23:30:46.368126 MPLS (label 100004, exp 0, ttl 64) (label 100005, exp 0, ttl 64) (label 100001, exp 0, [S], ttl 64) IP 10.107.1.1 > 10.0.0.1: ICMP echo request, id 3, seq 3, length 64
23:30:46.372139 IP 10.0.0.1 > 10.107.1.1: ICMP echo reply, id 3, seq 3, length 64
```
3. Use tcpdump on the xrd VM to trace labeled packets through the network
 - On the xrd VM cd into the lab_6 directory
 - run the dockernets.sh shell script, which will write the appropriate linux bridge names to a file
```
# ingress to xrd07
sudo tcpdump -ni ens192




#### DS and SRv6
1. cleanup any old routes:
```
./cleanup_rome_routes.sh
```
2. re-run the client with SRv6 encap:
```
python3 client.py -f rome.json -e srv6 -s ds
```
4. IPv6 ND may not have worked. Login to xrd07 and ping Rome vm
```
ping fc00:0:107:1::1
```
5. re-run the ping/tcpdump test. Expected output:
```
cisco@rome:~$ sudo tcpdump -ni ens192
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on ens192, link-type EN10MB (Ethernet), capture size 262144 bytes
23:40:41.614862 IP6 fe80::250:56ff:fe86:8789 > fc00:0:107:1::2: ICMP6, neighbor solicitation, who has fc00:0:107:1::2, length 32
23:40:41.615999 IP6 fc00:0:107:1::2 > fe80::250:56ff:fe86:8789: ICMP6, neighbor advertisement, tgt is fc00:0:107:1::2, length 32
23:40:42.665521 IP6 fc00:0:107:1::1 > fc00:0:4:5:1::: srcrt (len=2, type=4, segleft=0[|srcrt]
23:40:43.086871 IP6 fc00:0:107:1::1 > fc00:0:4:5:1::: srcrt (len=2, type=4, segleft=0[|srcrt]
23:40:43.502868 IP6 fc00:0:107:1::1 > fc00:0:4:5:1::: srcrt (len=2, type=4, segleft=0[|srcrt]
23:40:43.918911 IP6 fc00:0:107:1::1 > fc00:0:4:5:1::: srcrt (len=2, type=4, segleft=0[|srcrt]
```

### Low Latency Service
``` 
python3 client.py -f rome.json -e sr -s ll
```
```
python3 client.py -f rome.json -e srv6 -s ll
```
 - check log output:
 ```
cat log/low_latency.json
```

### Least Utilized service:
``` 
python3 client.py -f rome.json -e sr -s lu
```
```
python3 client.py -f rome.json -e srv6 -s lu
```
 - check log output:
 ```
cat log/least_utilized.json
```