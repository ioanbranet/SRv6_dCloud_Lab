## Contents
- [Contents](#contents)
- [xrd01](#xrd01)
- [xrd05](#xrd05)
- [xrd06](#xrd06)
- [xrd07](#xrd07)
- [Back to Lab 3 Guide](#back-to-lab-3-guide)

## xrd01
```
conf t

router bgp 65000
 address-family ipv4 unicast
  network 10.101.1.0/24
  network 10.101.2.0/24
  allocate-label all
 !
 neighbor-group xrd-ipv4-peer
  address-family ipv4 labeled-unicast
   next-hop-self
  !
 !
!
commit

```

## xrd05
```
conf t

router bgp 65000
 neighbor-group xrd-ipv4-peer
  address-family ipv4 labeled-unicast
   route-reflector-client
  !
 !
!
commit

```

## xrd06
```
conf t

router bgp 65000
 neighbor-group xrd-ipv4-peer
  address-family ipv4 labeled-unicast
   route-reflector-client
  !
 !
!
commit

```

## xrd07
```
conf t

router bgp 65000
 address-family ipv4 unicast
  network 20.0.0.0/24
  network 10.107.1.0/24
  allocate-label all
 !
 neighbor-group xrd-ipv4-peer
  address-family ipv4 labeled-unicast
   next-hop-self
  !
 !
!
commit

```

 ## Back to Lab 3 Guide
[Lab 3 Guide](https://github.com/jalapeno/SRv6_dCloud_Lab/tree/main/lab_3/lab_3-guide.md)